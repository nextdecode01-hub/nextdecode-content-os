from unittest.mock import patch

from app.visuals import visual_assets


def test_visual_provider_is_preferred_but_does_not_disable_fallbacks():
    visual_assets._PROVIDER_COOLDOWN.clear()
    with patch.dict("os.environ", {"NEXTDECODE_FREE_VISUALS_ONLY": "0"}), patch.object(
        visual_assets, "VISUAL_PROVIDER", "gemini"
    ), patch.object(visual_assets, "IMAGE_PROVIDER", "pollinations"), patch.object(
        visual_assets,
        "available_providers",
        return_value=["pollinations", "gemini", "cloudflare", "local"],
    ):
        chain = visual_assets._chain()

    assert chain[:3] == ["gemini", "pollinations", "cloudflare"]
    assert chain[-1] == "local"


def test_explicit_provider_argument_remains_a_strict_override():
    with patch.dict("os.environ", {"NEXTDECODE_FREE_VISUALS_ONLY": "0"}), patch.object(
        visual_assets,
        "available_providers",
        return_value=["pollinations", "gemini", "local"],
    ):
        assert visual_assets._chain("gemini") == ["gemini"]


def test_preferred_provider_in_cooldown_is_skipped_for_fallback():
    visual_assets._PROVIDER_COOLDOWN.clear()
    visual_assets._cool_down("gemini", "HTTP 429 rate limited")
    with patch.dict("os.environ", {"NEXTDECODE_FREE_VISUALS_ONLY": "0"}), patch.object(
        visual_assets, "VISUAL_PROVIDER", "gemini"
    ), patch.object(
        visual_assets,
        "available_providers",
        return_value=["pollinations", "gemini", "local"],
    ):
        chain = visual_assets._chain()
    assert chain[0] == "pollinations"
    assert "gemini" not in chain
    visual_assets._PROVIDER_COOLDOWN.clear()


def test_free_only_visual_policy_excludes_all_metered_providers():
    visual_assets._PROVIDER_COOLDOWN.clear()
    with patch.dict("os.environ", {"NEXTDECODE_FREE_VISUALS_ONLY": "1"}), patch.object(
        visual_assets, "VISUAL_PROVIDER", "wikimedia"
    ), patch.object(visual_assets, "IMAGE_PROVIDER", "gemini"):
        assert visual_assets._chain() == ["wikimedia", "local"]
        assert visual_assets._chain("gemini") == []
        assert visual_assets._chain("wikimedia") == ["wikimedia"]

def test_free_only_policy_never_uses_pollinations_after_keyless_402(monkeypatch):
    monkeypatch.setenv("NEXTDECODE_FREE_VISUALS_ONLY", "1")
    monkeypatch.setenv("POLLINATIONS_ENABLED", "true")
    monkeypatch.setenv("VISUAL_PROVIDER", "pollinations")
    monkeypatch.setattr(visual_assets, "POLLINATIONS_KEY", "")
    assert visual_assets._chain() == ["wikimedia", "local"]
    assert visual_assets._chain("pollinations") == []
