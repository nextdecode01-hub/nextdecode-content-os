from __future__ import annotations

import pytest

from app.script.short import trim_voiceover_at_sentence_boundary


def test_trim_voiceover_removes_whole_trailing_sentences_and_keeps_profile():
    first = "Hook " + "clear " * 38 + "."
    middle = "Next " + "useful " * 69 + "."
    final = "Finally " + "payoff " * 49 + "."
    original = " ".join((first, middle, final))
    trimmed, changed = trim_voiceover_at_sentence_boundary(original, 92, 118)
    assert changed is True
    assert trimmed.startswith("Hook ")
    assert "Finally" not in trimmed
    assert 92 <= len(trimmed.split()) <= 118


def test_trim_voiceover_does_not_change_already_valid_script():
    text = "A concise script with enough words to stay comfortably within its target length."
    result, changed = trim_voiceover_at_sentence_boundary(text, 5, 20)
    assert result == text
    assert changed is False


def test_trim_voiceover_fails_closed_when_only_sentence_exceeds_maximum():
    text = " ".join(["word"] * 174) + "."
    with pytest.raises(RuntimeError, match="sentence boundaries"):
        trim_voiceover_at_sentence_boundary(text, 92, 118)
