"""Channel-scoped editorial profile and content-format contract."""
from __future__ import annotations
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "config" / "channels" / "nextdecode.v1.json"

# The channel's six primary pillars, in editorial priority order. These are the
# rotation unit: consecutive videos should not sit on the same pillar when a
# comparably strong story exists on another one, but they always stay inside
# the niche.
PRIMARY_LANES = (
    "artificial_intelligence",
    "technology_innovation",
    "startups_entrepreneurship",
    "business_economics",
    "markets_industry_shifts",
    "future_trends",
)

# Explicit subject signals connect the existing broad taxonomy to this channel's
# audience promise. A broad label alone (e.g. history or geopolitics) is not enough.
# Lane ids mirror `config/channels/nextdecode.v1.json` so the config and the
# matcher cannot drift apart in naming.
RELATED_SIGNALS = {
    "artificial_intelligence": (
        "ai", "artificial intelligence", "machine learning", "deep learning",
        "neural", "neural network", "neural networks", "llm", "llms",
        "large language model", "large language models", "generative ai", "genai",
        "foundation model", "reasoning model", "ai model", "ai models",
        "model training", "model inference", "inference", "fine tuning",
        "alignment", "hallucination", "prompt", "prompts", "prompting",
        "agent", "agents", "agentic", "ai agent", "ai agents",
        "openai", "anthropic", "deepmind", "chatgpt", "gpt", "gpt 4", "gpt 5",
        "claude", "gemini", "llama", "mistral", "deepseek", "qwen", "grok",
        "copilot", "perplexity", "hugging face", "transformer", "transformers",
        "diffusion model", "dataset", "datasets", "synthetic data", "benchmark",
        "agi", "superintelligence", "ai safety", "ai regulation",
        "computer vision", "natural language processing", "nlp",
    ),
    "technology_innovation": (
        "technology", "tech", "innovation", "innovative", "software", "hardware",
        "computer", "computing", "algorithm", "algorithms", "app", "apps",
        "digital", "automation", "automate", "automated", "platform", "platforms",
        "engineering", "engineer", "prototype", "patent", "r d",
        "research and development", "breakthrough", "gadget", "device", "devices",
        "silicon", "open source", "github", "api", "sdk", "operating system",
        "linux", "browser", "search engine", "developer", "developers",
        "programming", "coding", "code", "data center", "data centre", "datacenter",
    ),
    "startups_entrepreneurship": (
        "startup", "startups", "founder", "founders", "co founder",
        "entrepreneur", "entrepreneurs", "entrepreneurship", "venture capital",
        "vc", "seed round", "series a", "series b", "funding round", "valuation",
        "unicorn", "bootstrapped", "accelerator", "incubator", "pitch deck",
        "product market fit", "saas", "y combinator",
    ),
    "business_economics": (
        "business", "businesses", "company", "companies", "corporate",
        "corporation", "economy", "economic", "economics", "gdp", "inflation",
        "interest rate", "interest rates", "recession", "revenue", "profit",
        "profits", "earnings", "margin", "supply chain", "supply chains", "trade",
        "tariff", "tariffs", "labor market", "labour market", "jobs report",
        "consumer spending", "pricing", "monopoly", "antitrust", "competition",
    ),
    "markets_industry_shifts": (
        "market", "markets", "stock", "stocks", "stock market", "share price",
        "ipo", "merger", "acquisition", "buyout", "industry", "industries",
        "sector", "manufacturing", "factory", "factories", "production", "output",
        "demand", "shortage", "oversupply", "commodity", "oil price", "shipping",
        "freight", "logistics", "layoffs", "restructuring", "market share",
    ),
    "future_trends": (
        "future of", "future tech", "emerging technology", "emerging technologies",
        "next generation", "next gen", "2030", "2040", "2050", "long term",
        "megatrend", "foresight", "scenario planning", "climate tech",
        "space economy", "digital transformation", "automation economy",
        "post work", "singularity", "moonshot",
    ),
    "semiconductors_computing": (
        "semiconductor", "semiconductors", "chip", "chips", "microchip", "gpu",
        "gpus", "tpu", "nvidia", "amd", "intel", "tsmc", "arm", "lithography",
        "fab", "foundry", "wafer", "compute", "supercomputer",
    ),
    "robotics_automation": (
        "robot", "robots", "robotics", "humanoid", "humanoids", "drone", "drones",
        "autonomous", "self driving", "driverless", "robotaxi",
        "industrial automation", "cobot",
    ),
    "cybersecurity_digital_privacy": (
        "cybersecurity", "cyber attack", "cyberattack", "hacking", "hacker",
        "malware", "ransomware", "breach", "data breach", "vulnerability",
        "exploit", "encryption", "privacy", "surveillance", "zero trust",
        "phishing", "deepfake",
    ),
    "internet_platforms_digital_economy": (
        "social media", "social platform", "social platforms", "platform economy",
        "creator economy", "e commerce", "ecommerce", "marketplace",
        "online advertising", "advertising technology", "streaming",
        "subscription", "app store", "digital economy",
    ),
    "venture_capital_funding": (
        "venture capital", "funding", "investor", "investors", "investment",
        "investments", "seed funding", "term sheet", "fundraise", "fundraising",
        "capital raise", "angel investor",
    ),
    "corporate_strategy_competition": (
        "strategy", "acquisition", "merger", "partnership", "joint venture",
        "market share", "competitor", "competitors", "competition", "monopoly",
        "antitrust", "spin off", "spinoff", "restructuring",
    ),
    "global_trade_supply_chains": (
        "trade", "tariff", "tariffs", "export", "exports", "import", "imports",
        "supply chain", "supply chains", "shipping", "freight", "port", "logistics",
        "rare earth", "rare earths", "critical minerals", "export control",
        "customs",
    ),
    "energy_batteries_electric_mobility": (
        "energy", "battery", "batteries", "electric vehicle", "electric vehicles",
        "ev", "evs", "charging", "grid", "solar", "wind power", "nuclear",
        "fusion", "hydrogen", "oil", "gas", "renewable", "renewables",
    ),
    "digital_infrastructure_cloud_data_centres": (
        "cloud", "data center", "data centre", "datacenter", "data centres",
        "data centers", "server", "servers", "infrastructure", "network",
        "networks", "broadband", "5g", "6g", "fiber", "fibre", "edge computing",
        "kubernetes",
    ),
    "biotechnology_commercial_innovation": (
        "biotech", "biotechnology", "genomics", "gene editing", "crispr",
        "drug discovery", "pharma", "pharmaceutical", "clinical trial",
        "clinical trials", "medtech", "medical technology", "synthetic biology",
    ),
    "science_to_market_breakthroughs": (
        "commercialization", "commercialisation", "breakthrough", "laboratory",
        "lab", "research paper", "peer reviewed", "patent", "prototype",
        "proof of concept", "technology transfer",
    ),
    "work_future_productivity": (
        "future of work", "remote work", "hybrid work", "productivity",
        "workforce", "automation economy", "reskilling", "upskilling",
        "gig economy", "four day week", "labor", "talent",
    ),
    "technology_policy_regulation": (
        "regulation", "regulatory", "policy", "legislation", "antitrust",
        "export control", "data protection", "gdpr", "ai act",
        "digital sovereignty", "net neutrality", "content moderation", "copyright",
    ),
    "industry_geopolitics": (
        "geopolitics", "export control", "chip war", "technology war", "tech war",
        "digital sovereignty", "industrial policy", "sanctions",
        "national security", "strategic competition",
    ),
    "consumer_technology_products": (
        "consumer technology", "smartphone", "smartphones", "laptop", "wearable",
        "wearables", "gadget", "gadgets", "device", "devices", "product launch",
        "consumer electronics",
    ),
}

@lru_cache(maxsize=1)
def load_channel_profile() -> dict:
    with PROFILE_PATH.open(encoding="utf-8") as handle:
        profile = json.load(handle)
    if profile.get("schema") != "nextdecode.channel-profile.v1":
        raise ValueError("Unsupported channel profile schema")
    return profile

def _has_signal(text: str, signals: tuple[str, ...]) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    for signal in signals:
        phrase = re.sub(r"[^a-z0-9]+", " ", signal.lower()).strip()
        if re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", normalized):
            return True
    return False

def matched_editorial_lanes(title: str, summary: str = "") -> list[str]:
    """Every niche lane whose explicit signals appear in the topic text."""
    text = f"{title} {summary}"
    return [lane for lane, signals in RELATED_SIGNALS.items() if _has_signal(text, signals)]

def primary_niche_lane(title: str, summary: str = "") -> str:
    """The rotation unit: first matched primary pillar, or "" when off-niche."""
    lanes = matched_editorial_lanes(title, summary)
    for lane in PRIMARY_LANES:
        if lane in lanes:
            return lane
    return ""

def channel_topic_relevance(title: str, summary: str = "", category: str = "general_curiosity") -> dict:
    """Return an explainable eligibility decision for the active channel only."""
    profile = load_channel_profile()
    matches = matched_editorial_lanes(title, summary)
    return {
        "eligible": bool(matches),
        "channel_id": profile["channel_id"],
        "topic_category": category,
        "matched_editorial_lanes": matches,
        "primary_niche_lane": primary_niche_lane(title, summary),
        "reason": ("topic connects to the NEXTDECODE technology/business/future audience promise" if matches
                   else "topic does not yet demonstrate a direct connection to NEXTDECODE's channel promise; retain for manual editorial review"),
    }

def enabled_content_formats() -> list[str]:
    return list(load_channel_profile().get("content_formats", {}).get("enabled", []))
