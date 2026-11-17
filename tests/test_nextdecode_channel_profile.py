from app.research.channel_profile import channel_topic_relevance, enabled_content_formats, load_channel_profile
from app.research.selector import niche_relevance


def test_active_channel_profile_has_focused_editorial_promise():
    profile = load_channel_profile()
    assert profile["channel_id"] == "nextdecode"
    assert "artificial_intelligence" in profile["editorial_niche"]["primary"]
    assert "energy_batteries_electric_mobility" in profile["editorial_niche"]["related"]
    assert profile["editorial_rules"]["evidence_required"] is True


def test_nextdecode_accepts_primary_and_adjacent_business_technology_topics():
    for title, summary in [
        ("How AI Agents Are Changing Software Work", "Artificial intelligence and automation"),
        ("Why Semiconductor Supply Chains Matter", "Chips, industry and global trade"),
        ("How a Startup Raised Venture Capital", "Founders, funding and business"),
        ("The Economics of Electric Vehicle Batteries", "Energy transition and industry"),
        ("How Cloud Data Centres Power the Internet", "Digital infrastructure"),
        ("How Social Platforms Make Money", "Digital economy and advertising"),
    ]:
        assert niche_relevance({"title": title, "summary": summary})["eligible"], title


def test_nextdecode_rejects_unrelated_topics_for_manual_review():
    for title in [
        "The Lost Tomb of an Ancient King",
        "Rare Birds Return to the Rainforest",
        "The Greatest Football Final in History",
        "A Celebrity's Private Life",
    ]:
        result = niche_relevance({"title": title})
        assert result["eligible"] is False, (title, result)
        assert "manual editorial review" in result["reason"]


def test_all_requested_content_formats_are_enabled_without_auto_publish():
    formats = enabled_content_formats()
    assert "youtube_longform" in formats
    assert "youtube_shorts" in formats
    assert "instagram_reels" in formats
    assert "instagram_carousels" in formats
    assert "youtube_community_posts" in formats
    assert load_channel_profile()["publishing"]["automatic_public_publishing"] is False
