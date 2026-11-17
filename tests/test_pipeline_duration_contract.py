from __future__ import annotations

import pytest

from app.script.short import SCRIPT_PROFILES as SHORT_SCRIPT_PROFILES
from app.script.studio import SCRIPT_PROFILES as STUDIO_SCRIPT_PROFILES
from app.publish.orchestration import SCRIPT_RANGES
from app.script.pipeline import (
    MAX_SHORT_DURATION_SECONDS,
    MIN_SHORT_DURATION_SECONDS,
    trim_script_for_measured_duration,
    validate_render_sync,
    validate_short_duration,
)


def test_short_duration_contract_accepts_inclusive_boundaries():
    validate_short_duration(MIN_SHORT_DURATION_SECONDS)
    validate_short_duration(MAX_SHORT_DURATION_SECONDS)

def test_candidate_urls_prioritize_primary_moe_sources():
    import app.script.pipeline as pipeline

    urls = pipeline._candidate_urls(
        {"topic": "How AI Models Activate a Few Experts to Save Compute"},
        [{"url": "https://random-blog.example/moe"}],
    )
    assert "https://mistral.ai/news/mixtral-of-experts/" in urls
    assert "https://huggingface.co/blog/mixtral" in urls
    assert "https://arxiv.org/abs/2401.04088" in urls


def test_script_research_bundle_filters_to_supported_primary_claims(monkeypatch):
    import app.script.pipeline as pipeline

    ledger = {"claims": [
        {"verification": {"status": "supported"}, "decision": "include",
         "source_url": "https://mistral.ai/news/mixtral-of-experts/", "narration": "Mixtral routes each token to two experts."},
        {"verification": {"status": "partially_supported"}, "decision": "qualify",
         "source_url": "https://agent5.news/moe", "narration": "MoE always reduces costs."},
        {"verification": {"status": "supported"}, "decision": "include",
         "source_url": "https://random-blog.example/moe", "narration": "A random claim."},
    ]}
    monkeypatch.setattr(pipeline.claims_ledger, "build_ledger", lambda *_args, **_kwargs: ledger)
    bundle = pipeline._script_research_bundle({
        "topic": "How mixture-of-experts models route tokens",
        "claims": [],
        "sources": [
            {"url": "https://mistral.ai/news/mixtral-of-experts/", "text": "Mixtral routes each token to two experts."},
            {"url": "https://agent5.news/moe", "text": "MoE always reduces costs."},
            {"url": "https://random-blog.example/moe", "text": "A random claim."},
        ],
        "source_urls": ["https://agent5.news/moe"],
        "summary": "noisy raw research summary",
    })
    assert len(bundle["claims"]) == 1
    assert bundle["claims"][0]["source_url"].startswith("https://mistral.ai/")
    assert bundle["source_urls"] == ["https://mistral.ai/news/mixtral-of-experts/"]
    assert "noisy raw research summary" not in bundle["summary"]


def test_script_evidence_gate_blocks_unsupported_and_unqualified_claims():
    from app.script.pipeline import _script_evidence_issues

    ledger = {
        "script_mapping": {
            "flags": [
                {"flag": "unqualified_partially_supported", "sentence": "The router always selects two experts.", "detail": "single-source support"},
                {"flag": "unsupported_factual", "sentence": "DeepSeek uses 37 billion active parameters.", "detail": "no mapped claim"},
            ],
            "unmapped": ["DeepSeek uses 37 billion active parameters."],
        }
    }
    issues = _script_evidence_issues(ledger)
    assert any("unqualified_partially_supported" in issue for issue in issues)
    assert any("unsupported_factual" in issue for issue in issues)
    assert len(issues) == 2


def test_evidence_checked_script_requests_rewrite_and_rechecks_ledger(tmp_path, monkeypatch):
    import app.script.pipeline as pipeline

    bad = {"script_mapping": {"flags": [
        {"flag": "unsupported_factual", "sentence": "A model uses 37 billion active parameters.", "detail": "no source"}
    ], "unmapped": ["A model uses 37 billion active parameters."]}}
    good = {"script_mapping": {"flags": [], "unmapped": []}}
    # Supply the two deterministic ledger results explicitly.
    ledgers = iter([bad, good])
    monkeypatch.setattr(pipeline.claims_ledger, "build_ledger", lambda *_args, **_kwargs: next(ledgers))
    monkeypatch.setattr(pipeline.claims_ledger, "write_ledger", lambda _ledger, _path: tmp_path / "claim_ledger.json")
    seen = {}
    def rewrite(*_args, **kwargs):
        seen["constraints"] = kwargs.get("additional_constraints")
        return {"title": "Grounded script", "voice_text": "Why does this model route each token to selected experts?", "critic": {"pass": True}}
    monkeypatch.setattr(pipeline.script_studio, "write_script", rewrite)

    script, ledger, path = pipeline._build_evidence_checked_script(
        "Mixture of Experts", {"claims": [{"quote": "router selects experts"}]},
        {"claims": [{"quote": "router selects experts"}]},
        {"voice_text": "A model uses 37 billion active parameters."}, 45, tmp_path,
    )
    assert script["title"] == "Grounded script"
    assert ledger is good
    assert path.name == "claim_ledger.json"
    assert any("37 billion" in issue for issue in seen["constraints"])


def test_generate_voice_honors_configured_free_first_provider(tmp_path, monkeypatch):
    import app.script.pipeline as pipeline

    captured = {}
    monkeypatch.setenv("TTS_PROVIDER", "kokoro_local")
    monkeypatch.setattr(
        pipeline.voice_provider, "synthesize_with_fallback",
        lambda _text, path, *, preferred, voice=None: (
            captured.update({"preferred": preferred}) or {"path": str(path), "provider": preferred}
        ),
    )
    monkeypatch.setattr(pipeline.voice_provider, "probe_audio_format", lambda _path: {"codec": "mp3"})
    monkeypatch.setattr(pipeline.voice_provider, "to_wav_master", lambda *_args, **_kwargs: None)
    result = pipeline.generate_voice("A short narration.", tmp_path / "voice.mp3")
    assert captured["preferred"] == "kokoro_local"
    assert result["provider"] == "kokoro_local"


@pytest.mark.parametrize("duration", [44.13, 63.86, 60.01])
def test_short_duration_contract_rejects_out_of_range_audio(duration):
    with pytest.raises(RuntimeError, match="outside the 45-60s Shorts contract"):
        validate_short_duration(duration)


def test_overlong_script_is_trimmed_only_at_complete_sentence_boundaries():
    sentences = [f"Sentence {index} contains several useful spoken words for viewers." for index in range(1, 21)]
    script = {"voice_text": " ".join(sentences), "word_count": 200}

    changed = trim_script_for_measured_duration(script, 63.86)

    assert changed is True
    assert script["voice_text"].endswith(".")
    assert "Sentence 20" not in script["voice_text"]
    assert script["word_count"] == len(script["voice_text"].split())
    assert script["word_count"] < 200


def test_in_range_script_is_not_changed():
    original = "First sentence is complete. Second sentence is also complete."
    script = {"voice_text": original, "word_count": len(original.split())}

    assert trim_script_for_measured_duration(script, 58.0) is False
    assert script["voice_text"] == original


def test_single_sentence_that_cannot_be_safely_trimmed_fails_closed():
    script = {"voice_text": " ".join(["word"] * 180) + ".", "word_count": 180}
    with pytest.raises(RuntimeError, match="sentence boundaries"):
        trim_script_for_measured_duration(script, 63.86)


def test_render_duration_must_match_narration():
    validate_render_sync(58.2, 58.0)
    with pytest.raises(RuntimeError, match="differs from narration"):
        validate_render_sync(59.0, 58.0)
    with pytest.raises(RuntimeError, match="outside the 45-60s Shorts contract"):
        validate_render_sync(44.13, 44.13)


def test_deep_60s_word_budget_is_consistent_across_script_and_publish_gates():
    expected = (170, 210)
    assert (SHORT_SCRIPT_PROFILES["deep_60s"]["min_words"], SHORT_SCRIPT_PROFILES["deep_60s"]["max_words"]) == expected
    assert (STUDIO_SCRIPT_PROFILES["deep_60s"]["min_words"], STUDIO_SCRIPT_PROFILES["deep_60s"]["max_words"]) == expected
    assert SCRIPT_RANGES["deep_60s"] == expected


def test_caption_builder_rejects_asr_that_covers_only_a_truncated_narration(tmp_path, monkeypatch):
    import app.script.pipeline as pipeline

    script_text = " ".join(f"word{index}" for index in range(100))
    monkeypatch.setattr(pipeline, "transcribe_words", lambda _path: [
        {"word": f"word{index}", "start": index * 0.4, "end": index * 0.4 + 0.3}
        for index in range(76)
    ])
    with pytest.raises(RuntimeError, match="ASR coverage too low"):
        pipeline.build_captions({"voice_text": script_text}, tmp_path / "voice.wav", tmp_path / "captions.ass", 50.0)


def test_caption_builder_falls_back_to_bounded_estimated_timings_when_alignment_overruns(tmp_path, monkeypatch):
    import app.script.pipeline as pipeline
    import app.render.subtitles as subtitles

    script_text = " ".join(f"word{index}" for index in range(100))
    monkeypatch.setattr(pipeline, "transcribe_words", lambda _path: [
        {"word": f"word{index}", "start": index * 0.45, "end": index * 0.45 + 0.3}
        for index in range(95)
    ])
    monkeypatch.setattr(subtitles, "align_script_to_asr", lambda _text, _words: [
        {"word": f"word{index}", "start": index * 0.6, "end": index * 0.6 + 0.4}
        for index in range(100)
    ])
    monkeypatch.setattr(pipeline, "make_kinetic_ass", lambda _words, _path: None)

    result = pipeline.build_captions(
        {"voice_text": script_text}, tmp_path / "voice.wav", tmp_path / "captions.ass", 50.0
    )
    payload = __import__("json").loads((tmp_path / "captions.words.json").read_text())
    assert result["timing_source"] == "estimated_alignment_fallback"
    assert payload["word_count"] == 100
    assert payload["words"][-1]["end"] == pytest.approx(50.0)


def test_verified_moe_template_recovers_a_supported_45_second_script():
    from app.script.studio import build_verified_moe_script

    research = {
        "topic": "How AI Models Activate a Few Experts to Save Compute",
        "source_urls": [
            "https://mistral.ai/news/mixtral-of-experts/",
            "https://huggingface.co/blog/mixtral",
        ],
        "claims": [
            {
                "decision": "include",
                "verification": {"status": "supported"},
                "source_url": "https://mistral.ai/news/mixtral-of-experts/",
                "claim": "Mixtral is a sparse mixture-of-experts model.",
                "quote": "Mixtral is a sparse mixture-of-experts model.",
            },
            {
                "decision": "include",
                "verification": {"status": "supported"},
                "source_url": "https://huggingface.co/blog/mixtral",
                "claim": "A router selects two experts for each token.",
                "quote": "A router selects two experts for each token.",
            },
            {
                "decision": "include",
                "verification": {"status": "supported"},
                "source_url": "https://mistral.ai/news/mixtral-of-experts/",
                "claim": "The router selects two experts at every layer.",
                "quote": "The router selects two experts at every layer.",
            },
        ],
    }
    script = build_verified_moe_script(
        research, seconds=45,
        topic="How AI Models Activate a Few Experts to Save Compute",
    )
    assert script is not None
    assert 92 <= script["word_count"] <= 118
    assert script["critic"]["pass"] is True


def test_pipeline_prefers_verified_moe_template_before_model_writer(monkeypatch):
    import app.script.pipeline as pipeline

    bundle = {"claims": [{"quote": "supported"}], "source_urls": []}
    monkeypatch.setattr(pipeline, "_script_research_bundle", lambda _research: bundle)
    monkeypatch.setattr(
        pipeline.script_studio,
        "build_verified_moe_script",
        lambda _bundle, **_kwargs: {"word_count": 100, "critic": {"pass": True}},
    )
    monkeypatch.setattr(
        pipeline.script_studio,
        "_review_script_editorial_quality",
        lambda *_args, **_kwargs: {
            "pass": True, "score": 88, "dimensions": {
                "hook": 4, "clarity": 4, "specificity": 4,
                "narrative_progression": 4, "insight": 4,
                "retention": 4, "evidence_alignment": 4,
            }, "issues": [], "rewrite_instructions": [],
        },
    )
    monkeypatch.setattr(
        pipeline.script_studio,
        "write_script",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("model writer should not run")),
    )
    result = pipeline._draft_script(
        "How AI Models Activate a Few Experts to Save Compute", {"claims": []}, 45
    )
    assert result["script_generation_path"] == "verified_moe_template"


def test_pipeline_script_normalization_repairs_question_and_possessive_boundaries():
    import app.script.pipeline as pipeline

    script = {"voice_text": "Google DeepMind?s tool helps. Is it research?or automation?"}
    normalized = pipeline._normalize_script_punctuation(script)
    assert normalized["voice_text"] == "Google DeepMind's tool helps. Is it research? or automation?"
    assert normalized["word_count"] == len(normalized["voice_text"].split())

def test_evidence_bounded_script_fallback_rejects_unverified_single_source_claims():
    from app.script.pipeline import _evidence_bounded_fallback_script

    claims = [
        ("The Intel 8085 is an eight-bit microprocessor designed for control-oriented computing applications.", "https://intel.example/8085"),
        ("Its instruction set includes arithmetic, logic, data transfer, and machine-control operations.", "https://manuals.example/8085"),
        ("The processor communicates with memory and input-output devices through defined address and data signals.", "https://university.example/8085"),
        ("Interrupts allow external events to request attention while the processor is executing a program.", "https://textbook.example/8085"),
        ("The system uses a clock signal to coordinate the timing of internal operations.", "https://engineering.example/8085"),
    ]
    research = {
        "verdict": "sufficient",
        "claims": [
            {"claim": sentence, "quote": sentence, "source_url": url}
            for sentence, url in claims
        ],
        "sources": [{"url": url, "text": sentence} for sentence, url in claims],
    }
    with pytest.raises(RuntimeError, match="at least three independently supported claims"):
        _evidence_bounded_fallback_script("Simple 8085 Computer", research, 45)
