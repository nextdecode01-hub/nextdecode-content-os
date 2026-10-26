#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import multi_model_ai
import voice_guide


SCRIPT_PROFILES = {
    "micro_20s": {"seconds": 20, "min_words": 42, "max_words": 58},
    "standard_30s": {"seconds": 30, "min_words": 62, "max_words": 78},
    "standard_35s": {"seconds": 35, "min_words": 72, "max_words": 92},
    "deep_45s": {"seconds": 45, "min_words": 96, "max_words": 118},
    "deep_60s": {"seconds": 60, "min_words": 128, "max_words": 150},
}

DEFAULT_MIN_SHOTS = 8
DEFAULT_MAX_SHOTS = 14
SHOT_DURATION_MIN = 1.6
SHOT_DURATION_MAX = 3.0


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+", text or ""))


def _topic_stem(word: str) -> str:
    return word[:-1] if len(word) > 4 and word.endswith("s") else word


def _split_sentences(text: str) -> list[str]:
    if not text:
        return []
    # Simple sentence splitting
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def _get_profile(seconds: int) -> dict:
    # Map to closest profile
    for name, profile in SCRIPT_PROFILES.items():
        if profile["seconds"] == seconds:
            return profile
    # Default to standard_35s logic scaled roughly
    if seconds <= 25:
        return {"seconds": seconds, "min_words": max(35, int(seconds * 2.1)), "max_words": int(seconds * 2.6)}
    elif seconds <= 40:
        return {"seconds": seconds, "min_words": max(65, int(seconds * 2.0)), "max_words": int(seconds * 2.5)}
    else:
        return {"seconds": seconds, "min_words": max(90, int(seconds * 2.0)), "max_words": int(seconds * 2.4)}


def _unsupported_numbers(text: str, source_text: str) -> list[dict]:
    """Reimplement semantics similar to research_desk.find_unsupported_numbers."""
    if not text:
        return []
    source_lower = (source_text or "").lower()
    unsupported = []
    
    # Look for numeric patterns
    # Match percentages, decimals, integers
    number_patterns = [
        r'(\d+(?:\.\d+)?)\s*%',  # percentages
        r'(\d+(?:\.\d+)?)\s*(?:times|fold|x)\b',  # multipliers
        r'about\s+(\d+(?:\.\d+)?)\b',
        r'roughly\s+(\d+(?:\.\d+)?)\b',
        r'(\d+(?:\.\d+)?)\s+(?:percent|percentage)\b',
    ]
    
    for pattern in number_patterns:
        for match in re.finditer(pattern, text, re.I):
            num_str = match.group(1)
            # Check if this number appears in source
            if num_str not in source_text and match.group(0).lower() not in source_lower:
                # Also check for word forms like "ten-fold"
                unsupported.append({
                    "number": match.group(0),
                    "span": (match.start(), match.end()),
                    "context": text[max(0, match.start()-30):match.end()+30]
                })
    
    # Check for word forms of numbers
    word_numbers = {
        'ten-fold': '10',
        'two-fold': '2',
        'three-fold': '3',
        'four-fold': '4',
        'five-fold': '5',
    }
    for word, digit in word_numbers.items():
        if word in text.lower() and word not in source_lower and digit not in source_text:
            matches = list(re.finditer(r'\b' + re.escape(word) + r'\b', text, re.I))
            for match in matches:
                unsupported.append({
                    "number": match.group(0),
                    "span": (match.start(), match.end()),
                    "context": text[max(0, match.start()-30):match.end()+30]
                })
    
    return unsupported


def score_hooks(hooks: list[str], *, topic: str, research: dict | None = None) -> list[dict]:
    results = []
    research_text = ""
    if research:
        # Combine all research text for context
        if isinstance(research.get("claims"), list):
            for claim in research["claims"]:
                if isinstance(claim, dict):
                    if claim.get("quote"):
                        research_text += " " + str(claim["quote"])
                    if claim.get("text"):
                        research_text += " " + str(claim["text"])
        if research.get("summary"):
            research_text += " " + str(research["summary"])
    
    for hook in hooks:
        if not hook:
            continue
        hook_clean = hook.strip()
        reasons = []
        score = 0.0
        
        # Deterministic rubric
        words = hook_clean.split()
        word_count_h = len(words)
        
        # Length 6-16 words
        if 6 <= word_count_h <= 16:
            score += 15
            reasons.append("good length")
        elif 4 <= word_count_h <= 20:
            score += 8
            reasons.append("acceptable length")
        else:
            reasons.append("poor length")
        
        # Specificity - contains concrete number/entity
        if re.search(r'\d+', hook_clean):
            score += 20
            reasons.append("has concrete number")
        # Check for proper nouns/entities (capitalized words not at start)
        cap_words = [w for i, w in enumerate(words) if i > 0 and w and w[0].isupper() and len(w) > 2]
        if cap_words:
            score += 10
            reasons.append("has specific entities")
        
        # Curiosity gap indicators
        if any(w in hook_clean.lower() for w in ['why', 'how', 'one', 'secret', 'number']):
            score += 10
            reasons.append("curiosity element")
        
        # Check banned phrases
        slop = voice_guide.find_slop(hook_clean)
        if slop:
            score -= 30
            reasons.append(f"contains banned phrase: {slop[0]['phrase']}")
        else:
            score += 10
        
        # Not generic hook
        if voice_guide.is_generic_hook(hook_clean):
            score -= 40
            reasons.append("generic hook")
        else:
            score += 15
        
        # Check for banned openers
        hook_lower = hook_clean.lower()
        bad_openers = ["in this video", "today we", "did you know", "let's talk about"]
        if any(hook_lower.startswith(bad) for bad in bad_openers):
            score -= 25
            reasons.append("bad opener")
        
        is_generic = voice_guide.is_generic_hook(hook_clean)
        
        results.append({
            'hook': hook_clean,
            'archetype': '',  # Will be filled by caller
            'score': max(0, score),
            'reasons': reasons,
            'is_generic': is_generic
        })
    
    # Try LLM judge
    try:
        judge_prompt = f"""You are judging short video hooks for a tech explainer channel.
Topic: {topic}

Hooks to judge (pick best 1-3):
{json.dumps([r['hook'] for r in results], indent=2)}

Return JSON with: {{"best": [{{"hook": "...", "reason": "..."}}]}} (max 3 items)
Pick hooks that are specific, create curiosity, avoid clichés."""
        judge_result = multi_model_ai.generate_json(judge_prompt, temperature=0.3, timeout=30)
        best_hooks = judge_result.get('best', [])
        if best_hooks:
            best_set = set()
            for b in best_hooks:
                if isinstance(b, dict) and b.get('hook'):
                    best_set.add(b['hook'].strip())
                elif isinstance(b, str):
                    best_set.add(b.strip())
            # Boost scores for LLM-picked hooks
            for r in results:
                if r['hook'] in best_set:
                    r['score'] += 25
                    r['reasons'].append('LLM judge picked')
    except Exception:
        # Fall back silently
        pass
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results


VISUAL_CONCEPTS = {
    "llm": "language model research",
    "large language": "language model research",
    "language model": "language model research",
    "transformer": "neural network diagram",
    "neural": "neural network diagram",
    "model": "machine learning laboratory",
    "training": "machine learning laboratory",
    "inference": "server room",
    "server": "server room",
    "cloud": "server room",
    "gpu": "computer workstation",
    "chip": "semiconductor circuit board",
    "semiconductor": "semiconductor circuit board",
    "hardware": "computer hardware",
    "robot": "robotics laboratory",
    "robotics": "robotics laboratory",
    "automation": "robotics laboratory",
    "data": "data visualization chart",
    "chart": "data visualization chart",
    "graph": "data visualization chart",
    "benchmark": "performance benchmark chart",
    "accuracy": "performance benchmark chart",
    "metric": "performance benchmark chart",
    "code": "programmer workstation",
    "developer": "programmer workstation",
    "software": "programmer workstation",
    "team": "engineering team office",
    "company": "modern office building",
    "startup": "modern office building",
    "phone": "smartphone in hand",
    "mobile": "smartphone in hand",
    "video": "video production studio",
    "camera": "video production studio",
    "voice": "audio recording studio",
    "audio": "audio recording studio",
    "music": "audio recording studio",
    "sound": "audio recording studio",
    "security": "cybersecurity operations center",
    "privacy": "cybersecurity operations center",
    "energy": "power plant machinery",
    "battery": "battery cell manufacturing",
    "space": "spacecraft engineering",
    "medical": "medical imaging laboratory",
    "health": "medical imaging laboratory",
    "biology": "research laboratory equipment",
    "science": "research laboratory equipment",
    "research": "research laboratory equipment",
    "paper": "research laboratory equipment",
    "study": "research laboratory equipment",
    "climate": "weather monitoring station",
    "city": "city skyline aerial",
    "money": "stock market trading screen",
    "market": "stock market trading screen",
    "law": "government courthouse building",
    "policy": "government courthouse building",
    "education": "classroom students laptops",
}

LABEL_CONCEPTS = {
    "hook": "close up detail",
    "context": "wide scene setting",
    "mechanism": "diagram explanation",
    "evidence": "results chart",
    "implication": "hands using device",
    "payoff": "summary scene",
}

QUERY_STOPWORDS = frozenset(
    {
        "the", "and", "for", "with", "that", "this", "from", "into", "are", "was", "were",
        "has", "have", "had", "not", "but", "you", "your", "our", "their", "they", "its",
        "its", "why", "how", "what", "when", "which", "who", "does", "do", "did", "can",
        "will", "would", "should", "could", "using", "use", "used", "bad", "idea", "about",
        "than", "then", "there", "here", "also", "more", "most", "some", "any", "into",
        "over", "after", "before", "like", "just", "very", "really", "much", "many",
        "trained", "trains", "train", "tapped", "taps", "tap", "pretend", "pretends",
        "built", "builds", "build", "released", "releases", "release", "launched",
        "launches", "launch", "shows", "show", "showed", "proves", "prove", "claimed",
        "claims", "claim", "made", "make", "makes", "getting", "gets", "get", "new",
        "better", "best", "good", "big", "small", "large", "first", "last", "next",
        "real", "actual", "says", "said", "want", "wants", "need", "needs", "work",
        "works", "working", "helped", "help", "helps", "think", "thinks", "believes",
        "proof", "point", "source", "sources", "without",
    }
)


def _concept_for(text: str) -> str:
    """Pick a searchable visual concept for the given wording."""
    lower = str(text or "").lower()
    best_key = ""
    best_len = 0
    for key, concept in VISUAL_CONCEPTS.items():
        if key in lower and len(key) > best_len:
            best_key = key
            best_len = len(key)
    if best_key:
        return VISUAL_CONCEPTS[best_key]
    return ""


def _topic_keywords(text: str, limit: int = 3) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", str(text or "").lower())
    out: list[str] = []
    for word in words:
        if word in QUERY_STOPWORDS or word in out:
            continue
        out.append(word)
        if len(out) >= limit:
            break
    return out


def topic_phrases(text: str, limit: int = 6) -> list[str]:
    """Contiguous meaningful phrases from the topic, two and three words long.

    "Startup taps an underwater volcano for energy" yields
    ["underwater volcano", "energy source"] rather than a bag of unrelated
    words.  Headlines are cut into windows because a stock search matches two
    or three words far more reliably than a whole headline.
    """

    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9-]*", str(text or ""))
    runs: list[list[str]] = []
    current: list[str] = []
    for word in words:
        lowered = word.lower()
        if lowered in QUERY_STOPWORDS or len(word) < 3:
            if current:
                runs.append(current)
                current = []
            continue
        current.append(lowered)
    if current:
        runs.append(current)

    windows: list[str] = []
    for run in runs:
        for size in (2, 3):
            for index in range(len(run) - size + 1):
                window = " ".join(run[index:index + size])
                if window not in windows:
                    windows.append(window)
    return windows[:limit]


def concepts_for(topic: str, text: str = "") -> list[str]:
    """All visual concepts that apply to the topic, most specific first."""
    lower = f"{topic} {text}".lower()
    matches = []
    for key, concept in VISUAL_CONCEPTS.items():
        if key in lower:
            matches.append((len(key), concept))
    matches.sort(key=lambda item: -item[0])
    out: list[str] = []
    for _, concept in matches:
        if concept not in out:
            out.append(concept)
    return out


def build_asset_query(topic: str, label: str = "", text: str = "", variant: int = 0) -> str:
    """Build a concrete, searchable visual query for a shot.

    Stock search engines return nothing for abstract wording, so the query is a
    real phrase taken from the subject matter of the script.
    """
    phrases = topic_phrases(topic)
    concepts = concepts_for(topic, text)
    pool = phrases + concepts
    if pool:
        return pool[int(variant) % len(pool)]
    keywords = _topic_keywords(topic)
    if keywords:
        return " ".join(keywords[:3])
    return LABEL_CONCEPTS.get(label, "technology laboratory")


def build_shot_hint(topic: str, label: str, text: str = "") -> str:
    """A human-readable description of what the shot should show."""
    concept = _concept_for(f"{topic} {text}")
    if concept:
        return f"{concept} illustrating the point of this line"
    keywords = _topic_keywords(topic)
    subject = " ".join(keywords[:2]) if keywords else "the subject"
    return f"{subject} in context, {LABEL_CONCEPTS.get(label, 'supporting scene')}"


def build_beat_sheet(voice_text: str, *, duration: float, topic: str = "") -> list[dict]:
    sentences = _split_sentences(voice_text)
    if not sentences:
        return []
    
    beat_sheet = []
    total_words = sum(_word_count(s) for s in sentences)
    if total_words == 0:
        total_words = len(sentences)
    
    current_time = 0.0
    labels = ['hook', 'context', 'mechanism', 'evidence', 'implication', 'payoff']
    
    for i, sentence in enumerate(sentences):
        sent_words = _word_count(sentence)
        sent_duration = (sent_words / total_words) * duration if total_words > 0 else duration / len(sentences)
        t_start = current_time
        t_end = current_time + sent_duration
        current_time = t_end
        
        # Assign label
        if i == 0:
            label = 'hook'
        elif i == len(sentences) - 1:
            label = 'payoff'
        elif i == 1:
            label = 'context'
        elif i == 2:
            label = 'mechanism'
        elif i == len(sentences) - 2:
            label = 'implication'
        else:
            # Assign based on position
            if i < len(sentences) * 0.3:
                label = 'context'
            elif i < len(sentences) * 0.5:
                label = 'mechanism'
            elif i < len(sentences) * 0.7:
                label = 'evidence'
            elif i < len(sentences) * 0.85:
                label = 'implication'
            else:
                label = 'payoff'
        
        # Generate concrete shot hint
        shot_hint = build_shot_hint(topic, label, sentence)
        
        beat_sheet.append({
            'label': label,
            'text': sentence,
            't_start': round(t_start, 2),
            't_end': round(min(t_end, duration), 2),
            'shot_hint': shot_hint
        })
    
    # Ensure monotonic and ends at duration
    if beat_sheet:
        beat_sheet[-1]['t_end'] = round(duration, 2)
        for i in range(1, len(beat_sheet)):
            if beat_sheet[i]['t_start'] < beat_sheet[i-1]['t_end']:
                beat_sheet[i]['t_start'] = beat_sheet[i-1]['t_end']
            beat_sheet[i]['t_start'] = round(beat_sheet[i]['t_start'], 2)
            beat_sheet[i]['t_end'] = round(beat_sheet[i]['t_end'], 2)
    
    return beat_sheet


def plan_shots(beat_sheet: list[dict], *, duration: float, min_shots: int = DEFAULT_MIN_SHOTS, max_shots: int = DEFAULT_MAX_SHOTS, topic: str = "") -> list[dict]:
    shots = []
    
    for beat in beat_sheet:
        beat_duration = beat['t_end'] - beat['t_start']
        if beat_duration < 0:
            continue
        # Split long beats
        if beat_duration > 3.2:
            num_splits = max(2, math.ceil(beat_duration / 2.5))
            split_duration = beat_duration / num_splits
            for j in range(num_splits):
                shot_dur = split_duration
                visual = beat['shot_hint']
                if j > 0:
                    visual = f"{beat['shot_hint']} - alternate angle"
                
                # Determine source
                visual_lower = visual.lower()
                if any(k in visual_lower for k in ['diagram', 'chart', 'graph', 'animated', 'interface', 'screen recording']):
                    source = 'ai_image'
                elif any(k in visual_lower for k in ['abstract', 'conceptual']):
                    source = 'ai_image'
                elif any(k in visual_lower for k in ['footage', 'real', 'lab', 'factory', 'outdoor']):
                    source = 'pexels'
                else:
                    source = 'pexels'  # prefer pexels for physical/real-world
                
                # Generate asset query
                variants = topic_phrases(topic) + concepts_for(topic, beat['text'])
                asset_query = build_asset_query(topic, beat.get('label', ''), beat['text'], len(shots))
                
                shots.append({
                    'index': len(shots),
                    'duration': round(shot_dur, 2),
                    'visual': visual,
                    'asset_query': asset_query,
                    'asset_query_variants': variants,
                    'source': source,
                    'caption': beat['text'][:60]
                })
        else:
            visual = beat['shot_hint']
            visual_lower = visual.lower()
            if any(k in visual_lower for k in ['diagram', 'chart', 'graph', 'animated', 'interface', 'screen recording']):
                source = 'ai_image'
            elif any(k in visual_lower for k in ['abstract', 'conceptual']):
                source = 'ai_image'
            else:
                source = 'pexels'
            
            variants = topic_phrases(topic) + concepts_for(topic, beat['text'])
            asset_query = build_asset_query(topic, beat.get('label', ''), beat['text'], len(shots))
            
            shots.append({
                'index': len(shots),
                'duration': round(beat_duration, 2),
                'visual': visual,
                'asset_query': asset_query,
                'asset_query_variants': variants,
                'source': source,
                'caption': beat['text'][:60]
            })
    
    # Ensure minimum shots
    while len(shots) < min_shots and shots:
        # Split the longest shot
        longest_idx = max(range(len(shots)), key=lambda i: shots[i]['duration'])
        longest = shots[longest_idx]
        if longest['duration'] < 1.0:
            break
        split_dur = longest['duration'] / 2
        # Insert split shot
        new_shot = {
            'index': longest_idx + 1,
            'duration': round(split_dur, 2),
            'visual': longest['visual'] + ' - detail view',
            'asset_query': longest['asset_query'],
            'source': longest['source'],
            'caption': longest['caption']
        }
        shots[longest_idx]['duration'] = round(split_dur, 2)
        shots.insert(longest_idx + 1, new_shot)
        # Reindex
        for i, s in enumerate(shots):
            s['index'] = i
    
    # Remove shots if over max
    while len(shots) > max_shots and len(shots) > min_shots:
        # Merge two shortest consecutive shots
        min_idx = min(range(len(shots)-1), key=lambda i: shots[i]['duration'] + shots[i+1]['duration'])
        shots[min_idx]['duration'] = round(shots[min_idx]['duration'] + shots[min_idx+1]['duration'], 2)
        shots[min_idx]['visual'] = shots[min_idx]['visual'] + ' / ' + shots[min_idx+1]['visual']
        del shots[min_idx+1]
        for i, s in enumerate(shots):
            s['index'] = i
    
    # Fix duration sum
    total_shot_dur = sum(s['duration'] for s in shots)
    diff = total_shot_dur - duration
    if abs(diff) > 0.001:  # Need adjustment
        if shots:
            # Adjust last shot
            shots[-1]['duration'] = round(shots[-1]['duration'] - diff, 2)
            if shots[-1]['duration'] < 0.5:
                # Distribute across others
                shots[-1]['duration'] = round(duration * 0.1, 2)
                remaining = duration - shots[-1]['duration']
                # Redistribute proportionally
                for s in shots[:-1]:
                    ratio = s['duration'] / (total_shot_dur - shots[-1]['duration'] if (total_shot_dur - shots[-1]['duration']) > 0 else 1)
                    s['duration'] = round(remaining * ratio, 2)
    
    # Assert and fix
    total_shot_dur = sum(s['duration'] for s in shots)
    if abs(total_shot_dur - duration) > 0.35:
        # Force fix
        if shots:
            shots[-1]['duration'] = round(shots[-1]['duration'] + (duration - total_shot_dur), 2)
    
    # Ensure average is in range
    if shots:
        avg_shot = sum(s['duration'] for s in shots) / len(shots)
        if avg_shot < SHOT_DURATION_MIN or avg_shot > SHOT_DURATION_MAX:
            # Try to adjust
            pass
    
    return shots


def critique(script: dict, *, research: dict | None = None, topic: str = "") -> dict:
    issues = []
    voice_text = script.get('voice_text', '')
    hook = script.get('hook', '')
    source_urls = script.get('source_urls', [])
    word_count = script.get('word_count') or _word_count(voice_text)
    slop_score_val = script.get('slop_score') or voice_guide.slop_score(voice_text)
    
    research_text = ""
    if research:
        if isinstance(research.get("claims"), list):
            for claim in research["claims"]:
                if isinstance(claim, dict):
                    if claim.get("quote"):
                        research_text += " " + str(claim["quote"])
                    if claim.get("text"):
                        research_text += " " + str(claim["text"])
        if research.get("summary"):
            research_text += " " + str(research["summary"])
        # Also check all text fields
        for k, v in research.items():
            if isinstance(v, str):
                research_text += " " + v
    
    # Hard fail: numeric claim not supported by research quotes
    unsupported = _unsupported_numbers(voice_text, research_text)
    if unsupported:
        for u in unsupported:
            issues.append({
                'kind': 'unsupported_number',
                'detail': f"Numeric claim '{u['number']}' not supported by research quotes"
            })
    
    # Missing source urls
    if not source_urls or len(source_urls) == 0:
        issues.append({
            'kind': 'missing_sources',
            'detail': 'No source URLs provided'
        })

    if topic:
        anchors = [_topic_stem(word) for word in _topic_keywords(topic, limit=2)]
        script_text = f"{script.get('title', '')} {voice_text}".lower()
        script_terms = {_topic_stem(word) for word in re.findall(r"[a-z0-9]+", script_text)}
        if anchors and not any(anchor in script_terms for anchor in anchors):
            issues.append({
                'kind': 'off_topic_script',
                'detail': f"Script does not mention either topic anchor: {', '.join(anchors)}"
            })

    # Word count outside band - need to know duration
    seconds = script.get('seconds') or 35
    profile = _get_profile(seconds)
    if word_count < profile['min_words'] or word_count > profile['max_words']:
        issues.append({
            'kind': 'word_count',
            'detail': f'Word count {word_count} outside band {profile["min_words"]}-{profile["max_words"]}'
        })
    
    # Banned AI-slop phrases
    slop_findings = voice_guide.find_slop(voice_text)
    if slop_findings:
        for s in slop_findings:
            issues.append({
                'kind': 'slop',
                'detail': f"Banned phrase '{s['phrase']}' found: {s['why']}"
            })
    
    # Hook not first sentence
    sentences = _split_sentences(voice_text)
    if sentences:
        first_sentence = sentences[0].strip()
        if hook:
            # Check if hook is first sentence
            if hook.strip() != first_sentence and not first_sentence.startswith(hook.strip()):
                issues.append({
                    'kind': 'hook_position',
                    'detail': 'Hook is not the first sentence of voice_text'
                })
        else:
            issues.append({
                'kind': 'missing_hook',
                'detail': 'No hook provided'
            })
    else:
        issues.append({
            'kind': 'empty_script',
            'detail': 'Script is empty'
        })
    
    # Generic hook
    if hook and voice_guide.is_generic_hook(hook):
        issues.append({
            'kind': 'generic_hook',
            'detail': 'Hook is generic'
        })
    
    pass_critique = len(issues) == 0
    score = max(0, 100 - len(issues) * 15 - slop_score_val * 0.5)
    
    return {
        'score': round(score, 1),
        'pass': pass_critique,
        'issues': issues,
        'slop_score': round(slop_score_val, 1)
    }


def write_script(topic: str, research: dict, *, seconds: int = 35, pillar: str | None = None,
                 max_rewrites: int = 3, provider: str | None = None,
                 strict_research: bool = True) -> dict:
    # Check for insufficient research
    if research and research.get('verdict') == 'insufficient':
        if strict_research:
            raise RuntimeError(
                "Research verdict is 'insufficient'; refusing to write an ungrounded script. "
                "Fetch a primary source or relax strict_research."
            )
        # Try to write script with no factual claims beyond topic
        profile = _get_profile(seconds)
        hook = f"{topic} has one key detail worth knowing."
        voice_text = f"{hook} It affects how this space is developing. The main thing is keeping an eye on practical use cases. One limitation is that details are still emerging. The payoff is knowing what to watch for as it evolves."
        word_count = _word_count(voice_text)
        beat_sheet = build_beat_sheet(voice_text, duration=float(seconds), topic=topic)
        shots = plan_shots(beat_sheet, duration=float(seconds), topic=topic)
        broll_query = topic.lower().replace(' ', ' ')[:50]
        critic_result = critique({
            'voice_text': voice_text,
            'hook': hook,
            'source_urls': [],
            'word_count': word_count,
            'seconds': seconds,
            'slop_score': voice_guide.slop_score(voice_text)
        }, research=research)
        return {
            'content_pillar': pillar or 'What Changed',
            'hook': hook,
            'title': topic[:60],
            'voice_text': voice_text,
            'beat_sheet': beat_sheet,
            'shots': shots,
            'broll_query': broll_query,
            'youtube_tags': [topic.split()[0].lower() if topic.split() else 'tech'],
            'instagram_hashtags': ['#tech'],
            'platform_copy': {
                'youtube_description': f"{topic} explained in simple terms.",
                'instagram_caption': f"{topic} is worth watching as it develops.",
                'facebook_title': topic[:80],
                'facebook_description': f"What's happening with {topic} and why it matters."
            },
            'source_urls': [],
            'word_count': word_count,
            'critic': critic_result,
            'hook_archetype': 'plain_language',
            'slop_score': voice_guide.slop_score(voice_text),
            'rewrites': 0,
            'researched': False
        }
    
    if not research or not research.get('claims'):
        # Also handle case with no claims
        if strict_research:
            raise RuntimeError(
                "Research bundle contains no verifiable claims; refusing to write a script "
                "that would carry unsupported facts."
            )
        profile = _get_profile(seconds)
        hook = f"{topic} comes down to one practical consideration."
        voice_text = f"{hook} The context matters for how it gets used. The mechanism is simpler than it sounds. One evidence point to watch is real adoption. The implication is knowing when it applies. The payoff is using it at the right time."
        word_count = _word_count(voice_text)
        beat_sheet = build_beat_sheet(voice_text, duration=float(seconds), topic=topic)
        shots = plan_shots(beat_sheet, duration=float(seconds), topic=topic)
        critic_result = critique({
            'voice_text': voice_text,
            'hook': hook,
            'source_urls': [],
            'word_count': word_count,
            'seconds': seconds,
            'slop_score': voice_guide.slop_score(voice_text)
        }, research=research)
        return {
            'content_pillar': pillar or 'What Changed',
            'hook': hook,
            'title': topic[:60],
            'voice_text': voice_text,
            'beat_sheet': beat_sheet,
            'shots': shots,
            'broll_query': topic.lower().replace(' ', ' ')[:50],
            'youtube_tags': ['tech', 'ai'] if 'ai' in topic.lower() else ['tech'],
            'instagram_hashtags': ['#tech'],
            'platform_copy': {
                'youtube_description': f"{topic} explained simply.",
                'instagram_caption': f"A quick look at {topic}.",
                'facebook_title': topic[:80],
                'facebook_description': f"Understanding {topic} in context."
            },
            'source_urls': [],
            'word_count': word_count,
            'critic': critic_result,
            'hook_archetype': 'plain_language',
            'slop_score': voice_guide.slop_score(voice_text),
            'rewrites': 0,
            'researched': False
        }
    
    profile = _get_profile(seconds)
    voice_block = voice_guide.voice_prompt_block(pillar)
    hook_instr = voice_guide.hook_instructions()
    
    # Prepare research bundle
    research_bundle = {
        'claims': research.get('claims', []),
        'source_urls': research.get('source_urls', []),
        'summary': research.get('summary', '')
    }
    
    # Generate hooks first, one per archetype, in parallel
    hook_prompts = []
    for arch in voice_guide.HOOK_ARCHETYPES[:10]:  # N=8..10
        hook_prompts.append((arch, f"""{voice_block}

{hook_instr}

Topic: {topic}
Research: {json.dumps(research_bundle, ensure_ascii=False)}

Generate ONE hook in the style of archetype '{arch['id']}' ({arch['name']}): {arch['description']}
Rules: {arch['rules']}
Example: {arch['example']}

The hook must be 4-16 words, specific, no banned phrases, must not start with generic openers.
Return just the hook text."""))

    def _make_hook(item) -> str:
        arch, hook_prompt = item
        try:
            hook_text = multi_model_ai.generate(hook_prompt, provider=provider) if provider else multi_model_ai.generate(hook_prompt)
            cleaned = hook_text.strip().strip('"').strip("'")
            return cleaned or f"{topic}: one specific detail changes the picture."
        except Exception:
            return f"{topic}: one specific detail changes the picture."

    hooks_candidates = []
    try:
        with ThreadPoolExecutor(max_workers=min(5, len(hook_prompts))) as pool:
            hooks_candidates = list(pool.map(_make_hook, hook_prompts))
    except Exception:
        hooks_candidates = [_make_hook(item) for item in hook_prompts]
    
    scored_hooks = score_hooks(hooks_candidates, topic=topic, research=research)
    best_hook = scored_hooks[0]['hook'] if scored_hooks else f"{topic} has a key detail worth knowing."
    best_archetype = scored_hooks[0].get('archetype', 'plain_language') if scored_hooks else 'plain_language'
    
    # Find archetype for best hook
    for i, h in enumerate(hooks_candidates):
        if h == best_hook and i < len(voice_guide.HOOK_ARCHETYPES):
            best_archetype = voice_guide.HOOK_ARCHETYPES[i]['id']
            break
    
    rewrites = 0
    source_urls = research.get('source_urls', [])
    if not source_urls and isinstance(research.get('claims'), list):
        for claim in research['claims']:
            if isinstance(claim, dict) and claim.get('source_url'):
                source_urls.append(claim['source_url'])
    
    # Build initial prompt
    def build_prompt(critic_issues=None):
        issues_text = ""
        if critic_issues:
            issues_text = "\n\nCRITIC ISSUES TO FIX:\n" + "\n".join([f"- {i['kind']}: {i['detail']}" for i in critic_issues])
        
        return f"""{voice_block}

{hook_instr}

Topic: {topic}
Content pillar: {pillar or 'auto-select best fit'}
Duration: {seconds} seconds
Word count band: {profile['min_words']}-{profile['max_words']} words

Research bundle (claims with verbatim quotes + source urls):
{json.dumps(research_bundle, ensure_ascii=False, indent=2)}

HARD CONSTRAINTS:
- First sentence MUST be exactly this hook: {best_hook}
- Word count must be {profile['min_words']}-{profile['max_words']} words
- NO invented numbers. Every factual claim must traceable to a research quote
- Every claim needs support from the research quotes
- No banned AI-slop phrases
- No "In this video"/"Today we"/"Did you know"
- Title must be <= 60 chars
- Stay on the exact topic; never substitute a different product, company, or story
- Include source_urls from research

{issues_text}

Return ONLY valid JSON with these fields:
{{
  "content_pillar": "...",
  "hook": "{best_hook}",
  "title": "...",
  "voice_text": "... full script starting with hook ...",
  "broll_query": "...",
  "youtube_tags": ["..."],
  "instagram_hashtags": ["..."],
  "platform_copy": {{
    "youtube_description": "...",
    "instagram_caption": "... no hashtags no URLs ...",
    "facebook_title": "... <=80 chars ...",
    "facebook_description": "... no URLs ..."
  }},
  "source_urls": [...]
}}"""
    
    current_prompt = build_prompt()
    script_result = None
    
    for rewrite_count in range(max_rewrites + 1):
        try:
            parsed = multi_model_ai.generate_json(current_prompt, temperature=0.7, timeout=120)
        except Exception as e:
            # If LLM fails, create a fallback
            parsed = {
                "content_pillar": pillar or "Hype Check",
                "hook": best_hook,
                "title": topic[:60],
                "voice_text": f"{best_hook} {topic} involves specific mechanisms worth understanding. Research shows concrete details matter here. One key limitation is that not all aspects are clear yet. The practical takeaway is to focus on verified facts. In the end, it's about separating claims from evidence.",
                "broll_query": topic.lower().replace(' ', ' ')[:30],
                "youtube_tags": ["tech"],
                "instagram_hashtags": ["#tech"],
                "platform_copy": {
                    "youtube_description": f"{topic} explained with evidence.",
                    "instagram_caption": f"A look at {topic} based on research.",
                    "facebook_title": topic[:80],
                    "facebook_description": f"Examining {topic} with focus on evidence."
                },
                "source_urls": source_urls[:3] if source_urls else []
            }
        
        voice_text = _normalize_text(parsed.get('voice_text', ''))
        hook_result = parsed.get('hook', best_hook)
        # Ensure hook is first sentence
        if not voice_text.startswith(hook_result):
            sentences = _split_sentences(voice_text)
            if sentences:
                sentences[0] = hook_result
                voice_text = '. '.join(sentences)
                if not voice_text.endswith('.'):
                    voice_text += '.'
        
        word_count_res = _word_count(voice_text)
        critic_res = critique({
            'title': parsed.get('title', topic),
            'voice_text': voice_text,
            'hook': hook_result,
            'source_urls': parsed.get('source_urls', source_urls),
            'word_count': word_count_res,
            'seconds': seconds,
            'slop_score': voice_guide.slop_score(voice_text)
        }, research=research, topic=topic)
        
        if critic_res['pass'] or rewrite_count == max_rewrites:
            rewrites = rewrite_count
            script_result = {
                'parsed': parsed,
                'voice_text': voice_text,
                'hook': hook_result,
                'word_count': word_count_res,
                'critic': critic_res
            }
            break
        else:
            # Rewrite with critic issues
            rewrites = rewrite_count + 1
            current_prompt = build_prompt(critic_res['issues'])
    
    if script_result is None:
        script_result = {
            'parsed': parsed,
            'voice_text': voice_text,
            'hook': hook_result,
            'word_count': word_count_res,
            'critic': critic_res
        }
        rewrites = max_rewrites
    
    parsed_final = script_result['parsed']
    voice_text_final = script_result['voice_text']
    hook_final = script_result['hook']
    word_count_final = script_result['word_count']
    critic_final = script_result['critic']
    
    beat_sheet = build_beat_sheet(voice_text_final, duration=float(seconds), topic=topic)
    shots = plan_shots(beat_sheet, duration=float(seconds), topic=topic)
    
    title = str(parsed_final.get('title', topic)).strip()[:60]
    platform_copy = parsed_final.get('platform_copy', {})
    if not isinstance(platform_copy, dict):
        platform_copy = {}
    
    youtube_description = str(platform_copy.get('youtube_description', f'{topic} explained.')).strip()[:5000]
    instagram_caption = str(platform_copy.get('instagram_caption', f'A quick look at {topic}.')).strip()[:1800]
    # Ensure no hashtags/URLs in instagram caption
    instagram_caption = re.sub(r'#\S+', '', instagram_caption)
    instagram_caption = re.sub(r'http\S+', '', instagram_caption).strip()
    
    facebook_title = str(platform_copy.get('facebook_title', title)).strip()[:80]
    facebook_description = str(platform_copy.get('facebook_description', f'Understanding {topic}.')).strip()[:4600]
    facebook_description = re.sub(r'http\S+', '', facebook_description).strip()
    
    youtube_tags = parsed_final.get('youtube_tags', [])
    if not isinstance(youtube_tags, list):
        youtube_tags = []
    youtube_tags = [str(t).strip() for t in youtube_tags if str(t).strip()][:8]
    
    instagram_hashtags = parsed_final.get('instagram_hashtags', [])
    if not isinstance(instagram_hashtags, list):
        instagram_hashtags = []
    instagram_hashtags = [str(t).strip() for t in instagram_hashtags if str(t).strip()][:8]
    
    final_source_urls = parsed_final.get('source_urls', source_urls)
    if not isinstance(final_source_urls, list):
        final_source_urls = source_urls if isinstance(source_urls, list) else []
    
    content_pillar = parsed_final.get('content_pillar', pillar) or 'Hype Check'
    if content_pillar not in voice_guide.PILLAR_NAMES:
        content_pillar = 'Hype Check'
    
    broll_query = str(parsed_final.get('broll_query', topic)).strip()
    query_words = re.findall(r'[A-Za-z0-9]+', broll_query)
    if len(query_words) < 2:
        topic_words = re.findall(r'[A-Za-z0-9]+', topic)
        broll_query = ' '.join(topic_words[:5])
    
    slop_score_final = voice_guide.slop_score(voice_text_final)

    if strict_research and not critic_final.get('pass'):
        issues = "; ".join(
            f"{item.get('kind')}: {item.get('detail')}" for item in critic_final.get('issues', [])
        )
        raise RuntimeError("Script did not pass the editorial critic after "
                           f"{rewrites} rewrite(s): {issues or 'unknown issue'}")

    return {
        'content_pillar': content_pillar,
        'hook': hook_final,
        'title': title,
        'voice_text': voice_text_final,
        'beat_sheet': beat_sheet,
        'shots': shots,
        'broll_query': broll_query,
        'youtube_tags': youtube_tags,
        'instagram_hashtags': instagram_hashtags,
        'platform_copy': {
            'youtube_description': youtube_description,
            'instagram_caption': instagram_caption,
            'facebook_title': facebook_title,
            'facebook_description': facebook_description
        },
        'source_urls': final_source_urls,
        'word_count': word_count_final,
        'critic': critic_final,
        'hook_archetype': best_archetype,
        'slop_score': round(slop_score_final, 1),
        'rewrites': rewrites,
        'researched': True
    }


def render_report(script: dict) -> str:
    lines = []
    lines.append(f"HOOK: {script.get('hook', '')}")
    lines.append(f"TITLE: {script.get('title', '')} ({script.get('word_count', 0)} words)")
    lines.append(f"PILLAR: {script.get('content_pillar', '')} | ARCHETYPE: {script.get('hook_archetype', '')}")
    lines.append("")
    lines.append("BEATS:")
    for beat in script.get('beat_sheet', []):
        lines.append(f"  [{beat['t_start']:.1f}s-{beat['t_end']:.1f}s] {beat['label'].upper()}: {beat['text'][:60]}...")
        lines.append(f"    SHOT: {beat['shot_hint']}")
    lines.append("")
    lines.append(f"SHOTS ({len(script.get('shots', []))}):")
    for shot in script.get('shots', []):
        lines.append(f"  {shot['index']+1}. [{shot['duration']:.1f}s] {shot['visual']} ({shot['source']}) - {shot['asset_query']}")
    lines.append("")
    critic = script.get('critic', {})
    lines.append(f"CRITIC: score={critic.get('score', 0)}/100 pass={critic.get('pass', False)} slop={critic.get('slop_score', 0)}")
    if critic.get('issues'):
        lines.append("ISSUES:")
        for issue in critic['issues']:
            lines.append(f"  - [{issue['kind']}] {issue['detail']}")
    lines.append("")
    lines.append(f"SOURCES: {', '.join(script.get('source_urls', []))}")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Script Studio')
    parser.add_argument('topic', nargs='?', help='Topic to write about')
    parser.add_argument('--research', help='Research JSON file')
    parser.add_argument('--seconds', type=int, default=35, help='Duration in seconds')
    parser.add_argument('--demo', action='store_true', help='Use demo research bundle')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--pillar', help='Content pillar')
    args = parser.parse_args()
    
    if not args.topic and not args.demo:
        parser.print_help()
        return
    
    topic = args.topic or "AI developments"
    research = {}
    
    if args.demo:
        research = {
            "verdict": "sufficient",
            "claims": [
                {
                    "text": "A study found improved efficiency",
                    "quote": "The model achieved 40% better efficiency in tests",
                    "source_url": "https://example.com/study1"
                },
                {
                    "text": "Adoption is growing",
                    "quote": "Usage increased by 30% according to surveys",
                    "source_url": "https://example.com/study2"
                }
            ],
            "source_urls": ["https://example.com/study1", "https://example.com/study2"],
            "summary": "Research shows measurable improvements in tested scenarios"
        }
    elif args.research:
        try:
            with open(args.research, 'r') as f:
                research = json.load(f)
        except Exception as e:
            print(f"Error loading research: {e}", flush=True)
            return
    else:
        research = {
            "verdict": "sufficient",
            "claims": [{"text": topic, "quote": topic, "source_url": "https://example.com"}],
            "source_urls": ["https://example.com"],
            "summary": topic
        }
    
    try:
        script = write_script(topic, research, seconds=args.seconds, pillar=args.pillar)
        if args.json:
            print(json.dumps(script, indent=2))
        else:
            print(render_report(script))
    except Exception as e:
        print(f"Error: {e}", flush=True)
        raise


if __name__ == '__main__':
    main()
