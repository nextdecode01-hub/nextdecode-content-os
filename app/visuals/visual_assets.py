import os, json, re, base64, hashlib, hmac, subprocess, time, urllib.request
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

PROVIDERS = ["pollinations", "gemini", "cloudflare", "fal", "replicate", "openai", "wikimedia", "local"]

POLLINATIONS_KEY = os.getenv("POLLINATIONS_API_KEY", "").strip()
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
FAL_KEY = os.getenv("FAL_KEY", "").strip()
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN", "").strip()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()
IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "").strip().lower()
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "").strip()
THUMBNAIL_PROVIDER = os.getenv("THUMBNAIL_PROVIDER", "").strip().lower()
VISUAL_PROVIDER = os.getenv("VISUAL_PROVIDER", "").strip().lower()
_SECRET_VALUES = tuple(value for value in (POLLINATIONS_KEY, GEMINI_KEY, FAL_KEY, REPLICATE_TOKEN, OPENAI_KEY) if value)


def _redact(value) -> str:
    """Strip credentials from anything headed for a log line or API response."""
    text = str(value)
    for secret in _SECRET_VALUES:
        text = text.replace(secret, "***")
    return re.sub(r"(?i)\b(key|token|api_key|access_token)=([^&\s'\"]+)", r"\1=***", text)


def _looks_like_image(data: bytes) -> bool:
    if not data or len(data) < 1024:
        return False
    return (
        data.startswith(b"\x89PNG\r\n\x1a\n")
        or data.startswith(b"\xff\xd8\xff")
        or data.startswith(b"GIF8")
        or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")
    )


def available_providers():
    # Pollinations serves keyless requests too; a key only raises its limits.
    out = ["pollinations"]
    if GEMINI_KEY: out.append("gemini")
    if os.getenv("CF_ACCOUNT_ID", "").strip() and os.getenv("CF_API_TOKEN", "").strip(): out.append("cloudflare")
    if FAL_KEY: out.append("fal")
    if REPLICATE_TOKEN: out.append("replicate")
    if OPENAI_KEY: out.append("openai")
    out.append("wikimedia")
    out.append("local")
    return out


_PROVIDER_COOLDOWN: dict[str, float] = {}


def _cool_down(provider: str, error) -> None:
    """Stop hammering a provider that is rate-limited, unpaid, or rejecting auth."""
    err = str(error)
    if re.search(r"\b(401|402|403|429)\b", err):
        _PROVIDER_COOLDOWN[provider] = time.time() + 600
    elif not re.search(r"\b(no key|missing)\b", err, re.I):
        _PROVIDER_COOLDOWN[provider] = time.time() + 60


def _chain(provider=None):
    if provider: return [provider]
    if VISUAL_PROVIDER: return [VISUAL_PROVIDER]
    head = IMAGE_PROVIDER if IMAGE_PROVIDER else None
    configured = set(available_providers())
    now = time.time()
    chain = []
    if head and head in PROVIDERS: chain.append(head)
    for p in PROVIDERS:
        if p not in chain and p in configured and _PROVIDER_COOLDOWN.get(p, 0) <= now:
            chain.append(p)
    if "local" not in chain:
        chain.append("local")
    return chain


def _download(url, out_path):
    r = requests.get(url, timeout=120); r.raise_for_status()
    content = r.content or b""
    if not _looks_like_image(content):
        raise ValueError(f"downloaded payload is not an image ({r.headers.get('Content-Type', 'unknown')}, {len(content)} bytes)")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_bytes(content)
    return str(out_path)


def _pollinations(prompt, out_path):
    import urllib.parse
    tech_anchor = "dark moody corporate technology visual, NO nature, NO plants, NO outdoors: "
    enhanced_prompt = f"{tech_anchor} {prompt}, 8k resolution, cinematic lighting, photorealistic, vertical 9:16 composition"
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(enhanced_prompt)}?width=720&height=1280&nologo=true&model=flux"
    if POLLINATIONS_KEY:
        url += f"&key={POLLINATIONS_KEY}"
    last = None
    for attempt in range(3):
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
            if r.status_code == 429:
                last = "429 rate limited"
                time.sleep(8 * (attempt + 1))
                continue
            if r.status_code in (400, 401, 402, 403, 404):
                return None, _redact(f"HTTP {r.status_code} (provider rejected the request; not retrying)")
            if r.status_code >= 500:
                last = f"HTTP {r.status_code}"
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
            if not _looks_like_image(r.content or b""):
                last = f"invalid image response ({r.headers.get('Content-Type', 'unknown')}, {len(r.content or b'')} bytes)"
                time.sleep(4)
                continue
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            Path(out_path).write_bytes(r.content)
            return str(out_path), None
        except Exception as e:
            last = _redact(e)
            time.sleep(5)
    return None, _redact(last or "pollinations failed")


def _gemini(prompt, out_path):
    if not GEMINI_KEY: return None, "no key"
    model = IMAGE_MODEL if (IMAGE_MODEL and "gemini" in IMAGE_MODEL) else "gemini-2.5-flash-image"
    def try_model(m):
        url = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s" % (m, GEMINI_KEY)
        body = {"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"responseModalities":["TEXT","IMAGE"]}}
        r = requests.post(url, json=body, timeout=120)
        return r, m
    r, model = try_model(model)
    if r.status_code == 404:
        r, model = try_model("gemini-2.0-flash-preview-image-generation")
    r.raise_for_status()
    data = r.json()
    cand = (data.get("candidates") or [{}])[0]
    parts = ((cand.get("content") or {}).get("parts")) or []
    b64 = None
    for part in parts:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("data"):
            b64 = inline.get("data"); break
    if not b64: return None, "no image part"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_bytes(base64.b64decode(b64))
    return str(out_path), None


def _fal(prompt, out_path):
    if not FAL_KEY: return None, "no key"
    model = IMAGE_MODEL if (IMAGE_MODEL and IMAGE_MODEL.startswith("fal-ai/")) else "fal-ai/flux/schnell"
    url = "https://fal.run/%s" % model
    r = requests.post(url, headers={"Authorization":"Key "+FAL_KEY}, json={"prompt":prompt,"image_size":"square_hd"}, timeout=120)
    r.raise_for_status()
    imgs = (r.json().get("images") or [])
    if not imgs: return None, "no images"
    return _download(imgs[0]["url"], out_path), None


def _replicate(prompt, out_path):
    if not REPLICATE_TOKEN: return None, "no key"
    r = requests.post("https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions", headers={"Authorization":"Bearer "+REPLICATE_TOKEN}, json={"input":{"prompt":prompt,"aspect_ratio":"9:16","output_format":"webp"}}, timeout=60)
    r.raise_for_status()
    pid = r.json()["id"]
    for _ in range(40):
        time.sleep(3)
        r = requests.get("https://api.replicate.com/v1/predictions/%s" % pid, headers={"Authorization":"Bearer "+REPLICATE_TOKEN}, timeout=60)
        r.raise_for_status()
        d = r.json()
        if d.get("status") == "succeeded":
            outs = d.get("output")
            url = outs[0] if isinstance(outs, list) else outs
            return _download(url, out_path), None
        if d.get("status") in ("failed","canceled"): return None, str(d.get("error"))
    return None, "timeout"


def _openai(prompt, out_path):
    if not OPENAI_KEY: return None, "no key"
    r = requests.post("https://api.openai.com/v1/images/generations", headers={"Authorization":"Bearer "+OPENAI_KEY}, json={"model":"gpt-image-2","prompt":prompt,"size":"1024x1536","quality":"low"}, timeout=120)
    r.raise_for_status()
    item = (r.json().get("data") or [{}])[0]
    if "b64_json" in item:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(base64.b64decode(item["b64_json"]))
        return str(out_path), None
    if "url" in item: return _download(item["url"], out_path), None
    return None, "no image"


def _cloudflare(prompt, out_path):
    account = os.getenv("CF_ACCOUNT_ID", "").strip()
    token = os.getenv("CF_API_TOKEN", "").strip()
    if not account or not token: return None, "missing CF_ACCOUNT_ID/CF_API_TOKEN key"
    model = os.getenv("CF_IMAGE_MODEL", "@cf/black-forest-labs/flux-1-schnell").strip()
    url = "https://api.cloudflare.com/client/v4/accounts/%s/ai/run/%s" % (account, model)
    r = requests.post(url, headers={"Authorization": "Bearer " + token}, json={"prompt": prompt}, timeout=120)
    r.raise_for_status()
    image_b64 = (r.json().get("result") or {}).get("image")
    if not image_b64: return None, "no image in response"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_bytes(base64.b64decode(image_b64))
    return str(out_path), None


_WIKIMEDIA_NOISE = re.compile(
    r"(?i)\b(8k|4k|resolution|cinematic|lighting|photorealistic|vertical|composition|"
    r"9:16|dark|moody|visual|aesthetic|close[- ]?up|wide|shot|scene|stock|footage|video)\b"
)


def _wikimedia_queries(prompt: str) -> list[str]:
    """Turn a long style-laden shot prompt into short Commons search phrases."""
    text = re.sub(r"\bNO\b[^,:;]*[,;]?", " ", str(prompt or ""), flags=re.I)

    def words_of(segment: str) -> list[str]:
        segment = _WIKIMEDIA_NOISE.sub(" ", segment)
        return [word for word in re.findall(r"[A-Za-z0-9]+", segment) if len(word) > 2]

    # The subject usually follows the style prefix ("...visual: boardroom at night").
    subject = words_of(text.split(":", 1)[1]) if ":" in text else []
    fallback = words_of(text)
    queries = []
    if len(subject) >= 2:
        queries.extend([" ".join(subject[:4]), " ".join(subject[:3]), " ".join(subject[:2])])
    if len(fallback) >= 2:
        queries.extend([" ".join(fallback[:4]), " ".join(fallback[:3]), " ".join(fallback[:2])])
    return list(dict.fromkeys(query for query in queries if len(query) >= 3))


def _wikimedia(prompt, out_path):
    from app.visuals import stock_fetcher
    queries = _wikimedia_queries(prompt)
    if not queries:
        return None, "no usable query"
    hits = []
    for query in queries:
        try:
            hits = stock_fetcher.search_images(query, limit=5)
        except Exception as e:
            return None, "wikimedia search failed: %s" % _redact(e)
        if hits:
            break
    if not hits:
        return None, "no wikimedia results"
    hit = hits[0]
    original = str(hit.get("url") or "")
    url = original if re.search(r"\.(jpe?g|png|webp)(\?|$)", original, re.I) else (hit.get("thumb_url") or original)
    try:
        ok = stock_fetcher.download_image(url, Path(out_path))
        if ok and not _looks_like_image(Path(out_path).read_bytes()):
            return None, "wikimedia returned a non-image payload"
    except Exception as e:
        return None, "wikimedia download failed: %s" % _redact(e)
    if not ok: return None, "wikimedia download failed"
    return str(out_path), None


def _local(prompt, out_path):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    # prompt text intentionally not drawn on the frame
    cmd = ["ffmpeg","-y","-f","lavfi","-i","color=c=0x0B1220:s=1080x1920:d=1","-frames:v","1",out_path]
    subprocess.run(cmd, check=True, capture_output=True)
    return str(out_path), None


def generate_image(prompt, out_dir, *, provider=None, aspect="9:16", size=None):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(str(prompt).encode("utf-8")).hexdigest()[:12]
    out_path = str(out_dir / f"image_{digest}.png")

    last_err = None
    for p in _chain(provider):
        try:
            if p == "pollinations": path, err = _pollinations(prompt, out_path)
            elif p == "gemini": path, err = _gemini(prompt, out_path)
            elif p == "cloudflare": path, err = _cloudflare(prompt, out_path)
            elif p == "fal": path, err = _fal(prompt, out_path)
            elif p == "replicate": path, err = _replicate(prompt, out_path)
            elif p == "openai": path, err = _openai(prompt, out_path)
            elif p == "wikimedia": path, err = _wikimedia(prompt, out_path)
            elif p == "local": path, err = _local(prompt, out_path)
            else: path, err = None, "unknown provider"
            if path: return {"path":path,"provider":p,"url":None,"error":None}
            last_err = _redact(err)
            _cool_down(p, last_err)
            print(f"[visual] provider '{p}' skipped: {last_err}")
        except Exception as e:
            last_err = _redact(e)
            _cool_down(p, last_err)
            print(f"[visual] provider '{p}' failed: {last_err}")
    return {"path":None,"provider":(provider or "none"),"url":None,"error":last_err or "all failed"}


def remove_background(image_path, out_dir):
    if not FAL_KEY: return {"path":None,"provider":"fal","error":"FAL_KEY missing"}
    return {"path":None,"provider":"fal","error":"optional: requires hosted image url; not implemented for local files"}


def generate_thumbnail(prompt, title, out_path, *, provider=None):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    try:
        text = title.replace(":","\\:").replace("'","\\'").replace(",","\\,").replace("%","\\%")
        cmd = ["ffmpeg","-y","-f","lavfi","-i","color=c=0x1a1a2e:s=1280x720:d=1","-vf","drawtext=text='%s':fontcolor=yellow:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2" % text,"-frames:v","1",out_path]
        subprocess.run(cmd, check=True, capture_output=True)
        return {"path":str(out_path),"provider":"local","error":None}
    except Exception as e:
        return {"path":None,"provider":"local","error":str(e)}


def thumbnail_text_suggestions(script_json):
    try:
        from app.providers.multi_model_ai import generate_json
        prompt = "Propose 3 punchy thumbnail text options (max 5 words each) JSON list for: " + json.dumps(script_json)
        res = generate_json(prompt, 0.7, 60)
        if isinstance(res, list): return [str(x) for x in res][:3]
        if isinstance(res, dict):
            for k in ("options","texts","suggestions","titles"):
                if k in res and isinstance(res[k], list): return [str(x) for x in res[k]][:3]
            return [str(v) for v in list(res.values())[:3]]
    except Exception:
        pass
    return []


def ensure_public_url(video_path):
    if os.getenv("INSTAGRAM_VIDEO_URL"):
        return os.getenv("INSTAGRAM_VIDEO_URL")
    cn = os.getenv("CLOUDINARY_CLOUD_NAME"); ck = os.getenv("CLOUDINARY_API_KEY"); cs = os.getenv("CLOUDINARY_API_SECRET")
    su = os.getenv("SUPABASE_URL"); sk = os.getenv("SUPABASE_SERVICE_KEY")
    if not (cn and ck and cs) and not (su and sk):
        print("Set INSTAGRAM_VIDEO_URL or a storage provider key (Cloudinary/R2/Supabase) to publish to Instagram.")
    return None


def list_providers():
    for p in PROVIDERS:
        print("%s: %s" % (p, "yes" if p in available_providers() else "no"))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--generate")
    ap.add_argument("--out")
    ap.add_argument("--provider")
    ap.add_argument("--thumbnail")
    ap.add_argument("--remove-bg")
    ap.add_argument("--public-url")
    args = ap.parse_args()
    if args.list:
        list_providers(); return
    if args.generate:
        out = args.out or "/home/demon/shorts_studio/outputs/media/test.png"
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        res = generate_image(args.generate, str(Path(out).parent), provider=args.provider)
        if res["path"] and res["path"] != out:
            try: Path(res["path"]).rename(out)
            except Exception: pass
        print(res); return
    if args.thumbnail:
        out = args.out or "/home/demon/shorts_studio/outputs/media/thumb.jpg"
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        print(generate_thumbnail(args.thumbnail, args.thumbnail, out, provider=args.provider)); return
    if args.remove_bg:
        out_dir = str(Path(args.out).parent) if args.out else "/home/demon/shorts_studio/outputs/media"
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        print(remove_background(args.remove_bg, out_dir)); return
    if args.public_url:
        print(ensure_public_url(args.public_url)); return

if __name__ == "__main__":
    main()
