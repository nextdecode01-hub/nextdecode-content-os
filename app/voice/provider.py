#!/usr/bin/env python3
"""Pluggable text-to-speech provider chain for the Nextdecode content studio.

Nextdecode turns a generated script into a narrated vertical video.  Voiceover
is the one step that must never fail, so this module exposes a free-tier-first
provider chain with automatic fallback.

Priority order
--------------
1. ``edge_tts``    - free Microsoft Edge neural TTS service (network required).
2. ``kokoro_local`` - local Kokoro-82M neural TTS; no API key or per-run cost.
3. ``elevenlabs``  - optional hosted provider with a limited free tier.
4. ``cartesia``    - optional hosted provider with a limited free tier.
5. ``openai``      - paid; only used when explicitly configured.
6. ``silent``      - diagnostic-only ffmpeg tone, never valid narration by default.

Every provider is optional. The chain prefers free local synthesis before hosted
providers. Silent output is diagnostic-only and is rejected as production narration.

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
import fcntl
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=True)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROVIDERS = ["edge_tts", "kokoro_local", "gtts", "elevenlabs", "cartesia", "openai", "silent"]

PROVIDER_ALIASES = {
    "edge": "edge_tts",
    "edge-tts": "edge_tts",
    "edge_tts_cli": "edge_tts",
    "edgetts": "edge_tts",
    "kokoro": "kokoro_local",
    "kokoro-js": "kokoro_local",
    "eleven": "elevenlabs",
    "eleven_labs": "elevenlabs",
    "11labs": "elevenlabs",
    "openai_tts": "openai",
    "tone": "silent",
    "fallback": "silent",
}

# Approved in Phase 9 after the Phase 8 A/B listening test: Andrew Multilingual is
# the production narration voice.  TTS_VOICE still overrides this.
DEFAULT_VOICE = "en-US-AndrewMultilingualNeural"
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
EDGE_TTS_TIMEOUT = 30
HTTP_TIMEOUT = 120
FFMPEG_TIMEOUT = 300
CONCAT_TIMEOUT = 600
KOKORO_INFERENCE_TIMEOUT = 240
KOKORO_LOCK_WAIT_SECONDS = 30
CHUNK_SIZE = 1800
KOKORO_CHUNK_SIZE = 320
ELEVENLABS_MAX_CHARS = 5000

# Edge TTS exposes only these three prosody controls.  Defaults are neutral so
# existing renders do not change unless TTS_RATE/TTS_PITCH/TTS_VOLUME is set.
DEFAULT_EDGE_RATE = "+0%"
DEFAULT_EDGE_PITCH = "+0Hz"
DEFAULT_EDGE_VOLUME = "+0%"
_RATE_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?%$")
_PITCH_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?Hz$")

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


def _edge_prosody(rate: str | None = None, pitch: str | None = None,
                  volume: str | None = None) -> dict[str, str]:
    """Resolve and validate conservative Edge prosody values.

    Explicit arguments win over ``TTS_RATE``/``TTS_PITCH``/``TTS_VOLUME``.
    Invalid values fall back to neutral instead of failing the provider chain.
    """
    def pick(explicit: str | None, env_name: str, default: str,
             pattern: re.Pattern[str]) -> str:
        value = str(explicit if explicit not in (None, "") else (_env(env_name) or default)).strip()
        if pattern.fullmatch(value):
            return value
        print(f"[tts] invalid {env_name or 'prosody value'} {value!r}; using {default}")
        return default

    return {
        "rate": pick(rate, "TTS_RATE", DEFAULT_EDGE_RATE, _RATE_RE),
        "pitch": pick(pitch, "TTS_PITCH", DEFAULT_EDGE_PITCH, _PITCH_RE),
        "volume": pick(volume, "TTS_VOLUME", DEFAULT_EDGE_VOLUME, _RATE_RE),
    }


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


def _audio_peak_db(path: str | Path) -> float:
    """Measure decoded audio peak; reject empty or effectively silent TTS output."""
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found - cannot validate synthesized audio")
    completed = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True, timeout=FFMPEG_TIMEOUT,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(f"audio validation failed: {detail[-400:]}")
    match = re.search(r"max_volume:\s*(-?inf|-?\d+(?:\.\d+)?) dB", completed.stderr or "")
    if not match:
        raise RuntimeError("audio validation failed: ffmpeg did not report a measurable peak")
    value = float("-inf") if match.group(1) == "-inf" else float(match.group(1))
    if value <= -55.0:
        raise RuntimeError(f"TTS output is silent or near-silent (peak {value:.1f} dBFS)")
    return value


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
    kokoro_status = _kokoro_runtime_status()

    return {
        "edge_tts": {
            "configured": bool(edge_binary),
            "detail": edge_binary or "not found - run './venv/bin/pip install edge-tts'",
        },
        "kokoro_local": {
            "configured": kokoro_status["configured"],
            "detail": kokoro_status["detail"],
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
    prosody = _edge_prosody()
    print(
        "Edge prosody: rate {rate}, pitch {pitch}, volume {volume}".format(**prosody)
    )
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


def probe_audio_format(path: str | Path) -> dict:
    """Return ``{codec, sample_rate, channels, bit_rate}`` for an audio file."""
    ffprobe = _find_ffprobe()
    target = Path(path)
    if not ffprobe or not target.exists():
        return {}
    try:
        completed = subprocess.run(
            [
                ffprobe, "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_name,sample_rate,channels,bit_rate",
                "-of", "default=nw=1:nk=1",
                str(target),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    values = [line.strip() for line in (completed.stdout or "").splitlines() if line.strip()]
    keys = ("codec", "sample_rate", "channels", "bit_rate")
    info: dict[str, object] = {}
    for key, value in zip(keys, values):
        if not key.startswith("bit"):
            info[key] = value
        else:
            try:
                info[key] = int(value)
            except (TypeError, ValueError):
                info[key] = None
    return info


# ---------------------------------------------------------------------------
# Lossless master handling
# ---------------------------------------------------------------------------
MASTER_SAMPLE_RATE = 44100
MASTER_BITRATE = "320k"


def to_wav_master(src: str | Path, dst: str | Path | None = None) -> Path | None:
    """Decode a provider file once into a 44.1 kHz mono 24-bit WAV master.

    The narration is the asset every later stage reads, so it is decoded a single
    time and then handled losslessly.  Mixing from this WAV instead of the
    provider mp3 avoids a second lossy generation on the way to the video.
    """
    ffmpeg = _find_ffmpeg()
    source = Path(src)
    if not ffmpeg or not source.exists():
        return None
    target = Path(dst) if dst else source.with_suffix(".wav")
    command = [
        ffmpeg, "-y", "-v", "error",
        "-i", str(source),
        "-vn",
        "-ac", "1",
        "-ar", str(MASTER_SAMPLE_RATE),
        "-c:a", "pcm_s24le",
        str(target),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=FFMPEG_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0 or not target.exists() or target.stat().st_size == 0:
        return None
    return target


def export_master_mp3(src: str | Path, dst: str | Path,
                      bitrate: str = MASTER_BITRATE,
                      audio_filter: str | None = None) -> Path | None:
    """Write the narration deliverable as constant-bitrate mp3 from the master.

    ``-b:a`` sets the requested CBR; it cannot add information the provider did
    not render, it only prevents another lossy round-trip from hiding what is
    already there.  Pass the same loudness filter the video mix uses so the
    standalone file matches what the render sounds like.
    """
    ffmpeg = _find_ffmpeg()
    source = Path(src)
    if not ffmpeg or not source.exists():
        return None
    target = Path(dst)
    command = [
        ffmpeg, "-y", "-v", "error",
        "-i", str(source),
        "-vn",
        "-ac", "1",
        "-ar", str(MASTER_SAMPLE_RATE),
    ]
    if audio_filter:
        command += ["-af", str(audio_filter)]
    command += ["-c:a", "libmp3lame", "-b:a", str(bitrate), str(target)]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=FFMPEG_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0 or not target.exists() or target.stat().st_size == 0:
        return None
    return target


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
def _synthesize_edge_tts(text: str, out_path: Path, voice: str | None = None,
                         model: str | None = None, rate: str | None = None,
                         pitch: str | None = None, volume: str | None = None) -> None:
    """Render speech with the local edge-tts CLI (free, no key required)."""
    binary = _find_edge_tts()
    if not binary:
        raise RuntimeError("edge-tts CLI not found - run './venv/bin/pip install edge-tts'")
    voice_id = voice or _env("TTS_VOICE") or DEFAULT_VOICE
    prosody = _edge_prosody(rate, pitch, volume)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        binary,
        "--voice", voice_id,
        "--rate", prosody["rate"],
        "--pitch", prosody["pitch"],
        "--volume", prosody["volume"],
        "--text", text,
        "--write-media", str(out_path),
    ]
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


def _synthesize_gtts(text: str, out_path: Path, voice: str | None = None,
                    model: str | None = None) -> None:
    """Free network fallback using the already-installed gTTS client.

    It is intentionally below Edge/Kokoro in the chain and remains identifiable
    in run metadata so a human can reject or replace the voice during review.
    """
    from gtts import gTTS

    out_path.parent.mkdir(parents=True, exist_ok=True)
    speech = gTTS(text=text, lang="en", tld="com", slow=False, timeout=(10, 45))
    speech.save(str(out_path))


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


def _kokoro_runtime_status() -> dict:
    """Check the configured offline Kokoro runtime without attempting network access."""
    node = shutil.which("node")
    js_entry = Path(_env("KOKORO_JS_ENTRY")) if _env("KOKORO_JS_ENTRY") else None
    transformers_entry = Path(_env("KOKORO_TRANSFORMERS_ENTRY")) if _env("KOKORO_TRANSFORMERS_ENTRY") else None
    cache_dir = Path(_env("KOKORO_MODEL_CACHE")) if _env("KOKORO_MODEL_CACHE") else None
    model_id = _env("KOKORO_MODEL_ID", "onnx-community/Kokoro-82M-v1.0-ONNX")
    voice_id = _env("KOKORO_VOICE", "am_fenrir")
    model_path = cache_dir / model_id / "onnx" / "model_q4.onnx" if cache_dir else None
    voice_path = js_entry.parent.parent / "voices" / f"{voice_id}.bin" if js_entry else None
    missing = []
    if not node:
        missing.append("node executable")
    if not js_entry or not js_entry.is_file():
        missing.append("KOKORO_JS_ENTRY")
    if not transformers_entry or not transformers_entry.is_file():
        missing.append("KOKORO_TRANSFORMERS_ENTRY")
    if not model_path or not model_path.is_file():
        missing.append("cached Kokoro q4 model")
    if not voice_path or not voice_path.is_file():
        missing.append(f"Kokoro voice {voice_id}")
    return {
        "configured": not missing,
        "detail": "local Kokoro runtime ready" if not missing else "missing " + ", ".join(missing),
        "node": node,
        "js_entry": str(js_entry) if js_entry else "",
        "transformers_entry": str(transformers_entry) if transformers_entry else "",
        "cache_dir": str(cache_dir) if cache_dir else "",
        "model_id": model_id,
        "voice": voice_id,
    }


def _synthesize_kokoro_local(text: str, out_path: Path, voice: str | None = None,
                             model: str | None = None) -> None:
    """Generate neural narration offline with the configured local Kokoro-82M model."""
    status = _kokoro_runtime_status()
    if not status["configured"]:
        raise RuntimeError(f"local Kokoro is not ready: {status['detail']}")
    script_path = ROOT / "app" / "voice" / "kokoro_local.mjs"
    if not script_path.is_file():
        raise RuntimeError(f"Kokoro runner is missing: {script_path}")

    voice_id = voice if voice and not voice.lower().startswith("en-") else status["voice"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    chunks = chunk_text(text, KOKORO_CHUNK_SIZE)
    if not chunks:
        raise RuntimeError("Kokoro received empty narration text")
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found - cannot encode Kokoro output")

    with tempfile.TemporaryDirectory(prefix="nextdecode_kokoro_", dir=str(out_path.parent)) as temp_dir:
        temp_root = Path(temp_dir)
        chunk_paths = [temp_root / f"chunk_{index:03d}.wav" for index in range(len(chunks))]
        payload = {
            "chunks": chunks,
            "output_dir": str(temp_root),
            "voice": voice_id,
            "speed": float(_env("KOKORO_SPEED", "1.45")),
            "model_id": model or status["model_id"],
        }
        lock_path = ROOT / "data" / "cache" / "kokoro_inference.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+") as lock_handle:
            deadline = time.monotonic() + KOKORO_LOCK_WAIT_SECONDS
            while True:
                try:
                    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Kokoro inference lock remained busy; another run may be stuck")
                    time.sleep(0.25)
            try:
                inference_timeout = max(
                    30, min(600, int(_env("KOKORO_INFERENCE_TIMEOUT", str(KOKORO_INFERENCE_TIMEOUT))))
                )
                completed = subprocess.run(
                    [status["node"], str(script_path)],
                    input=json.dumps(payload), capture_output=True, text=True,
                    timeout=inference_timeout,
                )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(
                    f"Kokoro inference timed out after {inference_timeout}s; lock released for recovery"
                ) from exc
            finally:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise RuntimeError(f"Kokoro local inference failed: {detail[-600:]}")
        missing = [path.name for path in chunk_paths if not path.is_file() or path.stat().st_size == 0]
        if missing:
            raise RuntimeError("Kokoro did not produce all narration chunks: " + ", ".join(missing))

        wav_path = temp_root / "combined.wav"
        listing = temp_root / "chunks.txt"
        listing.write_text(
            "".join(f"file '{path.as_posix()}'\n" for path in chunk_paths),
            encoding="utf-8",
        )
        combined = subprocess.run(
            [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat",
             "-safe", "0", "-i", str(listing), "-ac", "1", "-ar", "24000",
             "-c:a", "pcm_s16le", str(wav_path)],
            capture_output=True, text=True, timeout=CONCAT_TIMEOUT,
        )
        if combined.returncode != 0 or not wav_path.is_file() or wav_path.stat().st_size == 0:
            detail = (combined.stderr or combined.stdout or "").strip()
            raise RuntimeError(f"could not concatenate Kokoro WAV chunks: {detail[-500:]}")

        encoded = subprocess.run(
            [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav_path),
             "-vn", "-ac", "1", "-ar", "24000", "-c:a", "libmp3lame", "-b:a", "192k", str(out_path)],
            capture_output=True, text=True, timeout=FFMPEG_TIMEOUT,
        )
        if encoded.returncode != 0:
            detail = (encoded.stderr or encoded.stdout or "").strip()
            raise RuntimeError(f"ffmpeg could not encode Kokoro audio: {detail[-500:]}")
        if not out_path.is_file() or out_path.stat().st_size == 0:
            raise RuntimeError("Kokoro chunk concatenation produced no MP3 output")


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
    "kokoro_local": _synthesize_kokoro_local,
    "gtts": _synthesize_gtts,
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
    """Build the ordered narration chain without silently degrading by default.

    Silent output is a diagnostic fallback, not valid narration. It is included
    only when explicitly enabled with TTS_ALLOW_SILENT_FALLBACK=true.
    """
    name = _normalize_provider(preferred) if preferred else _normalize_provider(_env("TTS_PROVIDER"))
    allow_silent = _env("TTS_ALLOW_SILENT_FALLBACK").strip().lower() in {
        "1", "true", "yes", "on",
    }
    chain = [provider for provider in PROVIDERS if provider != "silent" or allow_silent]
    if _env("TTS_ALLOW_LOCAL_MODELS").lower() not in {"1", "true", "yes", "on"}:
        chain = [provider for provider in chain if provider != "kokoro_local"]
    if name == "silent" and allow_silent:
        chain.remove("silent")
        chain.insert(0, "silent")
    elif name and name in chain:
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
    rate: str | None = None,
    pitch: str | None = None,
    volume: str | None = None,
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

    if name == "kokoro_local" and _env("TTS_ALLOW_LOCAL_MODELS").lower() not in {"1", "true", "yes", "on"}:
        return _result(
            None, name,
            "Local TTS models are disabled by TTS_ALLOW_LOCAL_MODELS; select a hosted/free network provider.",
            hint,
        )

    if not (text or "").strip():
        return _result(None, name, "Refusing to synthesize empty text.", hint)

    try:
        if name == "edge_tts":
            _SYNTHESIZERS[name](
                text, target, voice=voice, model=model,
                rate=rate, pitch=pitch, volume=volume,
            )
        else:
            _SYNTHESIZERS[name](text, target, voice=voice, model=model)
    except Exception as exc:  # noqa: BLE001 - the chain must never break
        error = f"{type(exc).__name__}: {exc}"
        try:
            if target.exists() and target.stat().st_size == 0:
                target.unlink()
        except OSError:
            pass
        return _result(None, name, error, hint, degraded=(name == "silent"))

    try:
        peak_db = _audio_peak_db(target)
        if peak_db <= -55.0:
            raise RuntimeError(f"TTS output is silent or near-silent (peak {peak_db:.1f} dBFS)")
    except Exception as exc:  # noqa: BLE001 - invalid audio must not enter the pipeline
        return _result(None, name, f"Invalid synthesized audio: {exc}", hint, degraded=True)
    return _result(target.resolve(), name, None, hint, degraded=(name == "silent"),
                   audio_peak_db=peak_db)


def synthesize_with_fallback(
    text: str,
    out_path: str | Path,
    *,
    preferred: str | None = None,
    voice: str | None = None,
    rate: str | None = None,
    pitch: str | None = None,
    volume: str | None = None,
) -> dict:
    """Walk the provider chain until one succeeds.  Never raises."""
    target = Path(out_path)
    hint = estimate_duration(text)
    chain = _provider_chain(preferred)
    errors: list[str] = []
    last_provider = chain[-1] if chain else "none"

    for name in chain:
        if name == "edge_tts":
            result = synthesize(
                text, target, provider=name, voice=voice,
                rate=rate, pitch=pitch, volume=volume,
            )
        else:
            # A Microsoft voice id is not valid for the hosted providers.
            result = synthesize(text, target, provider=name)
        if result.get("path") and not result.get("degraded"):
            result["chain"] = chain
            return result
        last_provider = name
        reason = result.get("error") or (
            "provider returned degraded audio; not accepted as narration"
            if result.get("degraded") else "provider returned no output path"
        )
        errors.append(f"{name}: {reason}")

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
    voice: str | None = None,
    rate: str | None = None,
    pitch: str | None = None,
    volume: str | None = None,
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
            result = synthesize_with_fallback(
                chunk, chunk_path, preferred=preferred, voice=voice,
                rate=rate, pitch=pitch, volume=volume,
            )
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
    parser.add_argument("--rate", help="Edge TTS rate, e.g. -4%%")
    parser.add_argument("--pitch", help="Edge TTS pitch, e.g. +0Hz")
    parser.add_argument("--volume", help="Edge TTS volume, e.g. +0%%")
    parser.add_argument("--long", action="store_true", help="Use chunked long-form synthesis")
    parser.add_argument("--master", action="store_true",
                        help="Also write a lossless WAV master and a 320 kbps CBR mp3 deliverable")
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
        info = probe_audio_format(result["path"])
        if info:
            print(f"[+] Source   : {info.get('codec')} {info.get('sample_rate')} Hz "
                  f"{info.get('channels')} ch {info.get('bit_rate') or 0} bps")
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

    out_path = Path(args.out) if args.out else ROOT / "outputs" / "tts_output.mp3"

    if args.long:
        result = synthesize_long(
            text, out_path, preferred=args.provider, voice=args.voice,
            rate=args.rate, pitch=args.pitch, volume=args.volume,
        )
    elif args.provider:
        result = synthesize(
            text, out_path, provider=args.provider, voice=args.voice,
            model=args.model, rate=args.rate, pitch=args.pitch, volume=args.volume,
        )
    else:
        result = synthesize_with_fallback(
            text, out_path, preferred=args.provider, voice=args.voice,
            rate=args.rate, pitch=args.pitch, volume=args.volume,
        )

    _print_result(result)
    if args.master and result.get("path"):
        source = Path(result["path"])
        wav = to_wav_master(source, source.with_suffix(".wav"))
        mp3 = export_master_mp3(wav or source, source.with_name(f"{source.stem}_320k.mp3"))
        print(f"[+] Master   : {wav or '(failed)'}")
        print(f"[+] 320k mp3 : {mp3 or '(failed)'}")
    if args.test:
        print("[+] " + ("TEST PASSED" if result.get("path") else "TEST FAILED"))
    return 0 if result.get("path") else 1


if __name__ == "__main__":
    raise SystemExit(main())