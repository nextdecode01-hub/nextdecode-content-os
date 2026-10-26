#!/usr/bin/env python3
"""Pluggable text-to-speech provider chain for the Nextdecode content studio.

Nextdecode turns a generated script into a narrated vertical video.  Voiceover
is the one step that must never fail, so this module exposes a free-tier-first
provider chain with automatic fallback.

Priority order
--------------
1. ``edge_tts``   - local, free, unlimited (Microsoft Edge neural voices).
2. ``elevenlabs`` - free tier allows 10,000 characters per month.
3. ``cartesia``   - free tier allows 20,000 credits.
4. ``openai``     - paid (~0.015 USD/min), opt-in via ``TTS_PROVIDER=openai``.
5. ``silent``     - local ffmpeg tone, always available, zero cost.

Every provider is optional.  The chain walks the providers in priority order and
degrades gracefully, so a missing API key can never break the pipeline.  The
final ``silent`` stage guarantees that some valid mp3 always exists.

Configuration (``.env``)::

    TTS_PROVIDER=edge_tts
    TTS_MODEL=eleven_flash_v2_5
    TTS_VOICE=en-US-ChristopherNeural
    ELEVENLABS_API_KEY=...
    ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
    CARTESIA_API_KEY=...
    CARTESIA_VOICE_ID=...
    OPENAI_API_KEY=...

Credentials are never printed and :func:`synthesize` never raises; failures are
returned as ``{"path": None, "error": "..."}`` so callers can fall through to
the next provider.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROVIDERS = ["edge_tts", "elevenlabs", "cartesia", "openai", "silent"]

PROVIDER_ALIASES = {
    "edge": "edge_tts",
    "edge-tts": "edge_tts",
    "edge_tts_cli": "edge_tts",
    "edgetts": "edge_tts",
    "eleven": "elevenlabs",
    "eleven_labs": "elevenlabs",
    "11labs": "elevenlabs",
    "openai_tts": "openai",
    "tone": "silent",
    "fallback": "silent",
}

DEFAULT_VOICE = "en-US-ChristopherNeural"
DEFAULT_ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
DEFAULT_ELEVENLABS_MODEL = "eleven_flash_v2_5"
DEFAULT_CARTESIA_MODEL = "sonic-3"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini-tts"
DEFAULT_OPENAI_VOICE = "alloy"

ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech"
CARTESIA_URL = "https://api.cartesia.ai/tts/bytes"
CARTESIA_VERSION = "2024-06-10"
OPENAI_SPEECH_URL = "https://api.openai.com/v1/audio/speech"

WORDS_PER_SECOND = 2.6
MIN_DURATION = 1.0
EDGE_TTS_TIMEOUT = 300
HTTP_TIMEOUT = 120
FFMPEG_TIMEOUT = 300
CONCAT_TIMEOUT = 600
CHUNK_SIZE = 1800
ELEVENLABS_MAX_CHARS = 5000

TEST_SENTENCE = (
    "Nextdecode voice provider chain test. If you can hear this sentence, "
    "the local text to speech engine is working correctly."
)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _env(name: str, default: str = "") -> str:
    """Read an environment variable and strip optional surrounding quotes."""
    value = os.getenv(name, default)
    if value is None:
        return default
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1].strip()
    return value


def _normalize_provider(name: str | None) -> str | None:
    """Map a provider name or alias onto a canonical provider id."""
    if not name:
        return None
    key = name.strip().lower().replace(" ", "_")
    if key in PROVIDERS:
        return key
    if key in PROVIDER_ALIASES:
        return PROVIDER_ALIASES[key]
    underscored = key.replace("-", "_")
    if underscored in PROVIDERS:
        return underscored
    if underscored in PROVIDER_ALIASES:
        return PROVIDER_ALIASES[underscored]
    return None


def _find_edge_tts() -> str | None:
    """Locate the edge-tts CLI: PATH first, then the project virtualenvs."""
    for candidate_name in ("edge-tts", "edge-tts.exe"):
        found = shutil.which(candidate_name)
        if found:
            return found
    relatives = (
        "venv/bin/edge-tts",
        ".venv/bin/edge-tts",
        "venv/Scripts/edge-tts.exe",
        ".venv/Scripts/edge-tts.exe",
    )
    for relative in relatives:
        candidate = ROOT / relative
        if candidate.exists():
            return str(candidate)
    return None


def _find_ffmpeg() -> str | None:
    """Locate the ffmpeg binary."""
    for candidate_name in ("ffmpeg", "ffmpeg.exe"):
        found = shutil.which(candidate_name)
        if found:
            return found
    for relative in ("/usr/bin/ffmpeg", "venv/bin/ffmpeg", ".venv/bin/ffmpeg"):
        candidate = Path(relative) if relative.startswith("/") else ROOT / relative
        if candidate.exists():
            return str(candidate)
    return None


def _find_ffprobe() -> str | None:
    """Locate the ffprobe binary."""
    for candidate_name in ("ffprobe", "ffprobe.exe"):
        found = shutil.which(candidate_name)
        if found:
            return found
    for relative in ("/usr/bin/ffprobe", "venv/bin/ffprobe", ".venv/bin/ffprobe"):
        candidate = Path(relative) if relative.startswith("/") else ROOT / relative
        if candidate.exists():
            return str(candidate)
    return None


def _result(
    path: str | Path | None,
    provider: str,
    error: str | None,
    duration_hint: float,
    degraded: bool = False,
    **extra,
) -> dict:
    """Build the standard result payload."""
    payload = {
        "path": str(path) if path else None,
        "provider": provider,
        "error": error,
        "duration_hint": duration_hint,
        "degraded": bool(degraded),
    }
    payload.update(extra)
    return payload

# ---------------------------------------------------------------------------
# Provider readiness
# ---------------------------------------------------------------------------
def provider_status() -> dict:
    """Return ``{provider: {"configured": bool, "detail": str}}`` - never secrets."""
    edge_binary = _find_edge_tts()
    eleven_key = bool(_env("ELEVENLABS_API_KEY"))
    cartesia_key = bool(_env("CARTESIA_API_KEY"))
    cartesia_voice = bool(_env("CARTESIA_VOICE_ID"))
    openai_key = bool(_env("OPENAI_API_KEY"))
    ffmpeg_binary = _find_ffmpeg()

    return {
        "edge_tts": {
            "configured": bool(edge_binary),
            "detail": edge_binary or "not found - run './venv/bin/pip install edge-tts'",
        },
        "elevenlabs": {
            "configured": eleven_key,
            "detail": "ELEVENLABS_API_KEY set" if eleven_key else "set ELEVENLABS_API_KEY (free tier: 10,000 chars/month)",
        },
        "cartesia": {
            "configured": cartesia_key and cartesia_voice,
            "detail": "CARTESIA_API_KEY + CARTESIA_VOICE_ID set" if (cartesia_key and cartesia_voice)
            else "set CARTESIA_API_KEY and CARTESIA_VOICE_ID (free tier: 20,000 credits)",
        },
        "openai": {
            "configured": openai_key,
            "detail": "OPENAI_API_KEY set" if openai_key else "set OPENAI_API_KEY (paid, ~$0.015/min) - never used by default",
        },
        "silent": {
            "configured": bool(ffmpeg_binary),
            "detail": ffmpeg_binary or "not found - install ffmpeg in WSL",
        },
    }


def available_providers() -> list[str]:
    """Return the providers that are usable right now, in priority order."""
    status = provider_status()
    return [name for name in PROVIDERS if status.get(name, {}).get("configured")]


def list_providers() -> None:
    """Print a provider -> configured yes/no table.  Never prints secrets."""
    status = provider_status()
    default_provider = _default_provider()
    print("Nextdecode TTS provider chain (priority order)")
    print("-" * 96)
    print(f"{'#':<3}{'PROVIDER':<14}{'STATUS':<10}DETAIL")
    for index, name in enumerate(PROVIDERS, start=1):
        entry = status.get(name, {})
        mark = "READY" if entry.get("configured") else "NOT SET"
        print(f"{index:<3}{name:<14}{mark:<10}{entry.get('detail', '')}")
    print("-" * 96)
    print(f"Configured now: {', '.join(available_providers()) or 'none'}")
    print(f"Default provider: {default_provider}")
    print("Voice: " + (_env("TTS_VOICE") or DEFAULT_VOICE))
    print("Set a key with:  echo 'ELEVENLABS_API_KEY=sk_xxx' >> .env")


# ---------------------------------------------------------------------------
# Duration helpers
# ---------------------------------------------------------------------------
def estimate_duration(text: str) -> float:
    """Estimate spoken duration in seconds from the word count."""
    words = len(re.findall(r"[A-Za-z0-9']+", text or ""))
    if words <= 0:
        return MIN_DURATION
    return max(MIN_DURATION, round(words / WORDS_PER_SECOND, 2))


def probe_duration(path: str | Path) -> float | None:
    """Return the real duration of an audio file via ffprobe, or None."""
    ffprobe = _find_ffprobe()
    target = Path(path)
    if not ffprobe or not target.exists():
        return None
    try:
        completed = subprocess.run(
            [
                ffprobe,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=nw=1:nk=1",
                str(target),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    lines = (completed.stdout or "").strip().splitlines()
    if not lines:
        return None
    try:
        return round(float(lines[0]), 3)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def _split_oversized(text: str, max_chars: int) -> list[str]:
    """Break a single over-long sentence into word-sized pieces."""
    words = text.split()
    pieces: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_chars:
            pieces.append(current)
            current = word
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces


def chunk_text(text: str, max_chars: int = CHUNK_SIZE) -> list[str]:
    """Split a script into chunks on sentence boundaries.

    Long-form scripts (8-12 minutes, 1000-1850 words) exceed the per-request
    limits of hosted providers, so every chunk stays below ``max_chars``.
    """
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_oversized(sentence, max_chars))
            continue
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks

# ---------------------------------------------------------------------------
# Provider implementations - each one raises on failure
# ---------------------------------------------------------------------------
def _synthesize_edge_tts(text: str, out_path: Path, voice: str | None = None, model: str | None = None) -> None:
    """Render speech with the local edge-tts CLI (free, no key required)."""
    binary = _find_edge_tts()
    if not binary:
        raise RuntimeError("edge-tts CLI not found - run './venv/bin/pip install edge-tts'")
    voice_id = voice or _env("TTS_VOICE") or DEFAULT_VOICE
    out_path.parent.mkdir(parents=True, exist_ok=True)
    command = [binary, "--voice", voice_id, "--text", text, "--write-media", str(out_path)]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=EDGE_TTS_TIMEOUT,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(f"edge-tts exited with code {completed.returncode}: {detail[:500]}")
    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError("edge-tts produced no audio file")


def _synthesize_elevenlabs(text: str, out_path: Path, voice: str | None = None, model: str | None = None) -> None:
    """Render speech with ElevenLabs (free tier: 10,000 characters per month)."""
    api_key = _env("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is not set")
    if len(text) > ELEVENLABS_MAX_CHARS:
        raise RuntimeError(
            f"text is {len(text)} characters, over the {ELEVENLABS_MAX_CHARS} character "
            "per-request limit - use chunk_text()/synthesize_long()"
        )
    voice_id = voice or _env("ELEVENLABS_VOICE_ID") or DEFAULT_ELEVENLABS_VOICE_ID
    model_id = model or _env("ELEVENLABS_MODEL") or _env("TTS_MODEL") or DEFAULT_ELEVENLABS_MODEL
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
    }
    headers = {
        "xi-api-key": api_key,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    response = requests.post(
        f"{ELEVENLABS_URL}/{voice_id}",
        headers=headers,
        json=payload,
        timeout=HTTP_TIMEOUT,
    )
    if response.status_code in (401, 402, 429):
        raise RuntimeError(
            f"ElevenLabs returned HTTP {response.status_code}. The free tier allows "
            "10,000 characters per month - check the ElevenLabs quota, top up the plan, "
            "or pick another provider."
        )
    if response.status_code >= 400:
        raise RuntimeError(f"ElevenLabs returned HTTP {response.status_code}: {response.text[:300]}")
    if not response.content:
        raise RuntimeError("ElevenLabs returned an empty audio body")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(response.content)


def _synthesize_cartesia(text: str, out_path: Path, voice: str | None = None, model: str | None = None) -> None:
    """Render speech with Cartesia Sonic (free tier: 20,000 credits)."""
    api_key = _env("CARTESIA_API_KEY")
    if not api_key:
        raise RuntimeError("CARTESIA_API_KEY is not set")
    voice_id = voice or _env("CARTESIA_VOICE_ID")
    if not voice_id:
        raise RuntimeError("CARTESIA_VOICE_ID is not set")
    model_id = model or _env("CARTESIA_MODEL") or _env("TTS_MODEL") or DEFAULT_CARTESIA_MODEL
    payload = {
        "model_id": model_id,
        "transcript": text,
        "voice": {"mode": "id", "id": voice_id},
        "output_format": {"container": "mp3", "encoding": "mp3", "sample_rate": 44100},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Cartesia-Version": CARTESIA_VERSION,
        "Content-Type": "application/json",
    }
    response = requests.post(CARTESIA_URL, headers=headers, json=payload, timeout=HTTP_TIMEOUT)
    if response.status_code in (401, 402, 429):
        raise RuntimeError(
            f"Cartesia returned HTTP {response.status_code}. The free tier provides "
            "20,000 credits - check the Cartesia quota or pick another provider."
        )
    if response.status_code >= 400:
        raise RuntimeError(f"Cartesia returned HTTP {response.status_code}: {response.text[:300]}")
    if not response.content:
        raise RuntimeError("Cartesia returned an empty audio body")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(response.content)


def _synthesize_openai(text: str, out_path: Path, voice: str | None = None, model: str | None = None) -> None:
    """Render speech with the OpenAI speech endpoint (paid, opt-in)."""
    api_key = _env("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    model_id = model or _env("OPENAI_TTS_MODEL") or _env("TTS_MODEL") or DEFAULT_OPENAI_MODEL
    voice_id = voice or _env("OPENAI_TTS_VOICE") or DEFAULT_OPENAI_VOICE
    payload = {"model": model_id, "voice": voice_id, "input": text}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(OPENAI_SPEECH_URL, headers=headers, json=payload, timeout=HTTP_TIMEOUT)
    if response.status_code in (401, 402, 429):
        raise RuntimeError(
            f"OpenAI returned HTTP {response.status_code}. The account has no usable "
            "credit or the key is invalid - check the OpenAI billing page."
        )
    if response.status_code >= 400:
        raise RuntimeError(f"OpenAI returned HTTP {response.status_code}: {response.text[:300]}")
    if not response.content:
        raise RuntimeError("OpenAI returned an empty audio body")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(response.content)


def _synthesize_silent(text: str, out_path: Path, voice: str | None = None, model: str | None = None) -> None:
    """Render a silent mp3 of the right length with ffmpeg (always available)."""
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found - install ffmpeg in WSL")
    seconds = max(MIN_DURATION, estimate_duration(text))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg, "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=stereo",
        "-t", f"{seconds:.3f}",
        "-c:a", "libmp3lame",
        "-q:a", "9",
        str(out_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=FFMPEG_TIMEOUT)
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip()
        raise RuntimeError(f"ffmpeg could not render the silent fallback: {detail[-500:]}")
    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError("ffmpeg produced no audio file for the silent fallback")


_SYNTHESIZERS = {
    "edge_tts": _synthesize_edge_tts,
    "elevenlabs": _synthesize_elevenlabs,
    "cartesia": _synthesize_cartesia,
    "openai": _synthesize_openai,
    "silent": _synthesize_silent,
}

# ---------------------------------------------------------------------------
# Public synthesis API
# ---------------------------------------------------------------------------
def _default_provider() -> str:
    """The provider used when no explicit choice is made."""
    return _normalize_provider(_env("TTS_PROVIDER")) or "edge_tts"


def _provider_chain(preferred: str | None = None) -> list[str]:
    """Build the ordered provider chain, honouring an explicit preference."""
    name = _normalize_provider(preferred) if preferred else _normalize_provider(_env("TTS_PROVIDER"))
    chain = list(PROVIDERS)
    if name and name in chain:
        chain.remove(name)
        chain.insert(0, name)
    return chain


def synthesize(
    text: str,
    out_path: str | Path,
    *,
    provider: str | None = None,
    voice: str | None = None,
    model: str | None = None,
) -> dict:
    """Synthesize ``text`` with exactly one provider.

    Returns ``{"path": str|None, "provider": str, "error": str|None,
    "duration_hint": float}``.  This function never raises: a provider failure
    is reported through the ``error`` key with ``path`` set to ``None``.
    """
    target = Path(out_path)
    hint = estimate_duration(text)

    if provider is None:
        name = _default_provider()
    else:
        name = _normalize_provider(provider)
        if name is None:
            return _result(
                None,
                str(provider),
                f"Unknown TTS provider '{provider}'. Valid providers: {', '.join(PROVIDERS)}.",
                hint,
            )

    if not (text or "").strip():
        return _result(None, name, "Refusing to synthesize empty text.", hint)

    try:
        _SYNTHESIZERS[name](text, target, voice=voice, model=model)
    except Exception as exc:  # noqa: BLE001 - the chain must never break
        error = f"{type(exc).__name__}: {exc}"
        try:
            if target.exists() and target.stat().st_size == 0:
                target.unlink()
        except OSError:
            pass
        return _result(None, name, error, hint, degraded=(name == "silent"))

    return _result(target.resolve(), name, None, hint, degraded=(name == "silent"))


def synthesize_with_fallback(
    text: str,
    out_path: str | Path,
    *,
    preferred: str | None = None,
) -> dict:
    """Walk the provider chain until one succeeds.  Never raises."""
    target = Path(out_path)
    hint = estimate_duration(text)
    chain = _provider_chain(preferred)
    errors: list[str] = []
    last_provider = chain[-1] if chain else "none"

    for name in chain:
        result = synthesize(text, target, provider=name)
        if result.get("path"):
            result["chain"] = chain
            return result
        last_provider = name
        errors.append(f"{name}: {result.get('error')}")

    return _result(
        None,
        last_provider,
        "Every TTS provider failed -> " + " | ".join(errors),
        hint,
        degraded=True,
        chain=chain,
    )


def _concat_mp3(parts: list[Path], out_path: Path) -> None:
    """Concatenate mp3 files with the ffmpeg concat demuxer."""
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found - install ffmpeg in WSL")
    listing = out_path.parent / f".{out_path.stem}_concat.txt"
    listing.write_text("\n".join(f"file '{part}'" for part in parts) + "\n", encoding="utf-8")
    try:
        command = [
            ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(listing),
            "-c", "copy",
            str(out_path),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=CONCAT_TIMEOUT)
        if completed.returncode != 0 or not out_path.exists() or out_path.stat().st_size == 0:
            # Stream copy failed (mismatched mp3 headers) - re-encode instead.
            command = [
                ffmpeg, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(listing),
                "-c:a", "libmp3lame",
                "-q:a", "2",
                str(out_path),
            ]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=CONCAT_TIMEOUT)
            if completed.returncode != 0:
                detail = (completed.stderr or "").strip()
                raise RuntimeError(f"ffmpeg concat failed: {detail[-500:]}")
    finally:
        try:
            listing.unlink()
        except OSError:
            pass


def synthesize_long(
    text: str,
    out_path: str | Path,
    *,
    preferred: str | None = None,
) -> dict:
    """Synthesize a long script chunk by chunk and concatenate into one mp3."""
    target = Path(out_path)
    chunks = chunk_text(text, CHUNK_SIZE)
    hint = estimate_duration(text)
    if not chunks:
        return _result(None, "none", "Nothing to synthesize (empty text).", hint)

    target.parent.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix="nextdecode_tts_"))
    produced: list[Path] = []
    warnings: list[str] = []
    provider_used = "none"

    try:
        for index, chunk in enumerate(chunks):
            chunk_path = workdir / f"chunk_{index:04d}.mp3"
            result = synthesize_with_fallback(chunk, chunk_path, preferred=preferred)
            if not result.get("path"):
                warnings.append(f"chunk {index + 1}/{len(chunks)} failed: {result.get('error')}")
                continue
            produced.append(chunk_path)
            provider_used = result.get("provider", provider_used)

        if not produced:
            return _result(
                None,
                provider_used,
                "Every chunk failed -> " + " | ".join(warnings),
                hint,
                degraded=True,
            )

        _concat_mp3(produced, target)
        if not target.exists() or target.stat().st_size == 0:
            return _result(None, provider_used, "ffmpeg concat produced an empty file", hint, degraded=True)

        return _result(
            target.resolve(),
            provider_used,
            None,
            hint,
            degraded=bool(warnings),
            chunks=len(chunks),
            rendered_chunks=len(produced),
            duration=probe_duration(target),
            warnings=warnings,
        )
    except Exception as exc:  # noqa: BLE001 - never break the pipeline
        return _result(
            None,
            provider_used,
            f"{type(exc).__name__}: {exc}",
            hint,
            degraded=True,
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nextdecode text-to-speech provider chain")
    parser.add_argument("--list", action="store_true", help="Print the provider table and exit")
    parser.add_argument("--speak", metavar="TEXT", help="Synthesize TEXT and write an mp3")
    parser.add_argument("--text-file", metavar="PATH", help="Read the text to speak from a file")
    parser.add_argument("--test", action="store_true", help="Run a short fixed sentence through the chain")
    parser.add_argument("--out", metavar="PATH", help="Output mp3 path (default: tts_output.mp3)")
    parser.add_argument("--provider", help="Force one provider instead of walking the chain")
    parser.add_argument("--voice", help="Override the voice / voice id")
    parser.add_argument("--model", help="Override the model")
    parser.add_argument("--long", action="store_true", help="Use chunked long-form synthesis")
    return parser


def _print_result(result: dict) -> None:
    print(f"[+] Provider : {result.get('provider')}")
    print(f"[+] Output   : {result.get('path') or '(none)'}")
    if result.get("degraded"):
        print("[!] Degraded output - the pipeline keeps running but the audio is not real narration.")
    if result.get("error"):
        print(f"[!] Error    : {result.get('error')}")
    if result.get("path"):
        media = Path(result["path"])
        print(f"[+] Size     : {media.stat().st_size if media.exists() else 0} bytes")
        probed = probe_duration(result["path"])
        print(f"[+] Duration : {probed if probed is not None else 'unknown'}s (estimated {result.get('duration_hint')}s)")
        if result.get("chunks"):
            print(f"[+] Chunks   : {result.get('rendered_chunks')}/{result.get('chunks')} rendered")
    else:
        print(f"[+] Estimated duration: {result.get('duration_hint')}s")


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.list:
        list_providers()
        return 0

    text = ""
    if args.speak:
        text = args.speak
    elif args.text_file:
        text = Path(args.text_file).read_text(encoding="utf-8")
    elif args.test:
        text = TEST_SENTENCE
    else:
        parser.print_help()
        print("\nUse --list, --speak, --test or --text-file.")
        return 0

    out_path = Path(args.out) if args.out else ROOT / "tts_output.mp3"

    if args.long:
        result = synthesize_long(text, out_path, preferred=args.provider)
    elif args.provider:
        result = synthesize(text, out_path, provider=args.provider, voice=args.voice, model=args.model)
    else:
        result = synthesize_with_fallback(text, out_path, preferred=args.provider)

    _print_result(result)
    if args.test:
        print("[+] " + ("TEST PASSED" if result.get("path") else "TEST FAILED"))
    return 0 if result.get("path") else 1


if __name__ == "__main__":
    raise SystemExit(main())