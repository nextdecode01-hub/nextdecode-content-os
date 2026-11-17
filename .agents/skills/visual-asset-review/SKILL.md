---
name: visual-asset-review
description: Review scene-to-asset relevance, rights, provenance and visual quality for NEXTDECODE Shorts.
---

# Visual Asset Review

Review the narration beat and scene brief, not only the search query. Inspect the actual image/video frame. Keyword overlap is discovery evidence, never semantic approval.

Return high, medium, low or unchecked with a concise reason and provider/model provenance. Reject low relevance and continue through the existing provider chain. Keep medium, unavailable, malformed or unchecked results in human review. Never infer reuse rights from a host, title or attribution string. Unknown rights are not permission.

Preserve source IDs, asset IDs, query, license, attribution, digest and attempt trail. A high vision verdict never overrides rights, provenance, evidence or integrity gates.

NEXTDECODE guardrails:
- Preserve app/visuals/chain.py resolver and fallback architecture.
- Local-first/free-first; network vision providers explicitly configured.
- Keep STORYBOARD_GATE=require for production.
- Bound retries and deduplicate provider/query attempts.
- Add tests for low rejection, fallback, high acceptance, medium/unchecked review and unknown rights.
