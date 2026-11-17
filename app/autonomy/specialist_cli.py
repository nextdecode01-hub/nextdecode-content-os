"""CLI boundary for sandboxed research and script-drafting specialists."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "outputs" / "autonomy" / "artifacts"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _save_artifact(kind: str, topic: str, payload: dict, *, studio_provenance: dict | None = None) -> dict:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex
    artifact_id = uuid.uuid4().hex
    envelope = {
        "schema_version": "nextdecode.autonomy-artifact.v1",
        "artifact_id": artifact_id,
        "run_id": run_id,
        "artifact_type": kind,
        "topic": topic,
        "created_at": _now(),
        "human_review_status": "pending",
        "external_actions_allowed": False,
        "payload": payload,
    }
    if studio_provenance:
        envelope["studio_provenance"] = dict(studio_provenance)
    raw = (json.dumps(envelope, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    path = ARTIFACT_ROOT / f"{kind}-{run_id}.json"
    path.write_bytes(raw)
    path.chmod(0o600)
    return {
        "run_id": run_id,
        "artifact_id": artifact_id,
        "artifact_path": path.relative_to(ROOT).as_posix(),
        "artifact_sha256": digest,
        "artifact_type": kind,
        "topic": topic,
        "human_review_status": "pending",
        "external_actions_allowed": False,
    }


def _research(topic: str, max_sources: int, studio_version_id: str = "",
              studio_content_sha256: str = "") -> dict:
    from app.research.desk import research_topic

    result = research_topic(topic, max_sources=max_sources)
    sources = []
    for page in result.get("sources", []):
        sources.append({
            "title": str(page.get("title", ""))[:240],
            "summary": str(page.get("text", ""))[:700],
            "url": str(page.get("url", ""))[:1000],
            "published": str(page.get("published", ""))[:80],
            "source": str(page.get("source", page.get("domain", "web")))[:100],
            "rank": float(page.get("relevance", page.get("rank", 0)) or 0),
        })
    compact = {
        "topic": topic,
        "verdict": result.get("verdict", "insufficient"),
        "sources": sources,
        "claims": result.get("claims", [])[:14],
        "contradictions": result.get("contradictions", [])[:10],
        "unsupported_numbers": result.get("unsupported_numbers", [])[:20],
        "limitations": result.get("limitations", [])[:20],
        "errors": [str(item)[:300] for item in result.get("errors", [])[:20]],
    }
    if compact["verdict"] != "sufficient" or not sources:
        raise RuntimeError("research evidence is insufficient; refusing to draft from weak evidence")
    provenance = None
    if studio_version_id or studio_content_sha256:
        if not re.fullmatch(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", studio_version_id):
            raise ValueError("invalid Studio version identity")
        if not re.fullmatch(r"[a-f0-9]{64}", studio_content_sha256):
            raise ValueError("invalid Studio content digest")
        provenance = {"studio_version_id": studio_version_id,
                      "studio_content_sha256": studio_content_sha256}
    artifact = _save_artifact("research-brief", topic, compact, studio_provenance=provenance)
    return {
        "status": "success",
        **artifact,
        "source_count": len(sources),
        "claim_count": len(compact["claims"]),
        "research_verdict": compact["verdict"],
        "source_urls": [item["url"] for item in sources],
        **(provenance or {}),
    }


def _load_research_artifact(path_value: str, expected_sha256: str,
                            expected_studio_provenance: dict | None = None) -> list[dict]:
    path = (ROOT / path_value).resolve()
    allowed_root = ARTIFACT_ROOT.resolve()
    if allowed_root not in path.parents or not path.is_file():
        raise ValueError("research artifact reference is outside the autonomy artifact store")
    raw = path.read_bytes()
    if len(raw) > 1_000_000:
        raise ValueError("research artifact exceeds the size limit")
    actual = hashlib.sha256(raw).hexdigest()
    if not expected_sha256 or actual != expected_sha256:
        raise ValueError("research artifact integrity check failed")
    envelope = json.loads(raw.decode("utf-8"))
    if envelope.get("schema_version") != "nextdecode.autonomy-artifact.v1":
        raise ValueError("unsupported research artifact schema")
    if envelope.get("artifact_type") != "research-brief":
        raise ValueError("dependency is not a research brief")
    if expected_studio_provenance is not None and envelope.get("studio_provenance") != expected_studio_provenance:
        raise ValueError("research artifact Studio provenance does not match the requested version")
    sources = envelope.get("payload", {}).get("sources", [])
    if not isinstance(sources, list) or not sources:
        raise ValueError("research brief has no usable source records")
    # Preserve the full research artifact, but keep the local-model prompt bounded.
    # The first two selected source records feed the Short script draft.
    return sources[:2]


def _draft_script(kind: str, topic: str, research_path: str = "",
                 research_sha256: str = "", studio_version_id: str = "",
                 studio_content_sha256: str = "") -> dict:
    if not research_path:
        raise ValueError("a verified research artifact is required before script drafting")
    provenance = None
    if studio_version_id or studio_content_sha256:
        if not re.fullmatch(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", studio_version_id):
            raise ValueError("invalid Studio version identity")
        if not re.fullmatch(r"[a-f0-9]{64}", studio_content_sha256):
            raise ValueError("invalid Studio content digest")
        provenance = {"studio_version_id": studio_version_id,
                      "studio_content_sha256": studio_content_sha256}
    candidates = _load_research_artifact(research_path, research_sha256, provenance)
    if kind == "short-script":
        from app.script.short import generate_script
        draft = generate_script(topic, research_candidates=candidates)
        artifact_type = "short-script-draft"
    elif kind == "longform-script":
        from app.script.longform import generate_script
        draft = generate_script(topic, research_candidates=candidates)
        artifact_type = "longform-script-draft"
    else:
        raise ValueError("unsupported script specialist")
    artifact = _save_artifact(artifact_type, topic, draft, studio_provenance=provenance)
    return {
        "status": "success",
        **artifact,
        "title": str(draft.get("title", ""))[:120],
        "word_count": int(draft.get("word_count", len(str(draft.get("voice_text", "")).split()))),
        "source_urls": [str(url)[:1000] for url in draft.get("source_urls", [])[:12]],
        "review_status": "pending",
        **(provenance or {}),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nextdecode-specialist")
    sub = parser.add_subparsers(dest="specialist", required=True)
    research = sub.add_parser("research")
    research.add_argument("--topic", required=True)
    research.add_argument("--max-sources", type=int, default=4)
    research.add_argument("--studio-version-id", default="")
    research.add_argument("--studio-content-sha256", default="")
    for name in ("short-script", "longform-script"):
        draft = sub.add_parser(name)
        draft.add_argument("--topic", required=True)
        draft.add_argument("--research-artifact", required=True)
        draft.add_argument("--research-sha256", required=True)
        draft.add_argument("--studio-version-id", default="")
        draft.add_argument("--studio-content-sha256", default="")
    args = parser.parse_args(argv)
    try:
        if not isinstance(args.topic, str) or not 1 <= len(args.topic.strip()) <= 200:
            raise ValueError("topic must be 1..200 characters")
        if args.specialist == "research":
            if not 1 <= args.max_sources <= 5:
                raise ValueError("max_sources must be between 1 and 5")
            result = _research(args.topic.strip(), args.max_sources,
                               args.studio_version_id, args.studio_content_sha256)
        else:
            result = _draft_script(args.specialist, args.topic.strip(),
                                   args.research_artifact, args.research_sha256,
                                   args.studio_version_id, args.studio_content_sha256)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({
            "status": "failed",
            "error_code": type(exc).__name__.lower(),
            "message": re.sub(r"\s+", " ", str(exc))[:500],
        }, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
