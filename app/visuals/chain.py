"""Per-scene visual provider chain for the strong pipeline.

Each shot is classified from its script text as ``motion_graphic`` (numbers,
claims, lists) or ``broll`` (ambient visual) and gets a short English keyword.
Resolution order:

    motion_graphic -> local card (ffmpeg, no API)
    broll          -> Pixabay video -> Coverr video (if configured)
                      -> Wikimedia/Openverse still -> AI image (only when a
                      configured provider is available) -> gradient + caption

Stock b-roll scenes are capped below half of the video. Logs never include
credentials or request URLs.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from app.visuals.scene_component_adapter import render_scene_component

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "pixabay"
CACHE_TTL_SECONDS = 24 * 3600
STOCK_CLIP_SECONDS = 3.6
WIDTH, HEIGHT, FPS = 1080, 1920, 30
USER_AGENT = "NextdecodeShorts/1.0 (automated short-form video pipeline)"
FONT_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
ACCENT = "0x22d3ee"

STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "for", "with", "that", "this", "from",
    "into", "are", "was", "were", "has", "have", "had", "not", "but", "you",
    "your", "our", "their", "they", "its", "why", "how", "what", "when",
    "which", "who", "does", "did", "can", "will", "would", "should", "could",
    "about", "after", "before", "over", "under", "than", "then", "just",
    "very", "more", "most", "some", "show", "shows", "shot", "scene",
    "visual", "footage", "video", "stock", "illustrating", "point", "line",
    "alternate", "angle", "close", "wide", "detail", "dark", "moody",
    "corporate", "cinematic", "photorealistic", "resolution", "composition",
    "nature", "plants", "outdoors", "no",
})

VERB_PHRASE_STOPWORDS = frozenset({
    "being", "revised", "resulting", "splits", "splitting",
    "currently", "happening", "making", "taking", "using",
    "getting", "having", "becoming", "including", "following",
    "showing", "helping", "working", "looking", "moving",
    "implemented", "implementing",
    "framework", "document", "documents", "process", "processes",
    "approach", "method", "methods", "concept", "concepts",
    "thing", "things", "aspect", "aspects", "factor", "factors",
    "part", "parts", "item", "items", "area", "areas",
    "feature", "features", "case", "cases", "point", "points",
    "example", "examples", "fact", "facts", "reason", "reasons",
    "way", "ways", "type", "types", "kind", "kinds",
    "level", "levels", "amount", "amounts", "result", "results",
    "period", "situation", "manner", "number", "version", "full",
})

GRAPHIC_FALLBACK_CHAIN = ["local_card", "gradient_caption", "procedural"]
BROLL_FALLBACK_CHAIN = [
    "pixabay_video", "coverr_video", "wikimedia_still", "openverse_image",
    "ai_image", "gradient_caption", "procedural",
]
# Full-screen cards are easy to read but become monotonous: no more than half
# the shots, and never three numeric cards in a row.
MAX_CONSECUTIVE_GRAPHICS = 2
# A query may serve at most this many scenes before the planner rotates to a
# meaningfully different phrase.  Two lets a recurring subject stay coherent;
# more than that turns the video into the same shot with different footage.
MAX_QUERY_REUSE = 2

GRAPHIC_HINTS = (
    "percent", "million", "billion", "trillion", "study", "report",
    "survey", "according", "data shows", "analysis", "growth", "increase",
    "decrease", "first", "second", "third", "finally", "step 1", "step 2",
    "chart", "graph",
)

CHART_HINTS = (
    "chart", "graph", "data shows", "statistics", "percentage", "percent",
    "growth", "decline", "survey", "compared with", "versus",
)
UI_HINTS = (
    "interface", "dashboard", "screen", "software", "browser", "chatgpt",
    "chatbot", "prompt", "api", "code", "programming", "terminal", "app ",
)
DIAGRAM_HINTS = (
    "diagram", "architecture diagram", "architecture routes", "network diagram",
    "flowchart", "schematic", "routing diagram", "token routing diagram",
    "mixture of experts token routing diagram", "mixture of experts diagram",
    "router gating diagram", "expert network architecture diagram",
    "service layers", "sub-network diagram", "subnetwork diagram",
)

MAP_HINTS = (
    "map", "geography", "region", "country", "global",
    "worldwide", "grid map", "statewide", "nationwide",
)
PRODUCT_HINTS = (
    "chip", "gpu", "h100", "b200", "device", "hardware", "robot", "phone",
    "smartphone", "camera", "sensor", "server rack", "data center", "server",
)

# Small, deterministic synonym expansion for stock search.  These are subject
# phrases, not style words, so they remain useful when the script wording is
# abstract ("power" -> "power grid").
QUERY_SYNONYMS = {
    "server": ("server room", "data center"),
    "servers": ("server room", "data center"),
    "data": ("data center", "analytics"),
    "chip": ("semiconductor", "microchip"),
    "chips": ("semiconductor", "microchip"),
    "gpu": ("graphics card", "semiconductor"),
    "ai": ("artificial intelligence", "neural network"),
    "model": ("neural network", "machine learning"),
    "models": ("neural network", "machine learning"),
    "robot": ("robotics", "automation"),
    "power": ("power grid", "electricity"),
    "electricity": ("power grid", "energy"),
    "energy": ("power plant", "electricity"),
    "climate": ("environment", "atmosphere"),
    "car": ("vehicle", "automobile"),
    "phone": ("smartphone", "mobile device"),
    "developer": ("programmer", "coding"),
    "code": ("software", "programming"),
    "security": ("cybersecurity", "hacker"),
    "money": ("finance", "stock market"),
    "office": ("workplace", "corporate"),
    "factory": ("manufacturing", "industrial"),
    "network": ("internet", "connectivity"),
    "policy": ("government policy", "legislation document"),
    "regulation": ("government regulation", "compliance checklist"),
    "framework": ("software architecture", "legal framework"),
    "compliance": ("compliance audit", "business regulation"),
    "governance": ("corporate governance", "boardroom meeting"),
    "deployment": ("cloud deployment", "software release"),
    "revision": ("document editing", "software update"),
}


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)


_DIGIT_WORDS = "zero|one|two|three|four|five|six|seven|eight|nine"
_NUM_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}
_MAGNITUDES = {"hundred": 100, "thousand": 1_000, "million": 1_000_000,
               "billion": 1_000_000_000, "trillion": 1_000_000_000_000}
_UNIT_PATTERN = (
    r"percent|gigawatt[- ]hours?|megawatt[- ]hours?|terawatt[- ]hours?|"
    r"kilowatt[- ]hours?|watt[- ]hours?|gwh|mwh|twh|kwh|wh|gigawatts?|"
    r"megawatts?|terawatts?|kilowatts?|watts?|hours?|years?|times?|fold"
)
_PERCENT_QUANTITY = re.compile(r"(?<![\w.-])(\d+(?:[.,]\d+)?)\s*%", re.I)
_DIGIT_QUANTITY = re.compile(r"(?<![\w.-])(\d+(?:[.,]\d+)?)\s*(" + _UNIT_PATTERN + r")\b", re.I)
_SPELLED_WORD = (
    _DIGIT_WORDS + "|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
    "seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|"
    "eighty|ninety"
)
_SPELLED_QUANTITY = re.compile(
    r"\b((?:" + _SPELLED_WORD + r")"
    r"(?:[ -](?:" + _SPELLED_WORD + r"))?"
    r"(?:\s+point\s+(?:\d+|" + _DIGIT_WORDS + r"))?"
    r"(?:\s+(?:hundred|thousand|million|billion|trillion))?"
    r"(?:\s+(?:" + _SPELLED_WORD + r"))?)"
    r"\s+(" + _UNIT_PATTERN + r")\b",
    re.I,
)
_DIGIT_PLAIN = re.compile(r"(?<![\w.-])(\d+(?:[.,]\d+)?)(?![\w])")
_LEADING_POINT_PERCENT = re.compile(
    r"\bpoint\s+(" + _SPELLED_WORD + r"|\d+)\s+percent\b", re.I
)
_UNIT_LABELS = {
    "%": "%", "percent": "%",
    "gigawatthour": "GWh", "gigawatthours": "GWh", "gwh": "GWh",
    "megawatthour": "MWh", "megawatthours": "MWh", "mwh": "MWh",
    "terawatthour": "TWh", "terawatthours": "TWh", "twh": "TWh",
    "kilowatthour": "kWh", "kilowatthours": "kWh", "kwh": "kWh",
    "watthour": "Wh", "watthours": "Wh", "wh": "Wh",
    "gigawatt": "GW", "gigawatts": "GW", "megawatt": "MW", "megawatts": "MW",
    "terawatt": "TW", "terawatts": "TW", "kilowatt": "kW", "kilowatts": "kW",
    "watt": "W", "watts": "W", "hour": "h", "hours": "h",
    "year": "years", "years": "years", "time": "x", "times": "x", "fold": "x",
}


def _unit_label(unit: str) -> str:
    key = re.sub(r"[\s-]+", "", str(unit or "").lower())
    return _UNIT_LABELS.get(key) or _UNIT_LABELS.get(key.rstrip("s"), "")


def _words_to_number(phrase: str) -> str:
    phrase = re.sub(r"[\s-]+", " ", phrase.strip().lower())
    if " point " in f" {phrase} ":
        whole, _, fraction = phrase.partition(" point ")
        digits = "".join(str(_NUM_WORDS.get(w, w)) for w in fraction.split())
        return f"{_words_to_number(whole)}.{digits}"
    total = 0
    current = 0
    for word in phrase.split():
        if word in _MAGNITUDES:
            current = (current or 1) * _MAGNITUDES[word]
            total += current
            current = 0
        else:
            current += _NUM_WORDS.get(word, 0)
    return str(total + current)


def _format_quantity(value: str, label: str) -> str:
    if label == "%":
        return f"{value}%"
    if label == "x":
        return f"{value}×"
    return f"{value} {label}".strip()


def _first_number(text: str) -> str:
    text = str(text or "")
    match = _PERCENT_QUANTITY.search(text)
    if match:
        return _format_quantity(match.group(1), "%")
    match = _DIGIT_QUANTITY.search(text)
    if match:
        return _format_quantity(match.group(1), _unit_label(match.group(2)))
    match = _LEADING_POINT_PERCENT.search(text)
    if match:
        fraction = _words_to_number(match.group(1))
        return _format_quantity(f"0.{fraction}", "%")
    match = _SPELLED_QUANTITY.search(text)
    if match:
        return _format_quantity(_words_to_number(match.group(1)), _unit_label(match.group(2)))
    for match in _DIGIT_PLAIN.finditer(text):
        value = match.group(1)
        previous = text[match.start() - 1] if match.start() else ""
        prefix = text[max(0, match.start() - 9):match.start()].lower()
        # "N+1", "N plus 1", "#1" and model names are not statistics.
        if previous in "+#":
            continue
        if re.search(r"\b(?:plus|minus)\s*$", prefix):
            continue
        # A bare year is a date, not a numeric claim worth a full-screen card.
        if "." not in value and value.isdigit() and 1900 <= int(value) <= 2099:
            continue
        return value
    return ""


def _clean_card_text(text: str) -> str:
    text = re.sub(r"^\s*(hook|open|intro|payoff|close|outro|cta)\s*[:\-]\s*", "", str(text or ""), flags=re.I)
    text = re.sub(r"^\s*\d+[.)]\s*", "", text)
    return re.sub(r"\s+", " ", text).strip(" \"'")


def _wrap(text: str, width: int = 18, max_lines: int = 3) -> list[str]:
    words = str(text or "").split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if not lines:
        return []
    if len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
        lines[-1] = lines[-1][: max(1, width - 1)].rstrip() + "…"
    return lines


def extract_keyword(shot: dict) -> str:
    """Return a coherent subject phrase, never a fragment of narration.

    Structured beat fields take precedence over legacy asset_query values:
    a query must describe a visible subject/action, not arbitrary prose words.
    """
    structured = " ".join(str(shot.get(key) or "") for key in (
        "visual_subject", "beat_subject", "visual_action", "beat_action",
        "visual_context", "beat_context",
    )).strip()
    if structured and len(re.findall(r"[A-Za-z][A-Za-z0-9-]*", structured)) >= 2:
        return re.sub(r"\s+", " ", structured)[:100]
    raw = " ".join(str(shot.get(key) or "") for key in ("asset_query", "visual"))
    if not raw.strip():
        raw = str(shot.get("claim") or shot.get("caption") or "")
    raw = re.sub(r"illustrating the point of this line.*$", " ", raw, flags=re.I)
    raw = re.sub(
        r"\b(alternate angle|detail view|in context|close up|wide shot)\b",
        " ", raw, flags=re.I,
    )
    words = []
    for word in re.findall(r"[A-Za-z][A-Za-z0-9-]+", raw):
        low = word.lower()
        if (
            len(low) > 2
            and low not in STOPWORDS
            and low not in VERB_PHRASE_STOPWORDS
            and low not in words
        ):
            words.append(low)

    # If no concrete words found in query/visual/caption, fall back to shot topic
    if not words:
        topic = str(shot.get("topic") or "")
        words = [
            w.lower()
            for w in re.findall(r"[A-Za-z][A-Za-z0-9-]+", topic)
            if len(w) > 2
            and w.lower() not in STOPWORDS
            and w.lower() not in VERB_PHRASE_STOPWORDS
            and w.lower() not in words
        ]
        # Synonym expansion if topic keyword has direct entry in QUERY_SYNONYMS
        if words:
            for term in words:
                syns = QUERY_SYNONYMS.get(term, ())
                if syns:
                    return syns[0]

    # If topic was also empty or yielded no words, check raw narration or direct topic synonyms
    if not words:
        topic = str(shot.get("topic") or "").lower()
        for term in topic.split():
            syns = QUERY_SYNONYMS.get(term, ())
            if syns:
                return syns[0]

    return " ".join(words[:3]) or "technology"


def _query_candidates(shot: dict, keyword: str) -> list[str]:
    """Search phrases in priority order: variants, explicit query, synonyms."""
    candidates: list[str] = []

    def add(value: str) -> None:
        cleaned = re.sub(r"\s+", " ", str(value or "")).strip(" ,.;:-")
        cleaned = re.sub(r"illustrating the point of this line.*$", "", cleaned, flags=re.I)
        if len(cleaned) < 3:
            return
        # If the phrase consists entirely of stopwords/verb phrases, don't prioritize as a valid query candidate
        cleaned_words = [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9-]+", cleaned)]
        if cleaned_words and all(w in STOPWORDS or w in VERB_PHRASE_STOPWORDS for w in cleaned_words):
            return
        if cleaned.lower() not in {item.lower() for item in candidates}:
            candidates.append(cleaned)

    # Preserve the accepted visual-intent-first ordering from the prior asset
    # intelligence task, while dropping generic editorial-only wording.
    intent = str(shot.get("visual_intent") or "")
    if intent and not re.search(r"\b(ground the narration|support the narration|illustrate the point|hold a claim)\b", intent, re.I):
        add(intent)
    for variant in shot.get("asset_query_variants") or []:
        add(variant)
    add(str(shot.get("asset_query") or ""))
    add(keyword)
    for term in str(keyword or "").lower().split():
        for synonym in QUERY_SYNONYMS.get(term, ()):
            add(synonym)
    return candidates[:6] or [keyword] or ["technology"]


def _quantities(text: str) -> list[tuple[str, str]]:
    """All explicit quantities in a sentence, as (value, unit label) pairs."""
    text = str(text or "")
    found: list[tuple[str, str]] = []
    for match in _PERCENT_QUANTITY.finditer(text):
        found.append((match.group(1), "%"))
    for match in _DIGIT_QUANTITY.finditer(text):
        found.append((match.group(1), _unit_label(match.group(2)) or match.group(2)))
    for match in _SPELLED_QUANTITY.finditer(text):
        found.append((_words_to_number(match.group(1)), _unit_label(match.group(2)) or match.group(2)))
    return found


def _explicit_moe_diagram_query(shot: dict) -> bool:
    """Whether the planner explicitly requests an original MoE mechanism diagram."""
    query = str(shot.get("asset_query") or shot.get("search_query") or "").lower()
    narration = str(
        shot.get("narration") or shot.get("text") or shot.get("claim")
        or shot.get("caption") or shot.get("visual") or ""
    ).lower()
    # A generic MoE search phrase must not turn every beat into a diagram.
    # Require the narration itself to describe a routing/architecture mechanism.
    explicit_mechanism = any(
        term in narration
        for term in (
            "router", "routing", "gating", "flowchart", "architecture diagram",
            "specialist networks", "each token", "whole prompt", "token arrives",
        )
    )
    # Once the narration itself names a concrete routing/selection mechanism,
    # prefer an original explanatory graphic even if a search-query rewrite
    # accidentally points at generic hardware footage.
    return explicit_mechanism


def _scene_type(shot: dict, visual_type: str, low: str, quantities: list[tuple[str, str]]) -> str:
    """Map one beat to a concrete visual treatment."""
    if _explicit_moe_diagram_query(shot):
        return "diagram"
    if visual_type == "motion_graphic":
        units = [unit for _, unit in quantities if unit]
        repeated_unit = any(units.count(unit) >= 2 for unit in set(units))
        if repeated_unit or any(hint in low for hint in CHART_HINTS):
            return "chart"
        if any(hint in low for hint in DIAGRAM_HINTS):
            return "diagram"
        return "typography"
    if any(hint in low for hint in UI_HINTS):
        return "ui_demo"
    if any(hint in low for hint in DIAGRAM_HINTS):
        return "diagram"
    if any(hint in low for hint in MAP_HINTS):
        return "map"
    if any(hint in low for hint in PRODUCT_HINTS):
        return "product"
    return "footage"


def classify_scene(shot: dict) -> dict:
    """Decide how one narration beat should be visualized."""
    text = str(
        shot.get("narration") or shot.get("text") or shot.get("claim")
        or shot.get("caption") or shot.get("visual") or ""
    )
    low = text.lower()
    quantities = _quantities(text)
    has_number = bool(_first_number(text))
    has_claim = any(hint in low for hint in GRAPHIC_HINTS)
    is_list = bool(re.search(r"(^|\s)(1[.)]|2[.)]|3[.)]|first|second|third)(\s|$)", low))
    has_architecture = any(hint in low for hint in DIAGRAM_HINTS)
    # Topic identity must not dictate visual treatment. Classify from the
    # actual narration beat and its explicit asset query so a technical MoE
    # explainer can alternate between footage, diagrams and typography.
    visual_type = "motion_graphic" if (
        has_number or has_claim or is_list or has_architecture
        or _explicit_moe_diagram_query(shot)
    ) else "broll"
    scene_type = _scene_type(shot, visual_type, low, quantities)
    explicit_family = str(shot.get("visual_family") or "").strip().lower()
    family_scene = {
        "diagram": "diagram", "chart": "chart", "typography": "typography",
        "ui_demo": "ui_demo", "map": "map", "product": "product",
        "real_footage": "footage", "footage": "footage",
    }.get(explicit_family)
    if family_scene:
        scene_type = family_scene
        visual_type = "motion_graphic" if family_scene in {"diagram", "chart", "typography"} else "broll"
    return {
        "visual_type": visual_type,
        "scene_type": scene_type,
        "keyword": extract_keyword(shot),
        "has_number": has_number,
    }


def _infer_intent(shot: dict, index: int) -> str:
    label = str(shot.get("beat_label") or shot.get("label") or "").strip().lower()
    if label in {"hook", "context", "mechanism", "evidence", "implication", "payoff"}:
        return label
    text = str(shot.get("claim") or shot.get("caption") or shot.get("visual") or "")
    if index == 0 or "?" in text:
        return "hook"
    if _first_number(text):
        return "evidence"
    return "context"


def _visual_purpose(scene_type: str) -> str:
    return {
        "chart": "make a numeric comparison legible",
        "typography": "hold a claim or figure long enough to read",
        "ui_demo": "show the software or interface being discussed",
        "diagram": "explain a process, architecture, or relationship",
        "map": "locate the story geographically",
        "product": "show the hardware or object at the centre of the story",
        "footage": "ground the narration in real-world imagery",
    }.get(scene_type, "support the narration")


def build_scene_brief(shot: dict, *, index: int | None = None) -> dict:
    """Structured contract between a script beat and visual resolution.

    Deterministic and offline: no claim about asset relevance is made here, only
    what the beat asks for and which fallbacks are available.
    """
    idx = int(shot.get("index", index if index is not None else 0) or 0)
    text = str(
        shot.get("narration") or shot.get("text") or shot.get("claim")
        or shot.get("caption") or shot.get("visual") or ""
    )
    caption = _clean_card_text(shot.get("caption") or shot.get("claim") or text)
    number = _first_number(text) or _first_number(caption)
    keyword = extract_keyword(shot)
    queries = _query_candidates(shot, keyword)
    scene = classify_scene(shot)
    explicit_family = str(shot.get("visual_family") or "").strip().lower()
    if scene["visual_type"] == "motion_graphic":
        fallback_chain = list(GRAPHIC_FALLBACK_CHAIN)
    else:
        fallback_chain = list(BROLL_FALLBACK_CHAIN)
        if _is_moe_query(keyword, text):
            # For technical MoE context, a title-matched Commons still is more
            # reliable than generic stock-video search results. Keep video
            # providers as fallbacks, but try the verifiable still first.
            fallback_chain = ["wikimedia", "pixabay", "coverr", "gradient"]
    try:
        duration = max(0.0, float(shot.get("duration") or 0.0))
    except (TypeError, ValueError):
        duration = 0.0
    visual_purpose = _visual_purpose(scene["scene_type"])
    if scene["scene_type"] == "footage" and _is_moe_query(keyword, text):
        if "token arrives" in text.lower():
            visual_purpose = "Show the transformer architecture that processes incoming tokens."
        else:
            visual_purpose = "Show GPU server hardware used to run large language models such as Mixtral."
    return {
        "index": idx,
        "beat_id": shot.get("beat_id") or f"scene-{idx:02d}",
        "intent": _infer_intent(shot, idx),
        "narration": text,
        "visual_subject": str(shot.get("visual_subject") or shot.get("beat_subject") or ""),
        "visual_action": str(shot.get("visual_action") or shot.get("beat_action") or ""),
        "visual_context": str(shot.get("visual_context") or shot.get("beat_context") or ""),
        "visual_family": explicit_family,
        "shot_size": str(shot.get("shot_size") or "medium"),
        "camera_angle": str(shot.get("camera_angle") or "eye_level"),
        "camera_movement": str(shot.get("camera_movement") or "slow_push_in"),
        "camera_instruction": str(shot.get("camera_instruction") or ""),
        "lighting_direction": str(shot.get("lighting_direction") or ""),
        "composition_direction": str(shot.get("composition_direction") or ""),
        "editing_rhythm": str(shot.get("editing_rhythm") or ""),
        "transition_intent": str(shot.get("transition_intent") or "cut"),
        "continuity_group": str(shot.get("continuity_group") or ""),
        "editorial_reason": str(shot.get("editorial_reason") or ""),
        "visual_purpose": visual_purpose,
        "visual_intent": str(shot.get("visual_intent") or visual_purpose),
        "scene_type": scene["scene_type"],
        "visual_type": scene["visual_type"],
        "asset_query": str(shot.get("asset_query") or keyword),
        "search_query": queries[0],
        "queries": queries,
        "expected_duration": round(duration, 3),
        "aspect": "9:16",
        "on_screen_text": number or caption[:80],
        "motion": {
            "zoom_from": float(shot.get("zoom_from", 1.0) or 1.0),
            "zoom_to": float(shot.get("zoom_to", 1.14) or 1.14),
            "pan": dict(shot.get("pan") or {}),
            "transition": str(shot.get("transition") or "cut"),
        },
        "fallback_chain": fallback_chain,
        "validation": {
            "query_ok": bool(keyword),
            "query_count": len(queries),
            "has_number": bool(number),
            "has_variants": len(queries) > 1,
        },
    }


def _graphic_signature(brief: dict) -> str:
    """Stable key for the text shown on a card, used to stop duplicate cards."""
    text = str(brief.get("on_screen_text") or brief.get("narration") or "")
    return re.sub(r"[^a-z0-9%]+", " ", text.lower()).strip()


def _query_key(value: str) -> str:
    """Normalised identity of a search phrase for reuse counting."""
    return " ".join(re.findall(r"[a-z0-9]+", str(value or "").lower()))


def _dedupe_query(brief: dict, query_use: dict[str, int],
                  query_context: dict[str, list[str]],
                  previous_query: str) -> tuple[str, dict]:
    """Pick a query that has not served more than ``MAX_QUERY_REUSE`` scenes.

    Meaningfully different phrases are preferred in their original order; a
    phrase reused by a different visual intent is allowed when no alternative
    exists, and the reason is recorded on the scene.
    """
    original = str(brief.get("search_query") or "")
    key = _query_key(original)
    if not key or query_use.get(key, 0) < MAX_QUERY_REUSE:
        return original, {}
    options = [query for query in brief.get("queries") or [] if _query_key(query)]
    ordered = sorted(options, key=lambda query: (query_use.get(_query_key(query), 0),
                                                 options.index(query)))
    for candidate in ordered:
        candidate_key = _query_key(candidate)
        if candidate_key == key or candidate_key == _query_key(previous_query):
            continue
        if query_use.get(candidate_key, 0) < MAX_QUERY_REUSE:
            return candidate, {
                "original": original,
                "switched_to": candidate,
                "prior_uses": query_use.get(key, 0),
                "reason": f"'{original}' already served {query_use.get(key, 0)} scene(s)",
            }
    prior_types = set(query_context.get(key) or [])
    different_intent = bool(prior_types) and brief.get("scene_type") not in prior_types
    return original, {
        "original": original,
        "switched_to": "",
        "prior_uses": query_use.get(key, 0),
        "reason": "no distinct query available" + (
            "; different visual intent" if different_intent
            else "; same visual intent"
        ),
        "different_intent": different_intent,
    }


def plan_scenes(shots: list[dict]) -> dict:
    """Classify every scene and reserve a stock budget below half the video."""
    total = len(shots)
    is_moe_plan = any(
        _is_moe_query(
            shot.get("narration") or shot.get("text") or shot.get("claim") or "",
            shot.get("asset_query") or shot.get("search_query") or "",
        )
        for shot in shots
    )
    stock_cap = max(0, (total - 1) // 2)
    # Technical topics still need editorial variety: diagrams explain the
    # mechanism, but they must not dominate the entire short. Keep graphics at
    # or below half the shots and never allow more than two consecutive cards.
    graphic_budget = max(1, total // 2) if total else 0
    max_graphic_run = MAX_CONSECUTIVE_GRAPHICS
    graphic_count = 0
    graphic_run = 0
    previous_was_recap = False
    seen_graphic_texts: set[str] = set()
    card_figures: list[dict] = []
    scenes: dict[int, dict] = {}
    scene_types: dict[str, int] = {}
    previous_query = ""
    query_use: dict[str, int] = {}
    query_context: dict[str, list[str]] = {}
    query_switches: list[dict] = []
    for position, shot in enumerate(shots):
        index = int(shot.get("index", position) or 0)
        brief = build_scene_brief(shot, index=index)
        # Do not ask the provider for the same phrase in consecutive scenes.
        if brief["search_query"].lower() == previous_query.lower():
            alternative = next(
                (query for query in brief["queries"][1:] if query.lower() != previous_query.lower()),
                "",
            )
            if alternative:
                brief["search_query"] = alternative
                brief["queries"] = [alternative] + [q for q in brief["queries"] if q != alternative]
        if brief["visual_type"] == "motion_graphic":
            signature = _graphic_signature(brief)
            duplicate = bool(signature and signature in seen_graphic_texts)
            if (
                duplicate
                and card_figures
                and not previous_was_recap
                and graphic_count < graphic_budget
                and graphic_run < max_graphic_run
            ):
                # Prefer a narration-derived recap over unrelated b-roll.  The
                # recap shows the real figures already used by earlier beats.
                # The normal graphic budget and consecutive-card limit still
                # apply, so recaps cannot turn the video into a wall of cards.
                brief["card_variant"] = "recap"
                brief["recap_figures"] = [dict(item) for item in card_figures[:4]]
                brief["scene_type"] = "chart" if len(card_figures) >= 2 else "typography"
                brief["visual_purpose"] = _visual_purpose(brief["scene_type"])
                brief["fallback_chain"] = list(GRAPHIC_FALLBACK_CHAIN)
                brief["variety_note"] = (
                    "duplicate figure kept as a narration-derived recap card"
                )
                graphic_count += 1
                graphic_run += 1
                previous_was_recap = True
            elif duplicate and brief["scene_type"] == "diagram" and _explicit_moe_diagram_query(shot):
                # A second shot of the same mechanism beat should not trigger a
                # weak stock search. Use a concise typography interstitial to
                # break up the diagram while staying grounded in the narration.
                narration = str(brief.get("narration") or "").lower()
                if "sparse" in narration or "selected subset" in narration:
                    title = "ONLY SELECTED EXPERTS"
                elif "router" in narration or "routing" in narration:
                    title = "THE ROUTER CHOOSES"
                elif "token" in narration:
                    title = "ONE TOKEN AT A TIME"
                else:
                    title = "SPECIALIST NETWORKS"
                brief["visual_type"] = "motion_graphic"
                brief["scene_type"] = "typography"
                brief["card_variant"] = "typography"
                brief["typography_title"] = title
                brief["visual_purpose"] = _visual_purpose("typography")
                brief["fallback_chain"] = list(GRAPHIC_FALLBACK_CHAIN)
                brief["variety_note"] = "typography interstitial breaks up a repeated mechanism diagram"
                graphic_run = 0
                previous_was_recap = False
            elif (
                is_moe_plan
                and brief["scene_type"] == "diagram"
                and _explicit_moe_diagram_query(shot)
                and graphic_run >= max_graphic_run
            ):
                narration = str(brief.get("narration") or "").lower()
                title = (
                    "ONLY SELECTED EXPERTS" if "sparse" in narration or "selected subset" in narration
                    else "THE ROUTER CHOOSES" if "router" in narration or "routing" in narration
                    else "ONE TOKEN AT A TIME" if "token" in narration
                    else "SPECIALIST NETWORKS"
                )
                brief["scene_type"] = "typography"
                brief["visual_type"] = "motion_graphic"
                brief["card_variant"] = "typography"
                brief["typography_title"] = title
                brief["visual_purpose"] = _visual_purpose("typography")
                brief["fallback_chain"] = list(GRAPHIC_FALLBACK_CHAIN)
                brief["variety_note"] = "mechanism interstitial keeps an explicit MoE beat visual"
                graphic_count += 1
                graphic_run = 1
                previous_was_recap = False
            elif (
                duplicate
                or graphic_count >= graphic_budget
                or graphic_run >= max_graphic_run
            ):
                # Keep the beat, but let real footage carry it instead of another
                # near-identical card. Captions still show the exact figure.
                brief["visual_type"] = "broll"
                brief["scene_type"] = "footage"
                brief["visual_purpose"] = _visual_purpose("footage")
                brief["fallback_chain"] = list(BROLL_FALLBACK_CHAIN)
                if is_moe_plan:
                    brief["fallback_chain"] = ["wikimedia", "pixabay", "coverr", "gradient"]
                    narration = str(brief.get("narration") or "").lower()
                    if "token arrives" in narration:
                        brief["visual_purpose"] = "Show the transformer architecture that processes incoming tokens."
                    else:
                        brief["visual_purpose"] = "Show GPU server hardware used to run large language models such as Mixtral."
                    contextual = _moe_context_still_queries(brief, brief.get("search_query") or "")
                    brief["queries"] = contextual + [q for q in brief.get("queries", []) if q not in contextual]
                    if contextual:
                        brief["search_query"] = contextual[0]
                brief["variety_note"] = (
                    "duplicate card text replaced with b-roll"
                    if duplicate
                    else "b-roll breaks up repeated full-screen cards"
                )
                graphic_run = 0
                previous_was_recap = False
            else:
                seen_graphic_texts.add(signature)
                graphic_count += 1
                graphic_run += 1
                previous_was_recap = False
                if brief.get("validation", {}).get("has_number"):
                    number = str(brief.get("on_screen_text") or "").strip()
                    if number and not any(item["number"] == number for item in card_figures):
                        card_figures.append({
                            "number": number,
                            "label": _recap_label(brief.get("narration") or ""),
                        })
        else:
            graphic_run = 0
            previous_was_recap = False
        brief["allow_stock"] = brief["visual_type"] == "broll"
        if brief["visual_type"] == "broll":
            # Global, not just consecutive: a phrase may not become the whole
            # video's subject, and an identical fetch must not repeat.
            chosen, reuse = _dedupe_query(brief, query_use, query_context, previous_query)
            if chosen != brief["search_query"]:
                brief["search_query"] = chosen
                brief["queries"] = [chosen] + [q for q in brief["queries"] if q != chosen]
            if reuse:
                brief["query_reuse"] = reuse
                if reuse.get("switched_to"):
                    query_switches.append({"index": index, **reuse})
            chosen_key = _query_key(chosen)
            query_use[chosen_key] = query_use.get(chosen_key, 0) + 1
            query_context.setdefault(chosen_key, []).append(brief.get("scene_type") or "")
        scenes[index] = brief
        scene_types[brief["scene_type"]] = scene_types.get(brief["scene_type"], 0) + 1
        previous_query = brief["search_query"]
    return {
        "scenes": scenes,
        "stock_cap": stock_cap,
        "stock_used": 0,
        "total": total,
        "scene_types": scene_types,
        "used_asset_ids": set(),
        "resolved": [],
        "query_use": dict(query_use),
        "query_switches": query_switches,
    }


def stock_summary(planner: dict) -> str:
    types = ", ".join(
        f"{name}:{count}" for name, count in sorted((planner.get("scene_types") or {}).items())
    ) or "none"
    fallbacks = sum(1 for item in planner.get("resolved", []) if item.get("fallback_reason"))
    return (
        f"stock b-roll scenes: {planner.get('stock_used', 0)}/{planner.get('total', 0)} "
        f"(cap {planner.get('stock_cap', 0)}); types={types}; fallbacks={fallbacks}"
    )


def _log_scene(index: int, visual_type: str, provider: str, keyword: str) -> None:
    print(f"[visual] scene {index:02d} {visual_type} -> {provider} ({keyword})")


# ---------------------------------------------------------------------------
# Provider: local motion graphic card (no API)
# ---------------------------------------------------------------------------
def _escape_text(value: str) -> str:
    return (
        str(value)
        .replace("\\", r"\\")
        .replace(":", r"\:")
        .replace(",", r"\,")
        .replace("'", r"\'")
        .replace("\n", " ")
    )


CARD_PALETTES = (
    ("0x08101f", "0x163a5f", "0x0f766e"),
    ("0x120b1f", "0x3b1d5f", "0x0e7490"),
    ("0x1c0b14", "0x4c1d3f", "0x115e59"),
)


def _gradient_input(variant: int = 0) -> str:
    c0, c1, c2 = CARD_PALETTES[int(variant) % len(CARD_PALETTES)]
    return (
        f"gradients=s={WIDTH}x{HEIGHT}:c0={c0}:c1={c1}:c2={c2}:"
        f"nb_colors=3:x0=0:y0=0:x1={WIDTH}:y1={HEIGHT}"
    )


def _text_filter(text: str, *, size: int, y: int, color: str = "white") -> str:
    return (
        f"drawtext=fontfile={FONT_PATH}:text='{_escape_text(text)}':expansion=none:"
        f"fontcolor={color}:fontsize={size}:x=(w-text_w)/2:y={y}:"
        f"shadowcolor=black@0.5:shadowx=4:shadowy=4"
    )


def _left_text_filter(text: str, *, size: int, x: int, y: int,
                      color: str = "white") -> str:
    return (
        f"drawtext=fontfile={FONT_PATH}:text='{_escape_text(text)}':expansion=none:"
        f"fontcolor={color}:fontsize={size}:x={x}:y={y}:"
        f"shadowcolor=black@0.5:shadowx=3:shadowy=3"
    )


def _recap_label(text: str, limit: int = 34) -> str:
    """Short, truthful label for a figure, taken from its narration beat."""
    cleaned = _clean_card_text(text)
    cleaned = re.sub(r"\b\d+(?:[.,]\d+)?\s*%?", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,:;-")
    if len(cleaned) > limit:
        cleaned = cleaned[:limit].rsplit(" ", 1)[0].rstrip(" .,:;-")
    words = cleaned.split()
    trailing = {"in", "by", "of", "at", "for", "to", "with", "from", "and",
                "the", "a", "an", "that", "this", "their", "its"}
    while words and words[-1].lower() in trailing:
        words.pop()
    return " ".join(words) or "narration figure"


def _recap_graphic(shot: dict, work_dir: Path, index: int,
                   figures: list[dict]) -> Path | None:
    """Narration-derived recap card for a repeated figure.

    The duplicate guard must not send a repeated number to unrelated b-roll.
    This card lists the real figures already used by earlier beats, so the new
    scene adds context without inventing data or repeating the exact layout.
    """
    figures = [item for item in figures if isinstance(item, dict) and item.get("number")]
    if not figures:
        return None
    shown = figures[:4]
    out = work_dir / f"recap_{index:03d}.png"
    filters = [
        "drawbox=x=90:y=360:w=260:h=8:color=%s@0.9:t=fill" % ACCENT,
        _left_text_filter("RECAP", size=46, x=90, y=270, color="white@0.75"),
    ]
    # Centre small recaps instead of leaving the lower two-thirds empty.
    top = {1: 760, 2: 650, 3: 520, 4: 430}[len(shown)]
    step = {1: 0, 2: 380, 3: 340, 4: 285}[len(shown)]
    for position, figure in enumerate(shown):
        y = top + position * step
        filters.append(_left_text_filter(str(figure["number"]), size=104, x=96, y=y))
        filters.append(
            _left_text_filter(str(figure.get("label") or "narration figure"),
                              size=36, x=100, y=y + 120, color="white@0.85")
        )
    filters.extend([
        "drawbox=x=64:y=64:w=132:h=8:color=white@0.30:t=fill",
        "drawbox=x=64:y=64:w=8:h=132:color=white@0.30:t=fill",
        f"drawbox=x={WIDTH - 196}:y={HEIGHT - 72}:w=132:h=8:color=white@0.30:t=fill",
        f"drawbox=x={WIDTH - 72}:y={HEIGHT - 196}:w=8:h=132:color=white@0.30:t=fill",
    ])
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", _gradient_input(index + 2),
        "-vf", ",".join(filters), "-frames:v", "1", str(out),
    ]
    try:
        _run(cmd)
    except Exception:
        return None
    return out if out.is_file() and out.stat().st_size > 5000 else None


def _motion_graphic(shot: dict, work_dir: Path, index: int) -> Path | None:
    out = work_dir / f"graphic_{index:03d}.png"
    source = str(shot.get("claim") or shot.get("visual") or shot.get("caption") or "")
    caption = _clean_card_text(shot.get("claim") or shot.get("caption") or source)
    number = _first_number(source) or _first_number(caption)
    lines = _wrap(caption, 22, 5)

    filters = [f"drawbox=x=90:y={470 if number else 420}:w={WIDTH - 180}:h=8:color={ACCENT}@0.9:t=fill"]
    if FONT_PATH.exists() and caption:
        if number:
            size = 200 if len(number) <= 3 else 150 if len(number) <= 5 else 118
            filters.append(_text_filter(number, size=size, y=250))
        y = 560 if number else 500
        for line in lines:
            filters.append(_text_filter(line, size=70, y=y))
            y += 90
        # Decorative framing only.  No bar chart is drawn unless the numbers
        # come from real data, so the card cannot imply invented statistics.
        filters.extend([
            "drawbox=x=64:y=64:w=132:h=8:color=white@0.30:t=fill",
            "drawbox=x=64:y=64:w=8:h=132:color=white@0.30:t=fill",
            f"drawbox=x={WIDTH - 196}:y={HEIGHT - 72}:w=132:h=8:color=white@0.30:t=fill",
            f"drawbox=x={WIDTH - 72}:y={HEIGHT - 196}:w=8:h=132:color=white@0.30:t=fill",
        ])
        for square in range(3):
            filters.append(
                f"drawbox=x={430 + square * 88}:y=1660:w=22:h=22:"
                f"color={ACCENT}@{0.40 + 0.18 * square}:t=fill"
            )

    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", _gradient_input(index),
        "-vf", ",".join(filters), "-frames:v", "1", str(out),
    ]
    try:
        _run(cmd)
    except Exception:
        return None
    return out if out.is_file() and out.stat().st_size > 5000 else None


def _moe_diagram_graphic(shot: dict, work_dir: Path, index: int) -> Path | None:
    """Render an original, narration-safe MoE routing diagram without stock imagery."""
    if not FONT_PATH.exists():
        return None
    text = " ".join(str(shot.get(key) or "") for key in ("topic", "claim", "caption", "visual")).lower()
    if not any(term in text for term in ("mixture of experts", "expert", "router", "gating", "deepseek", "sub-network", "subnetwork")):
        return None

    if any(term in text for term in ("limitation", "difficult", "load balance", "load-balancing")):
        title, subtitle = "MEMORY FOOTPRINT", "SPARSE COMPUTE STILL STORES THE FULL MODEL"
        footer = "ACTIVE PARAMETERS AND STORED PARAMETERS ARE DIFFERENT"
    elif "deepseek" in text:
        title, subtitle = "DEEPSEEK V3", "671B TOTAL  /  37B ACTIVE PARAMETERS"
        footer = "ILLUSTRATIVE MoE ROUTING FLOW"
    elif "mixtral" in text:
        title, subtitle = "MIXTRAL 8x7B", "A SPARSE MIXTURE-OF-EXPERTS MODEL"
        footer = "CHECK THE MODEL CARD FOR EXACT CONFIGURATION"
    elif any(term in text for term in ("employee", "company", "email")):
        title, subtitle = "ONE ROUTER, MANY SPECIALISTS", "NOT EVERY EXPERT ANSWERS EVERY REQUEST"
        footer = "ROUTING AVOIDS ACTIVATING THE WHOLE MODEL"
    elif any(term in text for term in ("256 billion", "671 billion", "total parameters", "37 billion", "8 billion")):
        title, subtitle = "PARAMETER SCALE", "TOTAL CAPACITY IS NOT THE SAME AS ACTIVE COMPUTE"
        footer = "A SMALLER SUBSET CAN RUN FOR EACH TOKEN"
    elif any(term in text for term in ("sub-network", "subnetwork", "specialist", "giant")):
        title, subtitle = "SPECIALIST EXPERTS", "ONE MODEL CAN CONTAIN MANY EXPERT BLOCKS"
        footer = "ONLY THE SELECTED EXPERTS DO THE WORK"
    elif any(term in text for term in ("gating", "router")):
        title, subtitle = "ROUTER / GATING", "SELECTING EXPERTS FOR EACH TOKEN"
        footer = "ONLY THE SELECTED EXPERTS DO THE WORK"
    elif any(term in text for term in ("memory", "compute", "research")):
        title, subtitle = "MODEL SYSTEMS", "SPECIALIZED COMPUTE THROUGH ROUTED EXPERTS"
        footer = "CONCEPTUAL VIEW OF A SPARSE MODEL"
    else:
        title, subtitle = "TOKEN ROUTING", "A ROUTER SELECTS WHICH EXPERTS ACTIVATE"
        footer = "ONLY THE SELECTED EXPERTS DO THE WORK"

    out = work_dir / f"moe_diagram_{index:03d}.png"
    filters = [
        "drawbox=x=72:y=72:w=936:h=1776:color=0x0A1726@0.96:t=fill",
        "drawbox=x=96:y=96:w=120:h=7:color=0x45D6C5@0.95:t=fill",
        _left_text_filter("NEXTDECODE  /  AI SYSTEMS", size=28, x=96, y=145, color="white@0.55"),
        _left_text_filter(title, size=66, x=96, y=250),
        _left_text_filter(subtitle, size=30, x=100, y=345, color="0x9CB7CC"),
        "drawbox=x=100:y=430:w=880:h=190:color=0x12283D@0.98:t=fill",
        "drawbox=x=100:y=430:w=880:h=4:color=0x3B6077@0.9:t=fill",
        _left_text_filter("INPUT TOKENS", size=28, x=135, y=468, color="0x9CB7CC"),
        _left_text_filter("TOKEN 01      TOKEN 02      TOKEN 03", size=34, x=135, y=525),
        "drawbox=x=280:y=730:w=520:h=205:color=0x123C48@0.98:t=fill",
        "drawbox=x=280:y=730:w=520:h=5:color=0x45D6C5@0.95:t=fill",
        _left_text_filter("ROUTER / GATING", size=38, x=330, y=790),
        _left_text_filter("selects a small set of experts", size=28, x=330, y=865, color="0xB5D4D7"),
        "drawbox=x=536:y=935:w=8:h=115:color=0x45D6C5@0.85:t=fill",
        "drawbox=x=290:y=1045:w=500:h=7:color=0x45D6C5@0.85:t=fill",
        "drawbox=x=290:y=1045:w=7:h=70:color=0x45D6C5@0.85:t=fill",
        "drawbox=x=783:y=1045:w=7:h=70:color=0x45D6C5@0.85:t=fill",
        "drawbox=x=100:y=1130:w=420:h=220:color=0x104A4B@0.98:t=fill",
        "drawbox=x=100:y=1130:w=420:h=5:color=0x45D6C5@0.95:t=fill",
        "drawbox=x=560:y=1130:w=420:h=220:color=0x17283A@0.98:t=fill",
        "drawbox=x=100:y=1410:w=420:h=220:color=0x17283A@0.98:t=fill",
        "drawbox=x=560:y=1410:w=420:h=220:color=0x104A4B@0.98:t=fill",
        "drawbox=x=560:y=1410:w=420:h=5:color=0x45D6C5@0.95:t=fill",
        _left_text_filter("EXPERT 01", size=42, x=140, y=1180),
        _left_text_filter("SELECTED", size=27, x=140, y=1260, color="0x45D6C5"),
        _left_text_filter("EXPERT 02", size=42, x=600, y=1180),
        _left_text_filter("STANDBY", size=27, x=600, y=1260, color="0x8FA5B8"),
        _left_text_filter("EXPERT 03", size=42, x=140, y=1460),
        _left_text_filter("STANDBY", size=27, x=140, y=1540, color="0x8FA5B8"),
        _left_text_filter("EXPERT 04", size=42, x=600, y=1460),
        _left_text_filter("SELECTED", size=27, x=600, y=1540, color="0x45D6C5"),
        # Reserve the lower caption band for kinetic subtitles.  Do not put
        # essential labels or footers underneath the subtitle layer.
    ]
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", _gradient_input(index + 5),
        "-vf", ",".join(filters), "-frames:v", "1", str(out),
    ]
    try:
        _run(cmd)
    except Exception:
        return None
    return out if out.is_file() and out.stat().st_size > 5000 else None


def _moe_context_graphic(shot: dict, work_dir: Path, index: int) -> Path | None:
    """Draw an original hardware/network illustration for MoE context beats."""
    if not FONT_PATH.exists():
        return None
    beat = str(shot.get("claim") or shot.get("caption") or shot.get("visual") or "").lower()
    if not any(term in beat for term in (
        "mixture of experts", "expert", "specialist", "router", "mixtral",
        "token", "processor", "gpu", "server",
    )):
        return None

    if "arrives" in beat or "input" in beat:
        title, subtitle = "TOKEN ARRIVES", "A NEW INPUT ENTERS THE MODEL"
        modules = ("TOKEN INPUT", "ROUTER", "EXPERT POOL", "OUTPUT")
        core = "MODEL CORE"
    elif "mixtral" in beat or "open weights" in beat:
        title, subtitle = "MIXTRAL 8x7B", "A SPARSE MIXTURE-OF-EXPERTS MODEL"
        modules = ("OPEN WEIGHTS", "MODEL LAYERS", "EXPERT POOL", "ROUTER")
        core = "MODEL CORE"
    elif "specialist" in beat or "networks" in beat:
        title, subtitle = "SPECIALIST NETWORKS", "ONE MODEL / MANY SPECIALIST BLOCKS"
        modules = ("EXPERT 01", "EXPERT 02", "EXPERT 03", "EXPERT 04")
        core = "SHARED MODEL"
    else:
        title, subtitle = "COMPUTE PATH", "FOLLOW THE TOKEN THROUGH THE MODEL"
        modules = ("TOKEN", "ROUTER", "SELECTED EXPERTS", "OUTPUT")
        core = "MODEL CORE"

    out = work_dir / f"moe_context_{index:03d}.png"
    filters = [
        "drawbox=x=48:y=48:w=984:h=1824:color=0x081522@0.99:t=fill",
        "drawbox=x=88:y=105:w=130:h=7:color=0x45D6C5@0.98:t=fill",
        _left_text_filter("NEXTDECODE  /  AI SYSTEMS", size=27, x=88, y=160, color="white@0.58"),
        _left_text_filter(title, size=62, x=88, y=290),
        _left_text_filter(subtitle, size=27, x=92, y=370, color="0xA9C2D4"),
        "drawbox=x=300:y=720:w=480:h=350:color=0x102B3D@0.99:t=fill",
        "drawbox=x=300:y=720:w=480:h=7:color=0x45D6C5@0.98:t=fill",
        "drawbox=x=350:y=790:w=380:h=205:color=0x0A1C2A@0.99:t=fill",
        "drawbox=x=350:y=790:w=380:h=4:color=0x34566D@0.95:t=fill",
        _left_text_filter(core, size=42, x=385, y=865),
        _left_text_filter("SPARSE COMPUTE", size=25, x=385, y=935, color="0x45D6C5"),
        "drawbox=x=535:y=1070:w=10:h=95:color=0x45D6C5@0.95:t=fill",
        "drawbox=x=220:y=1165:w=640:h=7:color=0x45D6C5@0.95:t=fill",
        "drawbox=x=220:y=1165:w=7:h=75:color=0x45D6C5@0.95:t=fill",
        "drawbox=x=853:y=1165:w=7:h=75:color=0x45D6C5@0.95:t=fill",
    ]
    positions = ((90, 570), (800, 570), (90, 1270), (800, 1270))
    for label, (x, y) in zip(modules, positions):
        filters.extend([
            f"drawbox=x={x}:y={y}:w=190:h=155:color=0x142A3D@0.99:t=fill",
            f"drawbox=x={x}:y={y}:w=190:h=5:color=0x45D6C5@0.95:t=fill",
            _left_text_filter(label, size=25, x=x+18, y=y+67),
            _left_text_filter("CONNECTED", size=18, x=x+18, y=y+112, color="0x8FA5B8"),
        ])
    filters.extend([
        "drawbox=x=88:y=1575:w=904:h=3:color=0x34566D@0.8:t=fill",
        _left_text_filter("ILLUSTRATIVE SYSTEM VIEW  /  NOT A BENCHMARK", size=20, x=90, y=1640, color="0x8FA5B8"),
    ])
    try:
        _run(["ffmpeg", "-y", "-f", "lavfi", "-i", _gradient_input(index),
              "-vf", ",".join(filters), "-frames:v", "1", str(out)])
    except Exception:
        return None
    return out if out.is_file() and out.stat().st_size > 5000 else None


def _moe_scene_graphic(shot: dict, work_dir: Path, index: int) -> Path | None:
    """Create a distinct, evidence-led MoE scene without external image services."""
    if not FONT_PATH.exists():
        return None
    beat = str(shot.get("claim") or shot.get("caption") or shot.get("visual") or "")
    context = str(shot.get("topic") or "")
    text = f"{beat} {context}".lower()
    if not any(term in text for term in ("expert", "router", "mixture of experts", "mixtral", "token routing")):
        return None

    variant = index % 4
    if "sparse" in beat.lower():
        title, subtitle = "SPARSE ROUTING", "ONLY THE SELECTED EXPERTS PROCESS THIS TOKEN"
        center_label = "ACTIVE EXPERTS"
    elif "token" in beat.lower():
        title, subtitle = "TOKEN-BY-TOKEN ROUTING", "THE ROUTER MAKES A CHOICE AT EACH LAYER"
        center_label = "ROUTER / GATING"
    elif "mixture" in beat.lower() or "pool" in beat.lower():
        title, subtitle = "MIXTURE OF EXPERTS", "ONE MODEL / A POOL OF SPECIALIST NETWORKS"
        center_label = "EXPERT POOL"
    elif "router" in beat.lower():
        title, subtitle = "THE ROUTER DECIDES", "TWO EXPERTS ARE SELECTED FOR EACH TOKEN"
        center_label = "ROUTER / GATING"
    else:
        title, subtitle = "EXPERT ROUTING", "A SMALL SUBSET HANDLES THE TOKEN"
        center_label = "SELECTED PATH"

    # Rotate the highlighted pair so adjacent scenes show different routing paths.
    selected = {index % 8, (index + 3) % 8}
    filters = [
        "drawbox=x=48:y=48:w=984:h=1824:color=0x081522@0.98:t=fill",
        "drawbox=x=88:y=100:w=120:h=7:color=0x45D6C5@0.98:t=fill",
        _left_text_filter("NEXTDECODE  /  AI SYSTEMS", size=27, x=88, y=155, color="white@0.55"),
        _left_text_filter(title, size=58, x=88, y=265),
        _left_text_filter(subtitle, size=27, x=92, y=345, color="0xA9C2D4"),
        "drawbox=x=110:y=440:w=860:h=150:color=0x12283D@0.98:t=fill",
        "drawbox=x=110:y=440:w=860:h=4:color=0x34566D@0.9:t=fill",
        _left_text_filter("INPUT", size=24, x=145, y=475, color="0x8EA8BC"),
        _left_text_filter("TOKEN 01       TOKEN 02       TOKEN 03", size=34, x=145, y=530),
        "drawbox=x=300:y=665:w=480:h=150:color=0x123C48@0.98:t=fill",
        "drawbox=x=300:y=665:w=480:h=5:color=0x45D6C5@0.98:t=fill",
        _left_text_filter(center_label, size=38, x=345, y=710),
        _left_text_filter("selects a small expert subset", size=24, x=345, y=770, color="0xB5D4D7"),
        "drawbox=x=536:y=815:w=8:h=65:color=0x45D6C5@0.95:t=fill",
        "drawbox=x=300:y=880:w=480:h=7:color=0x45D6C5@0.95:t=fill",
    ]
    # Eight distinct expert nodes; two active nodes change between scenes.
    for expert in range(8):
        col = expert % 2
        row = expert // 2
        x = 110 + col * 460
        y = 930 + row * 132
        active = expert in selected
        fill = "0x104A4B@0.99" if active else "0x142638@0.99"
        accent = "0x45D6C5@0.98" if active else "0x334A60@0.9"
        state = "SELECTED" if active else "AVAILABLE"
        state_color = "0x45D6C5" if active else "0x8FA5B8"
        filters.extend([
            f"drawbox=x={x}:y={y}:w=410:h=108:color={fill}:t=fill",
            f"drawbox=x={x}:y={y}:w=410:h=4:color={accent}:t=fill",
            _left_text_filter(f"EXPERT {expert + 1:02d}", size=31, x=x+24, y=y+28),
            _left_text_filter(state, size=21, x=x+24, y=y+72, color=state_color),
        ])
    filters.extend([
        "drawbox=x=110:y=1510:w=860:h=130:color=0x12283D@0.98:t=fill",
        "drawbox=x=110:y=1510:w=860:h=4:color=0x45D6C5@0.95:t=fill",
        _left_text_filter("COMBINED OUTPUT", size=34, x=145, y=1545),
        _left_text_filter("Selected expert outputs return to the model", size=23, x=145, y=1600, color="0xA9C2D4"),
        _left_text_filter("ILLUSTRATIVE ROUTING VIEW  /  NOT A BENCHMARK CHART", size=19, x=112, y=1690, color="white@0.42"),
    ])
    out = Path(work_dir) / f"moe_scene_{index:03d}.png"
    command = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", _gradient_input(index + 17),
        "-vf", ",".join(filters), "-frames:v", "1", str(out),
    ]
    try:
        _run(command)
    except Exception:
        return None
    return out if out.is_file() and out.stat().st_size > 5000 else None


# ---------------------------------------------------------------------------
# Provider: gradient + caption fallback (no API, no prompt text)
# ---------------------------------------------------------------------------
def _gradient_caption(shot: dict, work_dir: Path, index: int) -> Path | None:
    duration = max(1.3, float(shot.get("duration") or 3.0))
    out = work_dir / f"gradient_{index:03d}.mp4"
    caption = _clean_card_text(shot.get("claim") or shot.get("caption") or shot.get("visual") or "")
    lines = _wrap(caption, 24, 2)
    filters = []
    if FONT_PATH.exists() and lines:
        # Kept in the upper third so burned-in captions can occupy the bottom.
        y = 380
        for line in lines:
            filters.append(_text_filter(line, size=64, y=y))
            y += 84

    base = ["ffmpeg", "-y", "-f", "lavfi", "-i", _gradient_input(index)]
    tail = [
        "-t", str(duration), "-r", str(FPS),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-an", str(out),
    ]
    try:
        _run(base + (["-vf", ",".join(filters)] if filters else []) + tail)
    except Exception:
        try:
            _run(base + tail)
        except Exception:
            return None
    return out if out.is_file() and out.stat().st_size > 5000 else None


# ---------------------------------------------------------------------------
# Provider: Pixabay videos (24h keyword cache)
# ---------------------------------------------------------------------------
def _cache_path(keyword: str) -> Path:
    normalized = " ".join(str(keyword or "").lower().split())
    digest = hashlib.sha256(f"pixabay-video-v2:{normalized}".encode("utf-8")).hexdigest()[:20]
    return CACHE_DIR / f"{digest}.json"


def _cached_hits(keyword: str) -> list[dict] | None:
    path = _cache_path(keyword)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - float(payload.get("fetched_at", 0)) < CACHE_TTL_SECONDS:
            return list(payload.get("hits") or [])
    except (OSError, ValueError, TypeError):
        return None
    return None


def _pixabay_hits(keyword: str) -> list[dict]:
    cached = _cached_hits(keyword)
    if cached is not None:
        return cached
    key = _env("PIXABAY_API_KEY")
    if not key:
        return []
    url = "https://pixabay.com/api/videos/?" + urllib.parse.urlencode({
        "key": key, "q": keyword[:100], "per_page": "20",
        "safesearch": "true", "video_type": "film",
    })
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"[visual] pixabay search unavailable (HTTP {exc.code})")
        return []
    except Exception as exc:
        print(f"[visual] pixabay search unavailable ({type(exc).__name__})")
        return []

    hits = []
    for hit in payload.get("hits") or []:
        videos = hit.get("videos") or {}
        chosen = videos.get("large") or videos.get("medium") or videos.get("small") or {}
        if not chosen.get("url"):
            continue
        hits.append({
            "id": hit.get("id"),
            "title": str(hit.get("title") or "")[:180],
            "description": str(hit.get("description") or "")[:500],
            "tags": str(hit.get("tags") or "")[:500],
            "page_url": str(hit.get("pageURL") or ""),
            "author": str(hit.get("user") or "")[:120],
            "duration": float(hit.get("duration") or 0),
            "width": int(chosen.get("width") or 0),
            "height": int(chosen.get("height") or 0),
            "url": str(chosen.get("url")),
        })
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cache_path(keyword).write_text(
            json.dumps({"fetched_at": time.time(), "keyword": keyword, "hits": hits}, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass
    return hits


MIN_TAG_OVERLAP = 0.5

# Style/medium words that stock providers often attach to unrelated clips.
# They should not by themselves make a clip look relevant to a narration beat.
GENERIC_STYLE_TERMS = frozenset({
    "technology", "tech", "digital", "computer", "modern", "future", "abstract",
    "light", "lights", "background", "video", "footage", "animation", "graphic",
    "graphics", "motion", "concept", "business", "corporate", "people", "person",
})

# Words that are too broad to prove that a still shows the requested subject.
# Wikimedia titles such as "Performance Measurement - Grassroots Development"
# can share two of these while showing something unrelated.
GENERIC_SUBJECT_TERMS = frozenset({
    "software", "development", "performance", "programming",
    "system", "systems", "project", "team", "teams", "work", "worker",
    "office", "measurement", "process", "management", "technology", "computer",
    "one", "two", "three", "these", "giant", "lightweight", "machine", "learning",
    "laboratory", "architecture", "diagram", "network", "building", "city", "modern",
    "company", "manager",
})


def _content_terms(*texts: object) -> set[str]:
    """Lower-cased content words from narration/query/title/tag text.

    Adds a simple singular/plural variant so ``servers`` and ``server`` match
    without a full stemmer.
    """
    terms: set[str] = set()
    for text in texts:
        for word in re.findall(r"[a-z0-9]+", str(text or "").lower()):
            if len(word) <= 2 or word in STOPWORDS or word in GENERIC_STYLE_TERMS:
                continue
            terms.add(word)
            if word.endswith("s") and len(word) > 3:
                terms.add(word[:-1])
            else:
                terms.add(word + "s")
    return terms


def _is_moe_query(*texts: object) -> bool:
    joined = " ".join(str(text or "").lower() for text in texts)
    return any(term in joined for term in ("mixture of experts", "expert routing", "expert", "router", "gating", "token routing", "deepseek", "sub-network", "subnetwork"))


def _moe_context_still_queries(scene: dict, keyword: str) -> list[str]:
    """Use precise, Commons-searchable context queries when stock APIs are absent."""
    narration = " ".join(str(scene.get(key) or "") for key in (
        "narration", "claim", "caption", "visual", "beat_label"
    )).lower()
    if not _is_moe_query(keyword, narration):
        return []
    if any(term in narration for term in ("specialist", "network")):
        return ["neural network", "artificial neural network"]
    if any(term in narration for term in ("token", "router", "routing", "layer")):
        return ["transformer architecture", "neural network"]
    return ["GPU server", "data center"]


def _specific_terms(*texts: object) -> set[str]:
    """Return distinct, non-generic subject terms for strict asset matching."""
    terms: set[str] = set()
    excluded = STOPWORDS | GENERIC_SUBJECT_TERMS
    for text in texts:
        for word in re.findall(r"[a-z0-9]+", str(text or "").lower()):
            word = word[:-1] if word.endswith("s") and len(word) > 3 else word
            if len(word) <= 2 or word in excluded:
                continue
            terms.add(word)
    return terms


def _term_overlap(terms: set[str], other: set[str]) -> float:
    if not terms:
        return 0.0
    return len(terms & other) / len(terms)


LOW_LIGHT_YAVG = 28.0
LOW_CONTRAST_SPAN = 12.0
LOW_LIGHT_YMAX = 150.0


def _is_low_light(stats: dict | None) -> bool:
    """True for footage that is very dark or flat enough to be hard to read."""
    if not stats:
        return False
    avg = float(stats.get("yavg") or 0.0)
    low = float(stats.get("ylow") or 0.0)
    high = float(stats.get("yhigh") or 0.0)
    peak = float(stats.get("ymax") or 0.0)
    if avg and avg < LOW_LIGHT_YAVG:
        return True
    return (high - low) < LOW_CONTRAST_SPAN and peak < LOW_LIGHT_YMAX


def validate_asset_relevance(scene: dict, asset: dict) -> dict:
    """Score a resolved asset against its narration beat and scene purpose.

    This is deliberately lexical/provenance-based.  It never claims semantic
    understanding of the visual content; stock and still matches remain
    ``semantic_review=True`` unless the asset is generated directly from the
    narration text.
    """
    provider = str(asset.get("provider") or "")
    visual_type = str(asset.get("visual_type") or scene.get("visual_type") or "broll")
    fallback_reason = str(asset.get("fallback_reason") or "")
    narration = str(scene.get("narration") or "")
    visual_intent = str(
        scene.get("visual_intent") or scene.get("visual_purpose")
        or scene.get("intent") or ""
    )
    query = str(asset.get("query") or scene.get("search_query") or scene.get("keyword") or "")
    title = str(asset.get("title") or "")
    description = str(asset.get("description") or "")
    tags = str(asset.get("tags") or "")
    metadata_text = " ".join(
        str(asset.get(key) or "")
        for key in ("author", "username", "category", "alt", "source_title", "source_url")
    )

    narration_terms = _content_terms(narration)
    intent_terms = _content_terms(visual_intent)
    # Compare against the query that actually produced this asset, not every
    # alternate query in the scene. Include the explicit visual intent so a
    # broad topic query cannot outweigh what this exact beat asks the viewer to see.
    query_terms = _content_terms(query, scene.get("keyword"))
    asset_terms = _content_terms(title, description, tags, metadata_text)
    matched_query = sorted(query_terms & asset_terms)
    matched_narration = sorted(narration_terms & asset_terms)
    query_overlap = _term_overlap(query_terms, asset_terms)
    narration_overlap = _term_overlap(narration_terms, asset_terms)
    specific_query_terms = _specific_terms(query, scene.get("keyword"))
    semantic_title = "" if title.lower().startswith("pixabay clip ") else title
    specific_asset_terms = _specific_terms(semantic_title, description, tags, asset.get("source_url"))
    matched_specific = sorted(specific_query_terms & specific_asset_terms)
    specific_overlap = _term_overlap(specific_query_terms, specific_asset_terms)
    intent_overlap = _term_overlap(intent_terms, asset_terms)
    relevance_score = round(
        min(1.0, query_overlap * 0.35 + intent_overlap * 0.40 + narration_overlap * 0.25),
        3,
    )

    if provider == "motion_graphic":
        return {
            "relevance_confidence": "high",
            "semantic_review": False,
            "relevance_reason": "on-screen text generated from the narration beat",
            "matched_terms": sorted(set(matched_query) | set(matched_narration)),
            "review_reason": "",
        }

    if asset.get("visual_quality") == "low_light":
        reason = "clip is too dark or flat to read clearly on a phone"
        return {
            "relevance_confidence": "low",
            "semantic_review": True,
            "relevance_reason": reason,
            "matched_terms": sorted(set(matched_query) | set(matched_narration)),
            "review_reason": reason,
        }

    if provider in {"gradient", "procedural"}:
        confidence = "none" if fallback_reason else "low"
        reason = fallback_reason or "procedural placeholder carries no subject imagery"
        return {
            "relevance_confidence": confidence,
            "semantic_review": True,
            "relevance_reason": reason,
            "matched_terms": [],
            "review_reason": reason,
        }

    if provider == "pixabay":
        if _is_moe_query(query, scene.get("keyword")):
            confidence = "medium" if len(matched_specific) >= 2 and specific_overlap >= MIN_TAG_OVERLAP else "low"
            reason = "two topic-specific terms match (lexical only); semantic review still required" if confidence == "medium" else "MoE asset lacks two topic-specific tag matches"
        elif not asset_terms:
            confidence, reason = "medium", "provider returned a result but tag/title metadata is unavailable; human review required"
        elif not specific_query_terms:
            confidence, reason = "low", "query contains only generic terms and cannot establish subject relevance"
        elif len(specific_query_terms) <= 2 and len(matched_specific) >= 1 and specific_overlap >= MIN_TAG_OVERLAP:
            confidence, reason = "medium", "concrete subject terms match metadata (lexical only)"
        elif len(matched_specific) >= 2 and specific_overlap >= MIN_TAG_OVERLAP:
            confidence, reason = "medium", "multiple beat-specific subject terms match metadata (lexical only)"
        else:
            confidence, reason = "low", "tags do not clearly match the narration/query terms"
        return {
            "relevance_confidence": confidence,
            "semantic_review": True,
            "relevance_reason": reason,
            "matched_terms": sorted(set(matched_query) | set(matched_narration) | set(matched_specific)),
            "relevance_score": relevance_score,
            "intent_overlap": round(intent_overlap, 3),
            "review_reason": "stock metadata overlap is lexical and needs visual review",
        }

    if provider == "coverr":
        if _is_moe_query(query, scene.get("keyword")):
            confidence = "medium" if len(matched_specific) >= 2 else "low"
            reason = "title shares two MoE-specific terms; semantic review still required" if confidence == "medium" else "Coverr title lacks two MoE-specific terms"
        elif not asset_terms:
            confidence, reason = "low", f"{provider} returned no subject metadata to verify the query"
        elif len(specific_query_terms) <= 2 and len(matched_specific) >= 1 and specific_overlap >= MIN_TAG_OVERLAP:
            confidence, reason = "medium", "concrete subject terms match metadata (lexical only)"
        elif len(matched_specific) >= 2 and specific_overlap >= MIN_TAG_OVERLAP:
            confidence, reason = "medium", "multiple beat-specific subject terms match metadata (lexical only)"
        else:
            confidence, reason = "low", f"{provider} metadata does not support this narration beat or visual intent"
        return {
            "relevance_confidence": confidence,
            "semantic_review": True,
            "relevance_reason": reason,
            "matched_terms": sorted(set(matched_query) | set(matched_narration) | set(matched_specific)),
            "relevance_score": relevance_score,
            "intent_overlap": round(intent_overlap, 3),
            "review_reason": "stock metadata match needs visual review",
        }

    if provider in {"wikimedia", "openverse"}:
        if _is_moe_query(query, scene.get("keyword")):
            confidence = "medium" if len(matched_specific) >= 2 and specific_overlap >= MIN_TAG_OVERLAP else "low"
            reason = "title/query shares two MoE-specific terms; image content not verified" if confidence == "medium" else "MoE title match lacks two topic-specific terms"
        elif not asset_terms:
            confidence, reason = "medium", f"{provider} still metadata unavailable; human review required"
        elif not specific_query_terms:
            confidence, reason = "low", "query contains only generic terms and cannot establish subject relevance"
        elif len(specific_query_terms) <= 2 and len(matched_specific) >= 1 and specific_overlap >= MIN_TAG_OVERLAP:
            confidence, reason = "medium", f"{provider} title/description matches concrete subject terms (lexical only)"
        elif len(matched_specific) >= 2 and specific_overlap >= MIN_TAG_OVERLAP:
            confidence, reason = "medium", f"{provider} title/description matches multiple beat-specific terms (lexical only)"
        else:
            confidence, reason = "low", f"{provider} title/query match is weak or ambiguous"
        return {
            "relevance_confidence": confidence,
            "semantic_review": True,
            "relevance_reason": reason,
            "matched_terms": sorted(set(matched_query) | set(matched_narration) | set(matched_specific)),
            "relevance_score": relevance_score,
            "intent_overlap": round(intent_overlap, 3),
            "review_reason": f"{provider} still requires visual and licence review",
        }

    if provider in {"ai_image", "gemini", "fal", "replicate", "openai", "pollinations", "cloudflare"}:
        return {
            "relevance_confidence": "medium",
            "semantic_review": True,
            "relevance_reason": "generated from the query prompt; output not verified",
            "matched_terms": sorted(set(matched_query) | set(matched_narration)),
            "review_reason": "generated image needs visual review",
        }

    return {
        "relevance_confidence": "unknown",
        "semantic_review": bool(fallback_reason),
        "relevance_reason": fallback_reason or "unknown provider",
        "matched_terms": sorted(set(matched_query) | set(matched_narration)),
        "review_reason": fallback_reason,
    }


def _pick_hit(hits: list[dict], keyword: str, *, used_ids: set[str] | None = None, scene: dict | None = None) -> dict | None:
    """Rank stock clips by tag overlap, vertical crop safety and quality.

    Assets already used by another scene are skipped so adjacent shots do not
    repeat the same clip.  A clip must share at least half of the query terms
    with its tags; otherwise a vertical, unrelated clip would win on geometry.
    """
    strict_topic_query = _is_moe_query(keyword)
    terms = _specific_terms(keyword) if strict_topic_query else set(re.findall(r"[a-z0-9]+", keyword.lower()))
    if not terms:
        return None
    used = {str(item) for item in (used_ids or set())}
    best, best_score = None, -1.0
    for hit in hits:
        asset_id = f"pixabay:{hit.get('id')}"
        if asset_id in used:
            continue
        duration = float(hit.get("duration") or 0)
        width = int(hit.get("width") or 0)
        height = int(hit.get("height") or 0)
        if duration < STOCK_CLIP_SECONDS or width <= 0 or height <= 0:
            continue
        metadata = " ".join(str(hit.get(key) or "") for key in ("title", "description", "tags", "category"))
        tags = _specific_terms(metadata) if strict_topic_query else set(re.findall(r"[a-z0-9]+", metadata.lower()))
        matched = terms & tags
        overlap = (len(matched) / len(terms)) if terms else 0.0
        intent_text = " ".join(str((scene or {}).get(key) or "") for key in ("visual_intent", "visual_purpose"))
        narration_text = str((scene or {}).get("narration") or "")
        intent_terms = _specific_terms(intent_text)
        narration_terms = _specific_terms(narration_text)
        intent_match = _term_overlap(intent_terms, tags)
        narration_match = _term_overlap(narration_terms, tags)
        if (len(matched) < 2 if strict_topic_query else overlap < MIN_TAG_OVERLAP):
            continue
        ratio = width / height
        target = 9 / 16
        ratio_fit = max(0.0, 1.0 - abs(ratio - target) / target)
        vertical = 1.0 if ratio < 1 else 0.0
        resolution = min(width, 1920) / 1920
        duration_fit = min(duration, 12.0) / 12.0
        score = (
            overlap * 3.0 + intent_match * 1.5 + narration_match * 0.75
            + ratio_fit * 2.0 + vertical * 1.0
            + resolution * 0.5 + duration_fit * 0.5
        )
        if score > best_score:
            best, best_score = hit, score
    if best is not None:
        best = dict(best)
        best["_rank_score"] = round(best_score, 3)
    return best


def _download_file(url: str, out: Path) -> bool:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=90) as response, open(out, "wb") as handle:
            while True:
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
    except Exception:
        out.unlink(missing_ok=True)
        return False
    return out.is_file() and out.stat().st_size > 100_000


def _clip_start_offset(source: Path) -> float:
    """Skip a fade-in from black so a stock clip does not start invisible.

    A single black intro frame freezes the whole Ken Burns shot, so always trim
    a short lead-in even when blackdetect cannot see a full interval.
    """
    offset = 0.15
    try:
        from app.render.ffmpeg_tools import _black_intervals
        for start, end in _black_intervals(source, min_duration=0.2, pix_th=0.10):
            if start <= 0.2 and end >= 0.2:
                offset = max(offset, end + 0.05)
    except Exception:
        pass
    return offset


def _prepare_clip(source: Path, out: Path) -> Path | None:
    vf = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},setsar=1,fps={FPS}"
    )
    start = _clip_start_offset(source)
    try:
        _run([
            "ffmpeg", "-y", "-ss", str(start), "-i", str(source), "-t", str(STOCK_CLIP_SECONDS),
            "-vf", vf, "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p", str(out),
        ])
    except Exception:
        return None
    if not out.is_file() or out.stat().st_size <= 50_000:
        return None
    # If the clip is black for most of its usable duration, ask for another.
    try:
        from app.render.ffmpeg_tools import _black_intervals
        if _black_intervals(out, min_duration=STOCK_CLIP_SECONDS * 0.6, pix_th=0.10):
            print("[visual] rejected a stock clip that is mostly black")
            out.unlink(missing_ok=True)
            return None
    except Exception:
        pass
    return out


def _visual_quality(path: Path) -> tuple[str, dict]:
    """Return (quality_label, luma_stats) for a prepared clip or still."""
    try:
        from app.render.ffmpeg_tools import video_luma_stats
        stats = video_luma_stats(Path(path))
    except Exception:
        stats = {}
    if _is_low_light(stats):
        print("[visual] flagged low-light/flat asset")
        return "low_light", stats
    return "ok", stats


def _pixabay_asset(keyword: str, work_dir: Path, index: int, *,
                   used_ids: set[str] | None = None, scene: dict | None = None) -> dict | None:
    hit = _pick_hit(_pixabay_hits(keyword), keyword, used_ids=used_ids, scene=scene)
    if not hit:
        return None
    raw = work_dir / f"pixabay_src_{index:03d}.mp4"
    if not _download_file(hit["url"], raw):
        return None
    out = _prepare_clip(raw, work_dir / f"stock_pixabay_{index:03d}.mp4")
    if not out:
        return None
    quality, luma = _visual_quality(out)
    return {
        "path": str(out),
        "provider": "pixabay",
        "title": str(hit.get("title") or f"Pixabay clip {hit.get('id')}"),
        "description": str(hit.get("description") or ""),
        "author": str(hit.get("author") or ""),
        "source_url": str(hit.get("page_url") or ""),
        "license": "Pixabay Content License",
        "query": keyword,
        "duration": STOCK_CLIP_SECONDS,
        "asset_id": f"pixabay:{hit.get('id')}",
        "relevance": "tag_overlap",
        "tags": str(hit.get("tags") or ""),
        "rank_score": hit.get("_rank_score", 0.0),
        "visual_quality": quality,
        "luma": luma,
    }


# ---------------------------------------------------------------------------
# Provider slot: Coverr videos (configured key; bounded free/demo quota)
# ---------------------------------------------------------------------------
def _coverr_asset(keyword: str, work_dir: Path, index: int, *,
                  used_ids: set[str] | None = None, scene: dict | None = None) -> dict | None:
    if not _env("COVERR_API_KEY"):
        return None
    try:
        from app.providers.media_sources import search_coverr_videos
        hits = search_coverr_videos(keyword, limit=8, orientation="vertical")
    except Exception as exc:
        print(f"[visual] coverr search unavailable ({type(exc).__name__})")
        return None
    used = {str(item) for item in (used_ids or set())}
    intent_terms = _specific_terms(
        str((scene or {}).get("visual_intent") or (scene or {}).get("visual_purpose") or "")
    )
    narration_terms = _specific_terms(str((scene or {}).get("narration") or ""))
    ranked = []
    for hit in hits:
        asset_id = f"coverr:{hit.get('id')}"
        if not hit.get("id") or asset_id in used or not hit.get("download_url"):
            continue
        metadata = " ".join([
            str(hit.get("title") or ""), str(hit.get("description") or ""),
            " ".join(str(tag) for tag in hit.get("tags") or []),
        ])
        terms = _specific_terms(metadata)
        score = _term_overlap(intent_terms, terms) * 1.5 + _term_overlap(narration_terms, terms) * 0.75
        ranked.append((score, hit))
    if not ranked:
        return None
    score, hit = max(ranked, key=lambda item: (item[0], str(item[1].get("id"))))
    source = str(hit.get("download_url") or "")
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme != "https" or not parsed.netloc:
        return None
    raw = work_dir / f"coverr_src_{index:03d}.mp4"
    if not _download_file(source, raw):
        return None
    out = _prepare_clip(raw, work_dir / f"stock_coverr_{index:03d}.mp4")
    if not out:
        return None
    quality, luma = _visual_quality(out)
    tags = hit.get("tags") or []
    return {
        "path": str(out), "provider": "coverr",
        "title": str(hit.get("title") or f"Coverr clip {hit.get('id')}"),
        "description": str(hit.get("description") or ""),
        "author": str(hit.get("creator") or hit.get("author") or ""),
        "source_url": str(hit.get("source_url") or ""),
        "license": str(hit.get("license") or "Coverr API terms; verify item terms"),
        "attribution_required": bool(hit.get("attribution_required", True)),
        "query": keyword, "tags": " ".join(str(tag) for tag in tags),
        "duration": STOCK_CLIP_SECONDS, "asset_id": f"coverr:{hit.get('id')}",
        "relevance": "coverr_metadata_match", "rank_score": score,
        "visual_quality": quality, "luma": luma,
    }


# ---------------------------------------------------------------------------
# Provider: Wikimedia stills
# ---------------------------------------------------------------------------
def _wikimedia_asset(shot: dict, keyword: str, work_dir: Path, index: int,
                     used_titles: set[str] | None,
                     extra_queries: list[str] | None = None) -> dict | None:
    queries = [str(item) for item in (extra_queries or [])]
    if not queries:
        queries = [str(item) for item in (shot.get("asset_query_variants") or [])]
    try:
        from app.visuals import stock_fetcher
        asset = stock_fetcher.fetch_shot_image(
            keyword, work_dir, index=index, used_titles=used_titles,
            extra_queries=queries,
        )
    except Exception:
        asset = None
    if not asset or not asset.get("path"):
        return None
    asset = dict(asset)
    asset.setdefault("provider", "wikimedia")
    asset["query"] = asset.get("query") or keyword
    title = " ".join(str(asset.get(key) or "") for key in ("title", "object_name", "description", "page_url", "source_url")).strip() or str(index)
    # Reject broad word overlap that does not identify the subject.  Example:
    # query "software development performance" matched a still titled
    # "Performance Measurement - Grassroots Development Programme".
    if _is_moe_query(asset["query"], keyword):
        query_terms = _content_terms(asset["query"])
        title_terms = _content_terms(title)
        specific = _specific_terms(asset["query"], keyword) & _specific_terms(title)
        query_coverage = len(query_terms & title_terms) / max(1, len(query_terms))
        # Commons titles often say "Neural Network" or "Transformer Architecture".
        # One non-generic anchor is enough when the selected search phrase itself
        # has a strong title match; requiring two non-generic words discarded these
        # useful, on-topic technical visuals because "network" is generic globally.
        rejected = len(specific) < 1 or query_coverage < 0.8
    else:
        query_terms = _content_terms(asset["query"], keyword)
        title_terms = _content_terms(title)
        shared = query_terms & title_terms
        specific = {
            term for term in shared
            if term not in GENERIC_SUBJECT_TERMS
            and term.rstrip("s") not in GENERIC_SUBJECT_TERMS
        }
        rejected = bool(shared and not specific)
    if rejected:
        print(
            f"[visual] wikimedia still rejected for '{keyword}': "
            f"insufficient topic-specific title match {sorted(specific)[:4]}"
        )
        return None
    asset.setdefault("asset_id", f"wikimedia:{title}")
    # The image search already required a query match; do not overstate it as a
    # semantic caption/content match.
    asset.setdefault("relevance", "title_query_match")
    quality, luma = _visual_quality(Path(asset["path"]))
    asset["visual_quality"] = quality
    asset["luma"] = luma
    return asset


# ---------------------------------------------------------------------------
# Provider: Openverse openly licensed stills (keyless, licence-aware)
# ---------------------------------------------------------------------------
def _openverse_asset(shot: dict, keyword: str, work_dir: Path, index: int,
                     used_titles: set[str] | None = None) -> dict | None:
    try:
        from app.providers.media_sources import search_openverse_images
        hits = search_openverse_images(keyword, limit=10)
    except Exception as exc:
        print(f"[visual] Openverse search unavailable ({type(exc).__name__})")
        return None
    used = {str(value).lower() for value in (used_titles or set())}
    intent_terms = _specific_terms(str(shot.get("visual_intent") or shot.get("visual_purpose") or ""))
    narration_terms = _specific_terms(str(shot.get("narration") or shot.get("claim") or ""))
    ranked = []
    for hit in hits:
        if hit.get("mature") or not hit.get("commercial_use"):
            continue
        title = str(hit.get("title") or "")
        asset_id = str(hit.get("id") or "")
        if not asset_id or asset_id.lower() in used or not hit.get("media_url"):
            continue
        metadata = _specific_terms(title, str(hit.get("creator") or ""))
        score = _term_overlap(intent_terms, metadata) * 1.5 + _term_overlap(narration_terms, metadata) * 0.75
        ranked.append((score, hit))
    if not ranked:
        return None
    score, hit = max(ranked, key=lambda item: (item[0], str(item[1].get("id"))))
    media_url = str(hit.get("media_url") or "")
    parsed = urllib.parse.urlparse(media_url)
    if parsed.scheme != "https" or not parsed.netloc:
        return None
    suffix = Path(parsed.path).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".jpg"
    raw = work_dir / f"openverse_src_{index:03d}{suffix}"
    if not _download_file(media_url, raw) or not raw.is_file() or raw.stat().st_size < 5000:
        return None
    try:
        out = work_dir / f"stock_openverse_{index:03d}.mp4"
        vf = f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},setsar=1,fps={FPS}"
        _run(["ffmpeg", "-y", "-loop", "1", "-i", str(raw), "-t", str(STOCK_CLIP_SECONDS), "-vf", vf, "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p", str(out)])
        if not out.is_file() or out.stat().st_size <= 50000:
            return None
    except Exception:
        return None
    quality, luma = _visual_quality(out)
    return {
        "path": str(out), "provider": "openverse",
        "title": str(hit.get("title") or ""),
        "description": str(hit.get("attribution") or ""),
        "author": str(hit.get("creator") or ""),
        "source_url": str(hit.get("source_url") or ""),
        "license": str(hit.get("license") or ""),
        "license_version": str(hit.get("license_version") or ""),
        "license_url": str(hit.get("license_url") or ""),
        "attribution": str(hit.get("attribution") or ""),
        "attribution_required": bool(hit.get("requires_attribution", True)),
        "license_review_required": True,
        "query": keyword, "asset_id": f"openverse:{hit.get('id')}",
        "relevance": "openverse_metadata_match", "rank_score": score,
        "visual_quality": quality, "luma": luma,
    }


# ---------------------------------------------------------------------------
# Provider: AI image (only with a configured keyed provider)
# ---------------------------------------------------------------------------
def _ai_configured() -> bool:
    """Check configured image providers, including opt-in keyless Pollinations."""
    selected = _env("VISUAL_PROVIDER").lower()
    image_fallback = _env("AI_IMAGE_FALLBACK").lower()
    if image_fallback in {"0", "false", "no", "off"}:
        return False
    if selected in {"off", "none", "local", "wikimedia"}:
        return False
    if any(_env(name) for name in (
        "GEMINI_API_KEY", "FAL_KEY", "REPLICATE_API_TOKEN", "OPENAI_API_KEY",
    )):
        return True
    if _env("CF_ACCOUNT_ID") and _env("CF_API_TOKEN"):
        return True
    # Keyless Pollinations is supported by the adapter, but must be explicitly
    # enabled so a default run never makes an unexpected external image request.
    return (
        selected == "pollinations"
        or _env("IMAGE_PROVIDER").lower() == "pollinations"
        or _env("POLLINATIONS_ENABLED").lower() in {"1", "true", "yes"}
    )


def _ai_asset(shot: dict, keyword: str, work_dir: Path) -> dict | None:
    if not _ai_configured():
        return None
    try:
        from app.visuals import visual_assets
        prompt = str(shot.get("asset_query") or keyword)
        result = visual_assets.generate_image(prompt, work_dir, aspect="9:16")
    except Exception:
        return None
    if not result or not result.get("path") or not Path(result["path"]).is_file():
        return None
    provider = str(result.get("provider") or "")
    if provider in ("", "local", "none"):
        return None
    return {
        "path": str(result["path"]),
        "provider": provider,
        "title": "",
        "license": "",
        "query": keyword,
        "relevance": "prompt_generated",
    }


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------
def _load_registered_generated_video(shot: dict, work_dir: Path, keyword: str) -> dict | None:
    """Load an explicitly selected generated clip only after provenance checks.

    This resolver never calls a generation API. A shot opts in through
    generated_video_asset, set to a media path or its .asset.json sidecar.
    """
    import hashlib
    import json

    reference = str(shot.get('generated_video_asset') or '').strip()
    if not reference:
        return None
    candidate = Path(reference).expanduser()
    if not candidate.is_absolute():
        candidate = (Path(work_dir) / candidate).resolve()
    if candidate.name.endswith('.asset.json'):
        sidecar = candidate
        media = Path(str(candidate)[:-len('.asset.json')])
    else:
        media = candidate
        sidecar = media.with_suffix(media.suffix + '.asset.json')
    if not media.is_file() or not sidecar.is_file():
        raise ValueError('generated asset or provenance sidecar is missing')
    record = json.loads(sidecar.read_text(encoding='utf-8'))
    if record.get('schema') != 'nextdecode.generated-video-asset.v1':
        raise ValueError('unsupported generated asset provenance schema')
    if record.get('status') != 'qualified' or not record.get('requires_editorial_review', True):
        raise ValueError('generated asset is not qualified for editorial review')
    if not record.get('provider') or not record.get('task_id') or not record.get('model'):
        raise ValueError('generated asset provider/model/task provenance is incomplete')
    if Path(str(record.get('local_path') or '')).resolve() != media.resolve():
        raise ValueError('generated asset sidecar path does not match selected media')
    digest = hashlib.sha256(media.read_bytes()).hexdigest()
    if not record.get('sha256') or digest != record.get('sha256'):
        raise ValueError('generated asset SHA-256 mismatch')
    from app.providers.video_generation_workflow import _probe_video
    probed = _probe_video(media)
    declared = record.get('metadata') or {}
    for key in ('width', 'height', 'size_bytes'):
        if int(declared.get(key) or 0) != int(probed.get(key) or 0):
            raise ValueError(f'generated asset {key} metadata mismatch')
    duration = float(probed.get('duration_seconds') or 0)
    if duration <= 0 or not probed.get('width') or not probed.get('height'):
        raise ValueError('generated asset media probe is incomplete')
    return {
        'path': str(media.resolve()), 'provider': 'generated_video',
        'title': str(record.get('model') or 'Generated video'),
        'description': str(record.get('prompt') or ''), 'query': keyword,
        'license': 'provider_generated; verify provider terms before publication',
        'asset_id': 'generated:{}:{}'.format(record.get('provider'), record.get('task_id')),
        'media_type': 'video', 'duration': duration,
        'generated_provenance': {
            'provider': record.get('provider'), 'model': record.get('model'),
            'task_id': record.get('task_id'), 'run_id': record.get('run_id'),
            'sidecar_path': str(sidecar.resolve()), 'sha256': digest,
            'metadata': probed, 'requires_editorial_review': True,
        },
        'relevance': 'prompt_generated_unreviewed', 'fallback_reason': '',
    }


def _registered_generated_video(shot: dict, work_dir: Path, keyword: str) -> dict | None:
    try:
        return _load_registered_generated_video(shot, work_dir, keyword)
    except Exception as exc:
        print(f"[visual] generated asset rejected for scene {shot.get('index', '?')}: {type(exc).__name__}")
        # Invalid optional generated media must not poison the shot. Continue
        # through the same stock/local visual fallback chain as any miss.
        return None




def _local_component_asset(shot: dict, scene: dict, work_dir: Path, index: int) -> dict | None:
    """Create a topic-aware, original vector visual when licensed footage is absent."""
    narration = str(shot.get("claim") or shot.get("caption") or scene.get("narration") or "").strip()
    topic = str(shot.get("topic") or scene.get("topic") or "").strip()
    subject = str(scene.get("visual_subject") or scene.get("subject") or shot.get("visual_subject") or shot.get("visual") or topic).strip()
    action = str(scene.get("visual_action") or scene.get("action") or shot.get("visual_action") or shot.get("action") or "").strip()
    combined = f"{topic} {subject} {narration} {action}".lower()
    work_dir = Path(work_dir)
    component_dir = work_dir / "components"
    component_dir.mkdir(parents=True, exist_ok=True)
    svg_path = component_dir / f"scene_{index:03d}.svg"
    png_path = component_dir / f"scene_{index:03d}.png"

    scene_type = str(scene.get("scene_type") or "").lower()
    if any(term in combined for term in ("protomaps", "pmtiles", "map tiles", "vector tiles", "map server", "cdn")) and scene_type == "diagram":
        spec = {
            "kind": "flow_diagram",
            "title": "How self-hosted map tiles work",
            "nodes": [
                {"title": "PMTiles archive", "detail": "Vector map tiles stored in one portable file"},
                {"title": "CDN storage", "detail": "Serve the archive from edge infrastructure"},
                {"title": "Map client", "detail": "Request only the map data needed for the view"},
            ],
        }
    elif any(term in combined for term in ("protomaps", "pmtiles", "map tiles", "vector tiles", "map server", "cdn")):
        spec = {
            "kind": "icon_tile",
            "symbol": "chip",
            "title": "Self-hosted map tiles",
            "caption": (narration or action or "Vector map data served from your own infrastructure")[:90],
        }
    elif any(term in combined for term in ("research agent", "ai agent", "open-ended research")):
        spec = {
            "kind": "flow_diagram",
            "title": "The research-agent loop",
            "nodes": [
                {"title": "Research question", "detail": "Define the problem and evidence target"},
                {"title": "Agent exploration", "detail": "Search, test hypotheses and run analysis"},
                {"title": "Human evaluation", "detail": "Check results, limits and reproducibility"},
            ],
        }
    elif any(term in combined for term in ("workflow", "steps", "process", "mechanism", "system", "architecture")):
        spec = {
            "kind": "flow_diagram",
            "title": (subject or topic or "How it works")[:54],
            "nodes": [
                {"title": "Input", "detail": narration[:92] or subject[:92]},
                {"title": "Mechanism", "detail": action[:92] or "Process the input through the described system"},
                {"title": "Outcome", "detail": "Review the result against the evidence and intended use"},
            ],
        }
    else:
        spec = {
            "kind": "icon_tile",
            "symbol": "chip" if any(x in combined for x in ("technology", "software", "computer", "server")) else "spark",
            "title": (subject or topic or "Key idea")[:48],
            "caption": (narration or action or topic)[:90],
        }

    try:
        render_scene_component({
            "visual_source": "vector_component",
            "scene_id": f"scene_{index:03d}",
            "narration": narration,
            "component": spec,
        }, svg_path)
        completed = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(svg_path), "-frames:v", "1", str(png_path)],
            capture_output=True, timeout=30,
        )
        if completed.returncode != 0 or not png_path.is_file() or png_path.stat().st_size < 1024:
            return None
    except Exception:
        return None
    return {
        "path": str(png_path),
        "provider": "motion_graphic",
        "title": spec.get("title", ""),
        "asset_id": f"local:vector-component:{index}",
        "card_variant": spec.get("kind", "vector_component"),
        "scene_type": "diagram" if spec.get("kind") == "flow_diagram" else "typography",
        "visual_type": "motion_graphic",
        "relevance": "narration_derived",
        "relevance_confidence": "high",
        "semantic_review": False,
        "review_reason": "",
        "relevance_reason": "original local vector component generated from the narration beat",
        "fallback_reason": "no sufficiently relevant licensed visual asset; used original local graphic",
        "generated_locally": True,
        "external_api_used": False,
    }


def resolve_scene(shot: dict, work_dir: Path, planner: dict, *,
                  used_titles: set[str] | None = None,
                  dry_run: bool = False) -> dict:
    """Resolve one shot through the provider chain and record why it ran.

    The returned dict always carries ``provider``, ``scene_type``,
    ``fallback_reason`` (empty when a real asset was used) and ``asset_id`` so
    downstream stages can report quality honestly.
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    index = int(shot.get("index", 0) or 0)
    scene = planner.get("scenes", {}).get(index) or build_scene_brief(shot, index=index)
    visual_type = scene.get("visual_type", "broll")
    scene_type = scene.get("scene_type", "footage")
    keyword = scene.get("keyword") or extract_keyword(shot)
    query = scene.get("search_query") or keyword
    queries = list(scene.get("queries") or [query])
    if not dry_run:
        contextual_queries = _moe_context_still_queries(scene, keyword)
        queries = contextual_queries + [item for item in queries if item not in contextual_queries]
    used_ids = planner.setdefault("used_asset_ids", set())
    reasons: list[str] = []

    def resolved(detail: dict) -> dict:
        detail.setdefault("visual_type", visual_type)
        detail.setdefault("scene_type", scene_type)
        detail.setdefault("keyword", keyword)
        detail.setdefault("query", query)
        detail.setdefault("fallback_reason", "")
        detail.setdefault("asset_id", "")
        # Keep the full attempt trail, including when a lower-priority provider
        # eventually succeeded, so metadata explains the visible choice.
        detail.setdefault("attempts", list(reasons))
        validation = validate_asset_relevance(scene, detail)
        detail.update(validation)
        if detail.get("provider") == "generated_video":
            detail.update({
                "relevance_confidence": "medium", "semantic_review": True,
                "review_reason": "generated footage has not received a visual/editorial review",
                "relevance_reason": "prompt provenance verified; visual semantics remain unverified",
                "visual_quality": "unreviewed",
            })
        if detail.get("provider") in {"pixabay", "coverr", "wikimedia", "openverse"} and validation.get("relevance_confidence") == "low":
            reasons.append(
                f"{detail.get('provider', 'stock')} candidate rejected: "
                f"{validation.get('relevance_reason') or 'weak topic-specific match'}"
            )
            return None
        if detail.get("provider") in {"pixabay", "coverr", "wikimedia", "openverse", "ai_image"}:
            vision_enabled = False
            try:
                from app.visuals import vision_review
                vision_enabled = vision_review.enabled()
                vision = vision_review.review_asset(scene, detail)
            except Exception as exc:
                vision = {"checked": False, "reason": f"vision review unavailable ({type(exc).__name__})"}
            detail["vision_review"] = vision
            if vision.get("checked"):
                verdict = str(vision.get("relevance") or "medium")
                visual_quality = str(vision.get("quality") or "unknown")
                detail["relevance_confidence"] = verdict
                detail["visual_quality"] = visual_quality
                detail["semantic_review"] = verdict != "high" or visual_quality == "low"
                detail["relevance_reason"] = f"vision review: {vision.get('reason', '')}"
                detail["review_reason"] = (
                    "low visual quality" if visual_quality == "low"
                    else "" if verdict == "high"
                    else "vision review requested human confirmation"
                )
                if verdict != "high" or visual_quality == "low":
                    reasons.append(
                        f"{detail.get('provider', 'visual')} candidate rejected by vision review: "
                        f"{verdict} relevance, {visual_quality} visual quality; "
                        f"{vision.get('reason') or 'insufficient visual support'}"
                    )
                    return None
            elif vision_enabled:
                reasons.append(
                    f"{detail.get('provider', 'visual')} candidate rejected because configured "
                    f"vision review was unavailable: {vision.get('reason') or 'no verdict'}"
                )
                return None
        if detail.get("provider") in {"pixabay", "coverr", "wikimedia", "openverse"}:
            previous = next(reversed(planner.get("resolved") or []), None)
            previous_path = Path(str((previous or {}).get("asset_path") or ""))
            current_path = Path(str(detail.get("path") or ""))
            if (
                previous
                and previous.get("provider") in {"pixabay", "coverr", "wikimedia", "openverse"}
                and int(previous.get("index", -2)) == index - 1
                and previous_path.is_file()
                and current_path.is_file()
            ):
                try:
                    from app.visuals.asset_qa import _dhash
                    previous_hash = _dhash(previous_path, seek_seconds=float(previous.get("duration_seconds") or 0) / 2)
                    current_hash = _dhash(current_path, seek_seconds=float(detail.get("duration") or 0) / 2)
                    if previous_hash is not None and current_hash is not None:
                        distance = (previous_hash ^ current_hash).bit_count()
                        if distance <= 3:
                            reasons.append(f"candidate rejected: adjacent composition too similar (dHash distance {distance})")
                            return None
                except Exception:
                    # Composition QA is advisory when FFmpeg cannot decode a frame;
                    # provenance and semantic review remain mandatory.
                    pass
        planner.setdefault("resolved", []).append({
            "index": index,
            "asset_path": str(detail.get("path") or ""),
            "duration_seconds": detail.get("duration"),
            "scene_type": scene_type,
            "visual_type": visual_type,
            "provider": detail.get("provider"),
            "query": detail.get("query") or query,
            "asset_id": detail.get("asset_id") or "",
            "card_variant": detail.get("card_variant") or "",
            "fallback_reason": detail.get("fallback_reason") or "",
            "relevance": detail.get("relevance") or "",
            "relevance_confidence": detail.get("relevance_confidence") or "",
            "semantic_review": bool(detail.get("semantic_review")),
            "review_reason": detail.get("review_reason") or "",
            "vision_checked": bool((detail.get("vision_review") or {}).get("checked")),
            "vision_relevance": (detail.get("vision_review") or {}).get("relevance") or "",
        })
        return detail

    # Generated media is never invoked here: only a pre-generated, explicitly
    # selected sidecar can be registered for the existing editorial review gate.
    if shot.get("generated_video_asset"):
        try:
            generated = _registered_generated_video(shot, work_dir, keyword)
        except Exception as exc:
            reasons.append("generated asset rejected: {}".format(type(exc).__name__))
            generated = None
        if generated:
            _log_scene(index, visual_type, "registered generated video", keyword)
            accepted = resolved(generated)
            if accepted is not None:
                return accepted
            reasons.append("registered generated clip could not pass editorial/provenance registration")

    # A topic match is not a visual instruction.  Only render the MoE diagram
    # for beats explicitly classified as diagrams; forcing every supporting
    # sentence through this branch caused the same graphic to fill the entire
    # video and overrode the planner's b-roll/typography variety decisions.
    if scene_type == "diagram" and (
        visual_type == "motion_graphic" or scene.get("intent") == "mechanism"
    ):
        diagram = _moe_scene_graphic(shot, work_dir, index) or _moe_diagram_graphic(shot, work_dir, index)
        if diagram:
            _log_scene(index, "motion_graphic", "local MoE diagram", keyword)
            return resolved({
                "path": str(diagram),
                "provider": "motion_graphic",
                "visual_type": "motion_graphic",
                "scene_type": "diagram",
                "title": "MoE routing diagram",
                "card_variant": "moe_diagram",
                "asset_id": f"local:moe-diagram:{index}",
                "relevance": "narration_derived",
                "relevance_confidence": "high",
                "semantic_review": False,
                "relevance_reason": "original diagram generated from this narration beat",
                "fallback_reason": "",
            })

    if visual_type == "motion_graphic":
        if scene.get("card_variant") == "recap":
            card = _recap_graphic(
                shot, work_dir, index, list(scene.get("recap_figures") or [])
            )
            card_variant = "recap"
        elif scene.get("card_variant") == "typography":
            graphic_shot = dict(shot)
            title = str(scene.get("typography_title") or "KEY MECHANISM")
            graphic_shot["claim"] = title
            graphic_shot["caption"] = title
            card = _motion_graphic(graphic_shot, work_dir, index)
            card_variant = "typography"
        else:
            card = _motion_graphic(shot, work_dir, index)
            card_variant = "number"
        if card:
            _log_scene(index, visual_type, "local card", keyword)
            detail = {
                "path": str(card), "provider": "motion_graphic", "title": "",
                "card_variant": card_variant,
            }
            if card_variant == "typography":
                detail.update({
                    "scene_type": "typography",
                    "visual_type": "motion_graphic",
                    "asset_id": f"local:moe-typography:{index}",
                    "relevance": "narration_derived",
                    "relevance_confidence": "high",
                    "semantic_review": False,
                    "relevance_reason": "original typography interstitial derived from the narration beat",
                })
            return resolved(detail)
        reasons.append("local card render failed")

    if not dry_run:
        if visual_type == "broll":
            if not scene.get("allow_stock"):
                reasons.append("stock budget reserved for non-b-roll scenes")
            elif planner.get("stock_used", 0) < planner.get("stock_cap", 0):
                providers = (("pixabay", _pixabay_asset), ("coverr", _coverr_asset))
                tried = False
                for provider, fetch in providers:
                    key_name = "PIXABAY_API_KEY" if provider == "pixabay" else "COVERR_API_KEY"
                    if not _env(key_name):
                        continue
                    tried = True
                    for candidate in queries[:2]:
                        asset = fetch(candidate, work_dir, index, used_ids=used_ids, scene=scene)
                        if not asset:
                            continue
                        asset.update({
                            "visual_type": visual_type,
                            "scene_type": scene_type,
                            "keyword": keyword,
                            "query": candidate,
                            "fallback_reason": "",
                        })
                        validation = validate_asset_relevance(scene, asset)
                        if validation.get("relevance_confidence") == "low":
                            if asset.get("visual_quality") == "low_light":
                                reasons.append(
                                    f"low-light clip for '{candidate}' skipped"
                                )
                            else:
                                reasons.append(
                                    f"weak lexical match for '{candidate}' skipped"
                                )
                            continue
                        _log_scene(index, visual_type, provider, candidate)
                        accepted = resolved(asset)
                        if accepted is None:
                            continue
                        planner["stock_used"] = planner.get("stock_used", 0) + 1
                        if asset.get("asset_id"):
                            used_ids.add(str(asset["asset_id"]))
                        return accepted
                if not tried:
                    reasons.append("no configured stock video provider (Pixabay/Coverr)")
                else:
                    reasons.append("no unused stock video matched")
            else:
                reasons.append("stock scene cap reached")

            still = _wikimedia_asset(shot, keyword, work_dir, index, used_titles,
                                     extra_queries=queries)
            if still:
                _log_scene(index, visual_type, "wikimedia", still.get("query") or keyword)
                still.update({
                    "visual_type": visual_type,
                    "scene_type": scene_type,
                    "keyword": keyword,
                    "fallback_reason": "",
                })
                accepted = resolved(still)
                if accepted is not None:
                    return accepted
            reasons.append("no unused Wikimedia still matched")

            openverse = None
            if _env("OPENVERSE_ENABLED").lower() in {"1", "true", "yes", "on"}:
                openverse = _openverse_asset(shot, keyword, work_dir, index, used_titles)
            if openverse:
                openverse.update({
                    "visual_type": visual_type,
                    "scene_type": scene_type,
                    "keyword": keyword,
                    "fallback_reason": "",
                })
                accepted = resolved(openverse)
                if accepted is not None:
                    return accepted
                reasons.append("Openverse still rejected by relevance/visual review")

            if _ai_configured():
                ai = _ai_asset(shot, keyword, work_dir)
                if ai:
                    _log_scene(index, visual_type, "ai_image", keyword)
                    ai.update({
                        "visual_type": visual_type,
                        "scene_type": scene_type,
                        "keyword": keyword,
                        "fallback_reason": "",
                    })
                    accepted = resolved(ai)
                    if accepted is not None:
                        return accepted
                    reasons.append("AI image candidate rejected by visual review")
                else:
                    reasons.append("AI image provider failed")
            else:
                reasons.append("AI image provider not configured")
    else:
        reasons.append("dry run: network providers skipped")

    reason = "; ".join(reasons) or "no visual provider available"
    topic_text = str(shot.get("topic") or "").lower()
    is_moe_topic = any(term in topic_text for term in ("mixture of experts", "few experts", "expert routing", "mixtral", "moe"))
    narration_text = str(
        shot.get("claim") or shot.get("caption") or shot.get("visual") or ""
    ).lower()
    context_visual_is_grounded = any(
        term in narration_text
        for term in (
            "token arrives", "open weights", "specialist networks",
            "gpu", "server", "processor", "hardware", "compute",
            "parameter", "memory", "chip",
        )
    )
    if (
        is_moe_topic
        and scene_type in {"footage", "ui_demo", "product"}
        and context_visual_is_grounded
    ):
        context_graphic = _moe_context_graphic(shot, work_dir, index)
        if context_graphic:
            scene = {**scene, "scene_type": "diagram", "visual_purpose": _visual_purpose("diagram")}
            scene_type = "diagram"
            visual_type = "motion_graphic"
            return resolved({
                "path": str(context_graphic),
                "provider": "motion_graphic",
                "title": "",
                "asset_id": f"local:moe-context:{index}",
                "card_variant": "context",
                "scene_type": "diagram",
                "visual_type": "motion_graphic",
                "relevance": "narration_derived",
                "relevance_confidence": "high",
                "semantic_review": False,
                "review_reason": "",
                "relevance_reason": "original local hardware/network illustration derived from the narration",
                "fallback_reason": "",
            })
    component_asset = _local_component_asset(shot, scene, work_dir, index)
    if component_asset:
        _log_scene(index, "motion_graphic", "original local vector component", keyword)
        return resolved(component_asset)

    fallback = _gradient_caption(shot, work_dir, index)
    if fallback:
        print(f"[visual] scene {index:02d} {visual_type} -> gradient caption (fallback: {reason})")
        return resolved({
            "path": str(fallback),
            "provider": "gradient",
            "title": "",
            "fallback_reason": reason,
            "relevance": "none",
        })
    print(f"[visual] scene {index:02d} {visual_type} -> procedural (fallback: {reason})")
    return resolved({
        "path": None,
        "provider": "procedural",
        "title": "",
        "fallback_reason": reason,
        "relevance": "none",
    })
