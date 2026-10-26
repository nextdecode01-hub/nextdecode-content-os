#!/usr/bin/env python3
"""Editorial voice guide for the Nextdecode script studio.

This module is pure data plus rules: it never calls a language model and never
touches the network.  ``script_studio.py`` imports it to build every prompt and
to police the finished script.

What lives here
---------------
``CHANNEL``            the editorial identity of the channel.
``PILLARS``            the five repeatable series and what each one must contain.
``HOOK_ARCHETYPES``    twelve opening shapes with rules and examples.
``BANNED_PHRASES``     the AI-slop ban list, each entry explained.
``SLOP_PATTERNS``      compiled regexes built from that ban list.
``find_slop`` / ``slop_score``
                        the detector used by the critic loop and the CLI.

The ban list is intentionally about *how something is said*, never about the
subject matter.  A technical sentence such as "A 2024 paper found that the
model cuts memory use by roughly 40% on long-context tasks" scores 0.0.
"""

from __future__ import annotations

import math
import re

# ---------------------------------------------------------------------------
# Channel identity
# ---------------------------------------------------------------------------
CHANNEL = {
    "name": "Nextdecode",
    "audience": (
        "curious non-specialists who want practical, trustworthy AI and technology "
        "explanations"
    ),
    "tone": [
        "calm, plain-spoken, and confident",
        "curious without being breathless",
        "specific instead of sweeping",
        "honest about uncertainty",
        "peer-to-peer, never lecturing",
        "concrete, one idea at a time",
    ],
    "point_of_view": [
        "explain the mechanism before the opinion",
        "show the evidence, then say what it does not prove",
        "translate jargon into consequences for the viewer",
        "distinguish a published result from a shipped product",
        "prefer a measured number over an adjective",
        "give the viewer something they can actually do or check",
    ],
    "never": [
        "invent numbers, quotes, prices, availability, or demonstrations",
        "claim a result is revolutionary, viral, or guaranteed",
        "quote anonymous authority ('experts say') without naming the source",
        "ask for likes, subscribes, comments, or follows inside the spoken script",
        "open with a greeting, a channel name, or a generic announcement",
        "promise the viewer a future reveal they will not get",
        "hide a limitation the source makes obvious",
    ],
    "always": [
        "name a concrete source and say what it measured",
        "give at least one real number with its unit or context",
        "state one honest limitation of the evidence",
        "close with an action or a decision the viewer can make",
        "write spoken sentences that sound like a person talking",
        "keep every claim traceable to the supplied research",
    ],
    "voice_rules": [
        "Use short spoken sentences; one idea per sentence.",
        "Write numbers the way a person says them: 'about 40%', 'roughly 3 times'.",
        "Replace every adjective that could sit on any product with a measurable fact.",
        "Never use a banned phrase - the ban list is enforced programmatically.",
        "Never open with 'today we', 'in this video', 'welcome back', 'did you know', "
        "'let's talk about', or 'here's what you need to know'.",
        "Do not refer to 'this video' or 'the video' inside the spoken script or the captions.",
        "Keep the hook between 4 and 16 words, and copy it verbatim as the first spoken line.",
        "Use one idea per sentence and let the mechanism beat carry the explanation.",
        "Say the limitation out loud; do not bury it in a caption.",
        "End on the opening frame so the short loops cleanly.",
    ],
}

# ---------------------------------------------------------------------------
# Content pillars
# ---------------------------------------------------------------------------
PILLARS = {
    "AI You Can Use": {
        "description": "A concrete workflow or tool tip the viewer can try today.",
        "must_contain": [
            "the exact tool, feature, or setting",
            "the step the viewer performs",
            "what changes for them afterwards",
            "one limit, cost, or caveat",
        ],
        "avoid": ["tool lists without a workflow", "pricing claims that expire"],
    },
    "Hype Check": {
        "description": "Test a loud AI or tech claim against what the source actually proves.",
        "must_contain": [
            "the claim in the viewer's own words",
            "what the source actually measured",
            "the gap between marketing and evidence",
            "a verdict the viewer can act on",
        ],
        "avoid": ["mocking the source", "declaring a verdict without evidence"],
    },
    "What Changed": {
        "description": "Explain a genuinely recent launch, paper, or development and why it matters.",
        "must_contain": [
            "what changed, in one sentence",
            "when it changed",
            "who it affects",
            "what is still unproven",
        ],
        "avoid": ["recapping a launch that is not actually new"],
    },
    "How It Works": {
        "description": "Make one difficult technology understandable with a simple analogy.",
        "must_contain": [
            "the one mechanism being explained",
            "a physical or everyday analogy",
            "a number that anchors the scale",
            "where the analogy breaks down",
        ],
        "avoid": ["multiple analogies at once", "metaphors that hide the real mechanism"],
    },
    "Startup Breakdown": {
        "description": "Explain a real product, business model, or technical trade-off from evidence.",
        "must_contain": [
            "what the product actually does",
            "how it makes money or where it costs money",
            "the trade-off it makes",
            "one honest risk",
        ],
        "avoid": ["valuation gossip", "funding-round summaries with no product detail"],
    },
}

PILLAR_NAMES = tuple(PILLARS.keys())
# ---------------------------------------------------------------------------
# Hook archetypes
# ---------------------------------------------------------------------------
HOOK_ARCHETYPES = [
    {
        "id": "bold_claim",
        "name": "Bold claim",
        "description": "State a specific, defensible claim in the first eight words.",
        "example": "Quantization is not losing accuracy. It is losing the wrong precision.",
        "rules": [
            "The claim must be supported by the supplied research.",
            "Name what is being claimed in three words or fewer.",
            "Do not exceed what the source proves.",
        ],
    },
    {
        "id": "curiosity_gap",
        "name": "Curiosity gap",
        "description": "Open a specific question the viewer cannot answer without watching.",
        "example": "There is one number in this benchmark that nobody is quoting.",
        "rules": [
            "The gap must be closable inside the short.",
            "Ask about a detail, not about a topic.",
            "Never fake suspense about a reveal that never comes.",
        ],
    },
    {
        "id": "cold_open_result",
        "name": "Cold open on the result",
        "description": "Start on the outcome, then explain how it was reached.",
        "example": "It cut memory use by 40%. Then we found out why.",
        "rules": [
            "Lead with the measured outcome, not the setup.",
            "Keep the number and its unit in the first sentence.",
            "Do not repeat the number three times.",
        ],
    },
    {
        "id": "contrast",
        "name": "Contrast / what changed",
        "description": "Put the old state next to the new state.",
        "example": "A year ago this needed a research team. Now it is one setting.",
        "rules": [
            "Both sides of the contrast must be true.",
            "The change must be specific enough to picture.",
            "Avoid 'everything has changed' framing.",
        ],
    },
    {
        "id": "number",
        "name": "Leading number",
        "description": "Start with a number the viewer can hold in their head.",
        "example": "Thirty percent of the benchmark runs never touched a GPU.",
        "rules": [
            "Use one number, with its unit and its context.",
            "The number must come from the research.",
            "Do not use '10x' style multipliers.",
        ],
    },
    {
        "id": "question",
        "name": "Question the viewer cannot ignore",
        "description": "Ask a question that the viewer wants answered immediately.",
        "example": "Why does the same prompt give two different answers?",
        "rules": [
            "The question must have a concrete answer in the short.",
            "No rhetorical questions about the viewer's life.",
            "Do not ask a question the research cannot answer.",
        ],
    },
    {
        "id": "mistake",
        "name": "Call out a common mistake",
        "description": "Name a mistake the viewer is probably making.",
        "example": "You are benchmarking the prompt, not the model.",
        "rules": [
            "The mistake must be real and common.",
            "Explain the correct approach in the same short.",
            "No shaming, no 'everyone gets this wrong'.",
        ],
    },
    {
        "id": "contradiction",
        "name": "Name a contradiction",
        "description": "Point out that two credible sources disagree.",
        "example": "One paper says it scales. Another says it plateaus.",
        "rules": [
            "Both sides must come from the supplied research.",
            "Say what would settle it.",
            "Do not manufacture a disagreement that is not there.",
        ],
    },
    {
        "id": "consequence",
        "name": "Consequence for the viewer",
        "description": "Start from what this means for the person watching.",
        "example": "If this holds, your next model comparison is the wrong one.",
        "rules": [
            "Name the affected person or workflow.",
            "Stay concrete: time, money, effort, risk.",
            "Avoid fear-based urgency.",
        ],
    },
    {
        "id": "first_person",
        "name": "First-person discovery",
        "description": "Narrate something you actually tested or read.",
        "example": "I ran the same prompt on both models. The answers did not match.",
        "rules": [
            "Only claim what was really done.",
            "No fake experiments, no fake screenshots, no fake demos.",
            "Keep the personal part to one sentence.",
        ],
    },
    {
        "id": "pattern_interrupt",
        "name": "Pattern interrupt",
        "description": "Break the expected rhythm with a short, flat statement.",
        "example": "Stop. The interesting part of this paper is on page nine.",
        "rules": [
            "The interruption must be one clause.",
            "The line after it must immediately pay off the interruption.",
            "Never shout or use filler emphasis.",
        ],
    },
    {
        "id": "plain_language",
        "name": "Plain-language translation",
        "description": "Translate a technical phrase into ordinary words.",
        "example": "Context window is just how much the model can remember at once.",
        "rules": [
            "Name the technical term and translate it in the same sentence.",
            "Do not define more than one term per sentence.",
            "Avoid the phrase 'in plain English' in the hook itself.",
        ],
    },
]

ARCHETYPE_IDS = tuple(item["id"] for item in HOOK_ARCHETYPES)
# ---------------------------------------------------------------------------
# Banned phrases (AI slop)
# ---------------------------------------------------------------------------
BANNED_PHRASES: list[dict] = [
    {"phrase": "in today's fast-paced world", "kind": "cliche",
     "why": "A stock scene-setter that says nothing about the topic."},
    {"phrase": "in today's digital age", "kind": "cliche",
     "why": "Same stock opener; dates the script and adds no information."},
    {"phrase": "in today's world", "kind": "cliche",
     "why": "Tells the viewer nothing they did not already assume."},
    {"phrase": "in an era where", "kind": "cliche",
     "why": "Generic scene-setting that delays the actual point."},
    {"phrase": "in an increasingly", "kind": "cliche",
     "why": "Half a sentence of throat clearing."},
    {"phrase": "game-changer", "kind": "hype",
     "why": "Unfalsifiable hype word."},
    {"phrase": "game changer", "kind": "hype",
     "why": "Unfalsifiable hype word."},
    {"phrase": "game-changing", "kind": "hype",
     "why": "Unfalsifiable hype word."},
    {"phrase": "revolutionary", "kind": "hype",
     "why": "Claims a historical rupture the source does not support."},
    {"phrase": "revolutionize", "kind": "hype",
     "why": "Claims a historical rupture the source does not support."},
    {"phrase": "revolutionise", "kind": "hype",
     "why": "Claims a historical rupture the source does not support."},
    {"phrase": "world-changing", "kind": "hype",
     "why": "Unfalsifiable and almost always unearned."},
    {"phrase": "paradigm shift", "kind": "jargon",
     "why": "Business jargon used instead of saying what changed."},
    {"phrase": "let that sink in", "kind": "hype",
     "why": "Fake gravitas; asks the viewer to feel something instead of learn."},
    {"phrase": "buckle up", "kind": "cliche",
     "why": "Engagement bait with no content behind it."},
    {"phrase": "fasten your seatbelts", "kind": "cliche",
     "why": "Engagement bait with no content behind it."},
    {"phrase": "brace yourself", "kind": "cliche",
     "why": "Engagement bait with no content behind it."},
    {"phrase": "the future is here", "kind": "hype",
     "why": "The oldest AI cliche; says nothing checkable."},
    {"phrase": "the future of work", "kind": "hype",
     "why": "Cliche framing that avoids naming the actual change."},
    {"phrase": "unlock the power", "kind": "hype",
     "why": "Marketing language for a capability that needs a number."},
    {"phrase": "unleash", "kind": "hype",
     "why": "Marketing verb that hides the actual capability."},
    {"phrase": "harness the power", "kind": "hype",
     "why": "Marketing language for a capability that needs a number."},
    {"phrase": "supercharge", "kind": "hype",
     "why": "Marketing verb; replace with the measured effect."},
    {"phrase": "take to the next level", "kind": "hype",
     "why": "Says a change happened without saying what changed."},
    {"phrase": "groundbreaking", "kind": "hype",
     "why": "A judgement the source has not earned."},
    {"phrase": "bleeding edge", "kind": "hype",
     "why": "Marketing label for 'unstable'."},
    {"phrase": "best-in-class", "kind": "hype",
     "why": "Comparative claim with no comparison."},
    {"phrase": "life-changing", "kind": "hype",
     "why": "Unfalsifiable promise to the viewer."},
    {"phrase": "seamlessly", "kind": "filler",
     "why": "Nothing is seamless; name the step instead."},
    {"phrase": "effortlessly", "kind": "filler",
     "why": "Hides the work the viewer still has to do."},
    {"phrase": "frictionless", "kind": "hype",
     "why": "A setup always has friction; name it."},
    {"phrase": "cutting-edge", "kind": "hype",
     "why": "Marketing label; use the date or the measurement instead."},
    {"phrase": "ever-evolving", "kind": "cliche",
     "why": "Nothing is 'ever-evolving' in a way a viewer can act on."},
    {"phrase": "rapidly evolving", "kind": "cliche",
     "why": "Same cliche with a speed adverb attached."},
    {"phrase": "landscape of", "kind": "jargon",
     "why": "Business noun used where a plain description belongs."},
    {"phrase": "testament to", "kind": "cliche",
     "why": "Empty praise; name the thing that proves it."},
    {"phrase": "realm of", "kind": "jargon",
     "why": "Business noun used where a plain description belongs."},
    {"phrase": "tapestry", "kind": "jargon",
     "why": "Mixed metaphor that adds no information."},
    {"phrase": "navigate the complexities", "kind": "jargon",
     "why": "Says 'it is hard' without saying what is hard."},
    {"phrase": "delve into", "kind": "jargon",
     "why": "Pretend depth; say what is actually inside."},
    {"phrase": "leverage", "kind": "jargon",
     "why": "Corporate verb; use 'use' or name the benefit."},
    {"phrase": "synergy", "kind": "jargon",
     "why": "Corporate noun with no measurable referent."},
    {"phrase": "democratize", "kind": "hype",
     "why": "Claims an access change the source has not measured."},
    {"phrase": "double down", "kind": "jargon",
     "why": "Corporate verb; say what was actually increased."},
    {"phrase": "move the needle", "kind": "jargon",
     "why": "Corporate phrase; give the number instead."},
    {"phrase": "low-hanging fruit", "kind": "jargon",
     "why": "Corporate metaphor; name the task."},
    {"phrase": "secret sauce", "kind": "cliche",
     "why": "Hides the mechanism behind a pun."},
    {"phrase": "holy grail", "kind": "cliche",
     "why": "Borrowed hype for a problem that is not solved."},
    {"phrase": "disrupt", "kind": "hype",
     "why": "Borrowed hype; describe the actual change."},
    {"phrase": "disruptive", "kind": "hype",
     "why": "Borrowed hype; describe the actual change."},
    {"phrase": "mind-blowing", "kind": "hype",
     "why": "Reaction instead of information."},
    {"phrase": "mind blowing", "kind": "hype",
     "why": "Reaction instead of information."},
    {"phrase": "insane", "kind": "hype",
     "why": "Reaction instead of information."},
    {"phrase": "crazy good", "kind": "hype",
     "why": "Reaction instead of information."},
    {"phrase": "shocking", "kind": "hype",
     "why": "Reaction instead of information."},
    {"phrase": "you won't believe", "kind": "engagement_bait",
     "why": "Engagement bait; state the fact instead."},
    {"phrase": "wait for it", "kind": "engagement_bait",
     "why": "Engagement bait; state the fact instead."},
    {"phrase": "let me tell you", "kind": "filler",
     "why": "Throat clearing before the point."},
    {"phrase": "little did you know", "kind": "cliche",
     "why": "Patronising scene-setter."},
    {"phrase": "scientists say", "kind": "vague_authority",
     "why": "Anonymous authority; name the paper or the researcher."},
    {"phrase": "experts say", "kind": "vague_authority",
     "why": "Anonymous authority; name the source."},
    {"phrase": "studies show", "kind": "vague_authority",
     "why": "Anonymous authority; cite the actual study."},
    {"phrase": "research shows", "kind": "vague_authority",
     "why": "Anonymous authority; cite the actual study."},
    {"phrase": "thought leader", "kind": "vague_authority",
     "why": "Status claim instead of evidence."},    {"phrase": "AI is changing everything", "kind": "hype",
     "why": "Unfalsifiable and useless to the viewer."},
    {"phrase": "the possibilities are endless", "kind": "hype",
     "why": "Filler that promises nothing checkable."},
    {"phrase": "only time will tell", "kind": "hedge",
     "why": "Hedge used instead of stating what is actually known."},
    {"phrase": "we're just getting started", "kind": "cliche",
     "why": "Filler sign-off with no payoff."},
    {"phrase": "the sky's the limit", "kind": "cliche",
     "why": "Filler sign-off with no payoff."},
    {"phrase": "think outside the box", "kind": "cliche",
     "why": "Management cliche in a technology explainer."},
    {"phrase": "must-have", "kind": "hype",
     "why": "Review cliche; say what it does for the viewer."},
    {"phrase": "next-level", "kind": "hype",
     "why": "Unfalsifiable adjective."},
    {"phrase": "next level", "kind": "hype",
     "why": "Unfalsifiable adjective."},
    {"phrase": "eye-opening", "kind": "hype",
     "why": "Reaction instead of information."},
    {"phrase": "in conclusion", "kind": "structure",
     "why": "Signals a summary the viewer can already hear coming."},
    {"phrase": "moreover", "kind": "transition",
     "why": "Written-register connector; spoken scripts need none."},
    {"phrase": "furthermore", "kind": "transition",
     "why": "Written-register connector; spoken scripts need none."},
    {"phrase": "at the end of the day", "kind": "cliche",
     "why": "Filler that re-opens a point already closed."},
    {"phrase": "when it comes to", "kind": "filler",
     "why": "Filler preamble before every noun phrase."},
    {"phrase": "that's the thing", "kind": "filler",
     "why": "Filler emphasis; delete it."},
    {"phrase": "here's the thing", "kind": "filler",
     "why": "Filler emphasis; delete it."},
    {"phrase": "the bottom line is", "kind": "structure",
     "why": "Pre-announces the takeaway instead of stating it."},
    {"phrase": "needless to say", "kind": "filler",
     "why": "Filler preamble."},
    {"phrase": "it goes without saying", "kind": "filler",
     "why": "Filler preamble."},
    {"phrase": "it's worth noting that", "kind": "filler",
     "why": "Filler preamble; the point may not even be worth noting."},
    {"phrase": "it's important to note", "kind": "filler",
     "why": "Filler preamble."},
    {"phrase": "at its core", "kind": "filler",
     "why": "Filler preamble before every definition."},
    {"phrase": "ultimately", "kind": "filler",
     "why": "Filler adverb that hides which point is the point."},
    {"phrase": "in short", "kind": "transition",
     "why": "Announces a summary the viewer does not need."},
    {"phrase": "to sum up", "kind": "transition",
     "why": "Announces a summary the viewer does not need."},
    {"phrase": "that being said", "kind": "filler",
     "why": "Filler connector; just say the counterpoint."},
    {"phrase": "the key takeaway", "kind": "structure",
     "why": "Announces the takeaway instead of giving it."},
    {"phrase": "imagine a world where", "kind": "cliche",
     "why": "Hypothetical scene-setting that replaces a real fact."},
    {"phrase": "picture this", "kind": "cliche",
     "why": "Hypothetical scene-setting that replaces a real fact."},
    {"phrase": "one more thing", "kind": "filler",
     "why": "List filler inside a 35 second script."},
    {"phrase": "and that's a good thing", "kind": "filler",
     "why": "Reaction instead of information."},
    {"phrase": "the truth is", "kind": "filler",
     "why": "Pre-announces truth-telling the script then does not do."},
    {"phrase": "this changes everything", "kind": "hype",
     "why": "Unfalsifiable claim about scale."},
    {"phrase": "nobody is talking about this", "kind": "engagement_bait",
     "why": "Engagement bait built on an unverifiable claim."},
    {"phrase": "most people don't know", "kind": "engagement_bait",
     "why": "Engagement bait built on an unverifiable claim."},
    {"phrase": "here's what most people miss", "kind": "engagement_bait",
     "why": "Engagement bait built on an unverifiable claim."},
    {"phrase": "if that sounds too good to be true", "kind": "filler",
     "why": "Pre-emptive deflection; say the limitation directly."},
    {"phrase": "this video", "kind": "engagement_bait",
     "why": "Refers to the artefact instead of the topic."},
    {"phrase": "in this video", "kind": "engagement_bait",
     "why": "Refers to the artefact instead of the topic."},
    {"phrase": "in this short", "kind": "engagement_bait",
     "why": "Refers to the artefact instead of the topic."},
    {"phrase": "subscribe", "kind": "engagement_bait",
     "why": "Spoken engagement bait; the channel never asks for it."},
    {"phrase": "like and subscribe", "kind": "engagement_bait",
     "why": "Spoken engagement bait; the channel never asks for it."},
    {"phrase": "follow for more", "kind": "engagement_bait",
     "why": "Spoken engagement bait; the channel never asks for it."},
    {"phrase": "hit the bell", "kind": "engagement_bait",
     "why": "Spoken engagement bait; the channel never asks for it."},
    {"phrase": "comment below", "kind": "engagement_bait",
     "why": "Spoken engagement bait; the channel never asks for it."},
    {"phrase": "drop a comment", "kind": "engagement_bait",
     "why": "Spoken engagement bait; the channel never asks for it."},
    {"phrase": "smash that", "kind": "engagement_bait",
     "why": "Spoken engagement bait; the channel never asks for it."},
    {"phrase": "let's dive", "kind": "structure",
     "why": "Filler transition used instead of the actual point."},
    {"phrase": "let's dive in", "kind": "structure",
     "why": "Filler transition used instead of the actual point."},
    {"phrase": "dive in", "kind": "structure",
     "why": "Filler transition used instead of the actual point."},
    {"phrase": "let's unpack", "kind": "structure",
     "why": "Filler transition used instead of the actual point."},
    {"phrase": "let's get into", "kind": "structure",
     "why": "Filler transition used instead of the actual point."},
    {"phrase": "without further ado", "kind": "cliche",
     "why": "Stage-direction clutter in a spoken script."},
    {"phrase": "here's what you need to know", "kind": "cliche",
     "why": "Generic opening that promises the viewer nothing specific."},
    {"phrase": "the possibilities", "kind": "hype",
     "why": "Vague promise; name the capability instead."},
]

# Phrases that need a hand-written pattern instead of the auto-generated one.
CUSTOM_PATTERNS: dict[str, str] = {
    "it's not just X, it's Y": r"\bit'?s not just [^.!?]{1,80}, it'?s\b",
    "10x": r"\b10\s?x\b",
    "disrupt": r"\bdisrupt(?:ive|ed|ing|s)?\b",
    "leverage": r"\bleverage(?:d|s|ing)?\b",
    "synergy": r"\bsynerg(?:y|ies|istic|istically)\b",
}

# Severity weight per kind: how much a hit of this kind drags the slop score.
KIND_WEIGHTS = {
    "engagement_bait": 1.2,
    "hype": 1.1,
    "vague_authority": 1.1,
    "hype_number": 1.0,
    "cliche": 1.0,
    "structure": 0.9,
    "jargon": 0.8,
    "filler": 0.7,
    "transition": 0.6,
    "hedge": 0.7,
}
def _phrase_regex(phrase: str) -> str:
    """Build a tolerant regex for a literal phrase.

    Hyphens and spaces are interchangeable, apostrophes accept an optional
    curly variant, and a trailing plural is allowed so that "game changer"
    also catches "game changers".
    """
    tokens = [token for token in re.split(r"[\s\-]+", phrase.strip().lower()) if token]
    parts = []
    for token in tokens:
        escaped = re.escape(token)
        escaped = escaped.replace("\\'", "[']?")
        escaped = escaped.replace("'", "[']?")
        parts.append(escaped)
    body = r"[\s\-]+".join(parts)
    if body and body[-1].isalpha():
        body += "s?"
    return r"\b" + body + r"\b"


def _compile(entry: dict) -> dict:
    phrase = entry["phrase"]
    pattern = CUSTOM_PATTERNS.get(phrase)
    regex = re.compile(pattern, re.IGNORECASE) if pattern else re.compile(_phrase_regex(phrase), re.IGNORECASE)
    return {
        "phrase": phrase,
        "kind": entry.get("kind", "filler"),
        "why": entry.get("why", ""),
        "regex": regex,
    }


SLOP_PATTERNS: list[dict] = [_compile(entry) for entry in BANNED_PHRASES]

# ---------------------------------------------------------------------------
# Generic hook openers - create_short.py's six plus more
# ---------------------------------------------------------------------------
GENERIC_HOOK_PREFIXES = (
    "today we",
    "in this video",
    "welcome back",
    "did you know",
    "let's talk about",
    "here's what you need to know",
    "welcome to",
    "hello everyone",
    "hi everyone",
    "hey guys",
    "hello and welcome",
    "so today",
    "in today's",
    "in this short",
    "let's explore",
    "let's dive",
    "let me explain",
    "imagine a world",
    "picture this",
    "have you ever wondered",
    "have you ever thought",
    "what if i told you",
    "join me",
    "quick question",
    "quick thought",
)

# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------
def find_slop(text: str) -> list[dict]:
    """Return every banned phrase found in ``text``.

    Each finding is ``{"phrase", "kind", "why", "span"}`` where ``span`` is a
    ``(start, end)`` character offset into the original text.  Overlapping
    matches are collapsed so the longest phrase wins.
    """
    source = text or ""
    if not source.strip():
        return []
    found: list[dict] = []
    for pattern in SLOP_PATTERNS:
        for match in pattern["regex"].finditer(source):
            found.append(
                {
                    "phrase": pattern["phrase"],
                    "kind": pattern["kind"],
                    "why": pattern["why"],
                    "span": (match.start(), match.end()),
                    "matched": match.group(0),
                }
            )
    found.sort(key=lambda item: (item["span"][0], -(item["span"][1] - item["span"][0])))
    collapsed: list[dict] = []
    for item in found:
        if collapsed and item["span"][0] < collapsed[-1]["span"][1]:
            continue
        collapsed.append(item)
    collapsed.sort(key=lambda item: item["span"][0])
    return collapsed


def slop_score(text: str) -> float:
    """Score ``text`` from 0 (clean) to 100 (saturated with banned phrases)."""
    source = text or ""
    words = len(re.findall(r"[A-Za-z0-9']+", source))
    findings = find_slop(source)
    if not findings:
        return 0.0
    weighted = sum(KIND_WEIGHTS.get(item["kind"], 1.0) for item in findings)
    density = weighted / max(words, 10)
    score = 100.0 * (1.0 - math.exp(-10.0 * density))
    return round(min(100.0, max(0.0, score)), 1)


def banned_phrase_list() -> list[str]:
    """The literal banned phrases, in ban-list order."""
    return [entry["phrase"] for entry in BANNED_PHRASES]


def banned_phrases_by_kind() -> dict[str, list[str]]:
    """Group the ban list by kind so the report can summarise it."""
    grouped: dict[str, list[str]] = {}
    for entry in BANNED_PHRASES:
        grouped.setdefault(entry["kind"], []).append(entry["phrase"])
    return grouped


def is_generic_hook(hook: str) -> bool:
    """True when the hook opens with a generic, banned opener."""
    text = (hook or "").strip().lower()
    return bool(text) and text.startswith(GENERIC_HOOK_PREFIXES)


def archetype_by_id(archetype_id: str) -> dict | None:
    """Look up one archetype by id, or by (approximate) name."""
    key = (archetype_id or "").strip().lower()
    for item in HOOK_ARCHETYPES:
        if item["id"] == key:
            return item
    for item in HOOK_ARCHETYPES:
        if item["name"].lower() == key:
            return item
    return None


def archetype_ids() -> list[str]:
    """Every valid archetype id."""
    return list(ARCHETYPE_IDS)


def hook_instructions() -> str:
    """The hook rules block that is embedded in every script prompt."""
    lines = [
        "HOOK RULES",
        "- The hook is the first spoken sentence and it must be copied verbatim as the "
        "first characters of voice_text.",
        "- The hook is 4 to 16 words. Three words is too thin, more than 20 is too long.",
        "- The hook must not start with: "
        + ", ".join(f"'{item}'" for item in GENERIC_HOOK_PREFIXES[:12])
        + ".",
        "- The hook must not contain a banned phrase, and must not ask for likes, "
        "subscribes, comments or follows.",
        "- The hook must be true given the supplied research. No invented numbers, "
        "quotes, prices, availability or demonstrations.",
        "- The hook must name a specific thing: a number, a mechanism, a claim, a "
        "mistake, or a contradiction.",
        "- Do not greet the viewer, announce the channel, or describe the format.",
        "",
        "HOOK ARCHETYPES (use the id in the 'archetype' field)",
    ]
    for item in HOOK_ARCHETYPES:
        lines.append(f"- {item['id']}: {item['description']}")
        for rule in item["rules"]:
            lines.append(f"    * {rule}")
    return "\n".join(lines)
def voice_prompt_block(pillar: str | None = None) -> str:
    """The editorial block embedded in every script prompt."""
    pillar_key = (pillar or "").strip()
    lines = [
        f"CHANNEL: {CHANNEL['name']}",
        f"AUDIENCE: {CHANNEL['audience']}",
        "",
        "TONE",
    ]
    lines.extend(f"- {item}" for item in CHANNEL["tone"])
    lines.append("")
    lines.append("POINT OF VIEW")
    lines.extend(f"- {item}" for item in CHANNEL["point_of_view"])
    lines.append("")
    lines.append("NEVER")
    lines.extend(f"- {item}" for item in CHANNEL["never"])
    lines.append("")
    lines.append("ALWAYS")
    lines.extend(f"- {item}" for item in CHANNEL["always"])
    lines.append("")
    lines.append("WRITING RULES")
    lines.extend(f"- {item}" for item in CHANNEL["voice_rules"])
    lines.append("")
    lines.append("CONTENT PILLARS (pick exactly one, and only if the evidence fits)")
    for name, spec in PILLARS.items():
        marker = " <- required pillar" if name == pillar_key else ""
        lines.append(f"- {name}{marker}: {spec['description']}")
        lines.append("    must contain: " + "; ".join(spec["must_contain"]))
        lines.append("    avoid: " + "; ".join(spec["avoid"]))
    if pillar_key and pillar_key not in PILLARS:
        lines.append("")
        lines.append(f"NOTE: '{pillar_key}' is not a valid pillar; choose one of the five above.")
    lines.append("")
    lines.append(
        "BANNED PHRASES - never write any of these, in the script, the title, or any caption:"
    )
    for entry in BANNED_PHRASES:
        lines.append(f"- {entry['phrase']}  ({entry['kind']}: {entry['why']})")
    return "\n".join(lines)


def list_archetypes() -> None:
    """Print the hook archetype catalogue."""
    print(f"Nextdecode hook archetypes ({len(HOOK_ARCHETYPES)})")
    print("-" * 96)
    for item in HOOK_ARCHETYPES:
        print(f"{item['id']:<20} {item['name']}")
        print(f"{'':<20} {item['description']}")
        print(f"{'':<20} example: {item['example']}")
        for rule in item["rules"]:
            print(f"{'':<22}- {rule}")
        print("-" * 96)
    grouped = banned_phrases_by_kind()
    print(f"Banned phrases: {len(BANNED_PHRASES)} in {len(grouped)} kinds")
    for kind in sorted(grouped):
        print(f"  {kind:<18} {len(grouped[kind]):>3}")


def describe(text: str) -> dict:
    """Summary report used by the CLI."""
    findings = find_slop(text)
    return {
        "text": text,
        "score": slop_score(text),
        "findings": findings,
        "clean": not findings,
        "generic_hook": is_generic_hook(text),
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Nextdecode editorial voice guide")
    parser.add_argument("--slop", metavar="TEXT", help="Scan TEXT for banned phrases")
    parser.add_argument("--archetypes", action="store_true", help="List the hook archetypes")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    args = parser.parse_args()

    if args.archetypes or not args.slop:
        list_archetypes()
        if not args.slop:
            raise SystemExit(0)

    report = describe(args.slop)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Slop score: {report['score']}/100")
        if report["clean"]:
            print("No banned phrases found.")
        for item in report["findings"]:
            start, end = item["span"]
            print(f"- {item['matched']!r} [{item['kind']}] at {start}-{end}")
            print(f"    banned as: {item['phrase']}")
            print(f"    why: {item['why']}")