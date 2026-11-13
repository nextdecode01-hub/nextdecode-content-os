"""Per-scene visual provider chain for the strong pipeline.

Each shot is classified from its script text as ``motion_graphic`` (numbers,
claims, lists) or ``broll`` (ambient visual) and gets a short English keyword.
Resolution order:

    motion_graphic -> local card (ffmpeg, no API)
    broll          -> Pixabay video -> Pexels video (if configured)
                      -> Wikimedia still -> AI image (only when a keyed
                      provider is configured) -> gradient + caption

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
    "pixabay_video", "pexels_video", "wikimedia_still",
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
    "diagram", "architecture", "network", "pipeline", "workflow", "process",
    "how it works", "flowchart", "schematic", "layer",
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
    """Short, human-meaningful search phrase for stock/still lookup.

    The explicit ``asset_query`` wins because the script stage already turned a
    narration beat into subject phrases; raw narration is only a fallback.
    """
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


def _scene_type(shot: dict, visual_type: str, low: str, quantities: list[tuple[str, str]]) -> str:
    """Map one beat to a concrete visual treatment."""
    if visual_type == "motion_graphic":
        units = [unit for _, unit in quantities if unit]
        repeated_unit = any(units.count(unit) >= 2 for unit in set(units))
        if repeated_unit or any(hint in low for hint in CHART_HINTS):
            return "chart"
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
    text = str(shot.get("claim") or shot.get("caption") or shot.get("visual") or "")
    low = text.lower()
    quantities = _quantities(text)
    has_number = bool(_first_number(text))
    has_claim = any(hint in low for hint in GRAPHIC_HINTS)
    is_list = bool(re.search(r"(^|\s)(1[.)]|2[.)]|3[.)]|first|second|third)(\s|$)", low))
    visual_type = "motion_graphic" if (has_number or has_claim or is_list) else "broll"
    return {
        "visual_type": visual_type,
        "scene_type": _scene_type(shot, visual_type, low, quantities),
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
    text = str(shot.get("claim") or shot.get("caption") or shot.get("visual") or "")
    caption = _clean_card_text(shot.get("caption") or shot.get("claim") or text)
    number = _first_number(text) or _first_number(caption)
    keyword = extract_keyword(shot)
    queries = _query_candidates(shot, keyword)
    scene = classify_scene(shot)
    if scene["visual_type"] == "motion_graphic":
        fallback_chain = list(GRAPHIC_FALLBACK_CHAIN)
    else:
        fallback_chain = list(BROLL_FALLBACK_CHAIN)
    try:
        duration = max(0.0, float(shot.get("duration") or 0.0))
    except (TypeError, ValueError):
        duration = 0.0
    return {
        "index": idx,
        "beat_id": shot.get("beat_id") or f"scene-{idx:02d}",
        "intent": _infer_intent(shot, idx),
        "narration": text,
        "visual_purpose": _visual_purpose(scene["scene_type"]),
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
    stock_cap = max(0, (total - 1) // 2)
    graphic_budget = max(1, total // 2) if total else 0
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
                and graphic_run < MAX_CONSECUTIVE_GRAPHICS
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
            elif (
                duplicate
                or graphic_count >= graphic_budget
                or graphic_run >= MAX_CONSECUTIVE_GRAPHICS
            ):
                # Keep the beat, but let real footage carry it instead of another
                # near-identical card. Captions still show the exact figure.
                brief["visual_type"] = "broll"
                brief["scene_type"] = "footage"
                brief["visual_purpose"] = _visual_purpose("footage")
                brief["fallback_chain"] = list(BROLL_FALLBACK_CHAIN)
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
    digest = hashlib.sha1(keyword.lower().encode("utf-8")).hexdigest()[:16]
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
            "tags": str(hit.get("tags") or "")[:160],
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
    "software", "development", "performance", "programming", "coding", "code",
    "data", "system", "systems", "project", "team", "teams", "work", "worker",
    "office", "measurement", "process", "management", "technology", "computer",
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
    query = str(asset.get("query") or scene.get("search_query") or scene.get("keyword") or "")
    title = str(asset.get("title") or "")
    tags = str(asset.get("tags") or "")

    narration_terms = _content_terms(narration)
    # Compare against the query that actually produced this asset, not every
    # alternate query in the scene.  Using all variants dilutes the overlap and
    # marks clearly tag-related clips as low confidence.
    query_terms = _content_terms(query, scene.get("keyword"))
    asset_terms = _content_terms(title, tags)
    matched_query = sorted(query_terms & asset_terms)
    matched_narration = sorted(narration_terms & asset_terms)
    query_overlap = _term_overlap(query_terms, asset_terms)
    narration_overlap = _term_overlap(narration_terms, asset_terms)

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
        if asset_terms:
            if query_overlap >= 0.5 and len(matched_query) >= 2:
                confidence = "medium"
                reason = "tags share multiple query terms (lexical, not semantic)"
            elif query_overlap >= MIN_TAG_OVERLAP or narration_overlap >= 0.34:
                confidence = "medium"
                reason = "tags share at least one query/narration term (lexical, not semantic)"
            else:
                confidence = "low"
                reason = "tags do not clearly match the narration/query terms"
        else:
            confidence = "medium"
            reason = "provider returned a result for the query; tags unavailable"
        return {
            "relevance_confidence": confidence,
            "semantic_review": True,
            "relevance_reason": reason,
            "matched_terms": sorted(set(matched_query) | set(matched_narration)),
            "review_reason": "stock tag overlap is lexical and needs visual review",
        }

    if provider == "pexels":
        return {
            "relevance_confidence": "medium",
            "semantic_review": True,
            "relevance_reason": "provider orientation/query filter only; tags unavailable",
            "matched_terms": sorted(set(matched_query) | set(matched_narration)),
            "review_reason": "orientation-filtered stock needs visual review",
        }

    if provider == "wikimedia":
        if asset_terms and (query_overlap >= 0.5 or narration_overlap >= 0.34):
            confidence = "medium"
            reason = "title/query lexical match; image content not verified"
        else:
            confidence = "low"
            reason = "title/query match is weak or ambiguous"
        return {
            "relevance_confidence": confidence,
            "semantic_review": True,
            "relevance_reason": reason,
            "matched_terms": sorted(set(matched_query) | set(matched_narration)),
            "review_reason": "still title match needs visual review",
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


def _pick_hit(hits: list[dict], keyword: str, *, used_ids: set[str] | None = None) -> dict | None:
    """Rank stock clips by tag overlap, vertical crop safety and quality.

    Assets already used by another scene are skipped so adjacent shots do not
    repeat the same clip.  A clip must share at least half of the query terms
    with its tags; otherwise a vertical, unrelated clip would win on geometry.
    """
    terms = set(re.findall(r"[a-z0-9]+", keyword.lower()))
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
        tags = set(re.findall(r"[a-z0-9]+", str(hit.get("tags") or "").lower()))
        overlap = (len(terms & tags) / len(terms)) if terms else 0.0
        if overlap < MIN_TAG_OVERLAP:
            continue
        ratio = width / height
        target = 9 / 16
        ratio_fit = max(0.0, 1.0 - abs(ratio - target) / target)
        vertical = 1.0 if ratio < 1 else 0.0
        resolution = min(width, 1920) / 1920
        duration_fit = min(duration, 12.0) / 12.0
        score = (
            overlap * 3.0 + ratio_fit * 2.0 + vertical * 1.0
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
                   used_ids: set[str] | None = None) -> dict | None:
    hit = _pick_hit(_pixabay_hits(keyword), keyword, used_ids=used_ids)
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
        "title": f"Pixabay clip {hit.get('id')}",
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
# Provider slot: Pexels videos (only when PEXELS_API_KEY is set)
# ---------------------------------------------------------------------------
def _pexels_asset(keyword: str, work_dir: Path, index: int, *,
                  used_ids: set[str] | None = None) -> dict | None:
    key = _env("PEXELS_API_KEY")
    if not key:
        return None
    url = "https://api.pexels.com/videos/search?" + urllib.parse.urlencode({
        "query": keyword[:100], "orientation": "portrait", "per_page": "5",
    })
    try:
        request = urllib.request.Request(url, headers={"Authorization": key, "User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(f"[visual] pexels search unavailable ({type(exc).__name__})")
        return None

    used = {str(item) for item in (used_ids or set())}
    candidates: list[tuple[float, str, object, float]] = []
    for video in payload.get("videos") or []:
        video_id = video.get("id")
        asset_id = f"pexels:{video_id}"
        if asset_id in used:
            continue
        best_link, best_file_score = None, -1.0
        for item in video.get("video_files") or []:
            width = int(item.get("width") or 0)
            height = int(item.get("height") or 0)
            link = item.get("link")
            if not link or width <= 0 or height <= 0:
                continue
            ratio = width / height
            score = 2.0 - abs(ratio - 9 / 16) * 3 + min(height, 1920) / 1920
            if score > best_file_score:
                best_link, best_file_score = link, score
        if not best_link:
            continue
        duration = float(video.get("duration") or 0)
        total = best_file_score + min(duration, 20.0) / 40.0
        candidates.append((total, best_link, video_id, duration))
    if not candidates:
        return None
    score, best, video_id, _duration = max(candidates, key=lambda item: (item[0], str(item[2])))

    raw = work_dir / f"pexels_src_{index:03d}.mp4"
    if not _download_file(best, raw):
        return None
    out = _prepare_clip(raw, work_dir / f"stock_pexels_{index:03d}.mp4")
    if not out:
        return None
    quality, luma = _visual_quality(out)
    return {
        "path": str(out),
        "provider": "pexels",
        "title": f"Pexels clip {video_id}",
        "license": "Pexels License",
        "query": keyword,
        "duration": STOCK_CLIP_SECONDS,
        "asset_id": f"pexels:{video_id}",
        "relevance": "provider_orientation_filter",
        "rank_score": round(score, 3),
        "visual_quality": quality,
        "luma": luma,
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
    title = str(asset.get("title") or asset.get("page_url") or index)
    # Reject broad word overlap that does not identify the subject.  Example:
    # query "software development performance" matched a still titled
    # "Performance Measurement - Grassroots Development Programme".
    query_terms = _content_terms(asset["query"], keyword)
    title_terms = _content_terms(title)
    shared = query_terms & title_terms
    specific = {
        term for term in shared
        if term not in GENERIC_SUBJECT_TERMS
        and term.rstrip("s") not in GENERIC_SUBJECT_TERMS
    }
    if shared and not specific:
        print(
            f"[visual] wikimedia still rejected for '{keyword}': "
            f"only generic title terms {sorted(shared)[:4]}"
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
# Provider: AI image (only with a configured keyed provider)
# ---------------------------------------------------------------------------
def _ai_configured() -> bool:
    keys = ("POLLINATIONS_API_KEY", "GEMINI_API_KEY", "FAL_KEY",
            "REPLICATE_API_TOKEN", "OPENAI_API_KEY")
    if any(_env(name) for name in keys):
        return True
    return bool(_env("CF_ACCOUNT_ID") and _env("CF_API_TOKEN"))


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
        if detail.get("provider") in {"pixabay", "pexels", "wikimedia", "ai_image"}:
            try:
                from app.visuals import vision_review
                vision = vision_review.review_asset(scene, detail)
            except Exception as exc:
                vision = {"checked": False, "reason": f"vision review unavailable ({type(exc).__name__})"}
            detail["vision_review"] = vision
            if vision.get("checked"):
                verdict = str(vision.get("relevance") or "medium")
                detail["relevance_confidence"] = verdict
                detail["semantic_review"] = verdict != "high"
                detail["relevance_reason"] = f"vision review: {vision.get('reason', '')}"
                detail["review_reason"] = (
                    "" if verdict == "high" else "vision review requested human confirmation"
                )
        planner.setdefault("resolved", []).append({
            "index": index,
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

    if visual_type == "motion_graphic":
        if scene.get("card_variant") == "recap":
            card = _recap_graphic(
                shot, work_dir, index, list(scene.get("recap_figures") or [])
            )
            card_variant = "recap"
        else:
            card = _motion_graphic(shot, work_dir, index)
            card_variant = "number"
        if card:
            _log_scene(index, visual_type, "local card", keyword)
            return resolved({
                "path": str(card), "provider": "motion_graphic", "title": "",
                "card_variant": card_variant,
            })
        reasons.append("local card render failed")

    if not dry_run:
        if visual_type == "broll":
            if not scene.get("allow_stock"):
                reasons.append("stock budget reserved for non-b-roll scenes")
            elif planner.get("stock_used", 0) < planner.get("stock_cap", 0):
                providers = (("pixabay", _pixabay_asset), ("pexels", _pexels_asset))
                tried = False
                for provider, fetch in providers:
                    key_name = "PIXABAY_API_KEY" if provider == "pixabay" else "PEXELS_API_KEY"
                    if not _env(key_name):
                        continue
                    tried = True
                    for candidate in queries[:2]:
                        asset = fetch(candidate, work_dir, index, used_ids=used_ids)
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
                        planner["stock_used"] = planner.get("stock_used", 0) + 1
                        if asset.get("asset_id"):
                            used_ids.add(str(asset["asset_id"]))
                        _log_scene(index, visual_type, provider, candidate)
                        return resolved(asset)
                if not tried:
                    reasons.append("no stock video provider configured")
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
                return resolved(still)
            reasons.append("no unused Wikimedia still matched")

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
                    return resolved(ai)
                reasons.append("AI image provider failed")
            else:
                reasons.append("AI image provider not configured")
    else:
        reasons.append("dry run: network providers skipped")

    reason = "; ".join(reasons) or "no visual provider available"
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
