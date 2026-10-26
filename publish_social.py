"""publish_social.py - Free/low-friction social publishing adapters."""
from __future__ import annotations
import hashlib, json, os, time
from pathlib import Path
from datetime import datetime, timezone
import requests

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "social_upload_ledger.json"
PLATFORMS = {}
_META_VERSION = os.getenv("META_GRAPH_API_VERSION", "v19.0").strip() or "v19.0"
_bsky_session = {}
_reddit_token = {}

def _env(k):
    return os.getenv(k, "").strip()

def _result(platform, ok, post_id=None, url=None, error=None):
    return {"platform": platform, "ok": bool(ok), "post_id": post_id, "url": url, "error": error}

def resolve_public_url(video_path):
    v = _env("INSTAGRAM_VIDEO_URL")
    if v:
        return v
    try:
        import visual_assets
        return visual_assets.ensure_public_url(str(video_path))
    except Exception:
        return None

def _cfg(keys):
    return all(_env(k) for k in keys)

def _fingerprint(platform, caption, video_path):
    h = hashlib.sha256()
    h.update(platform.encode())
    h.update(caption.strip().lower().encode())
    try:
        vh = hashlib.sha256(Path(video_path).read_bytes()).hexdigest()
    except Exception:
        vh = str(video_path)
    h.update(vh.encode())
    return h.hexdigest()

def _ledger():
    try:
        return json.loads(LEDGER.read_text()) if LEDGER.exists() else {}
    except Exception:
        return {}

def _ledger_save(d):
    try:
        LEDGER.write_text(json.dumps(d, indent=2))
    except Exception:
        pass

def _already(platform, fp):
    d = _ledger()
    return (d.get(fp, {}).get(platform)) is not None

def _record(platform, fp, post_id, url):
    d = _ledger()
    d.setdefault(fp, {})[platform] = {"post_id": post_id, "url": url, "ts": datetime.now(timezone.utc).isoformat()}
    _ledger_save(d)

def available_platforms():
    out = []
    for n, a in PLATFORMS.items():
        missing = [k for k in a["requires"] if not _env(k)]
        out.append({"name": n, "configured": a["configured"](), "missing_keys": missing, "capabilities": a["capabilities"]})
    return out

def list_platforms():
    for entry in available_platforms():
        print(f"{entry['name']}: configured={entry['configured']} missing={entry['missing_keys']} caps={entry['capabilities']}")

def _not_configured(name):
    return _result(name, False, error=f"{name} not configured")

def _make(name, requires, caps, configured_fn, publish_fn):
    PLATFORMS[name] = {"name": name, "requires": requires, "capabilities": caps,
                       "configured": configured_fn, "publish": publish_fn}

def _missing_url_msg(name):
    return f"{name} requires a public media URL (set INSTAGRAM_VIDEO_URL or configure Cloudinary/Supabase/R2)"

def _meta_base():
    return f"https://graph.facebook.com/{_env('META_GRAPH_API_VERSION') or _META_VERSION}"

def create_reel_container(ig_user_id, access_token, public_url, caption):
    base = _meta_base()
    r = requests.post(f"{base}/{ig_user_id}/media",
                      data={"media_type": "REELS", "video_url": public_url, "caption": caption, "share_to_feed": "true"},
                      headers={"Authorization": f"Bearer {access_token}"}, timeout=45)
    r.raise_for_status()
    cid = r.json().get("id")
    if not cid:
        raise RuntimeError("Meta did not return a media container.")
    deadline = time.time() + 180
    status_code = "IN_PROGRESS"
    while time.time() < deadline:
        s = requests.get(f"{base}/{cid}", params={"fields": "status_code"}, headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
        s.raise_for_status()
        status_code = s.json().get("status_code", "")
        if status_code == "FINISHED":
            break
        if status_code in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Media processing ended with {status_code}.")
        time.sleep(5)
    if status_code != "FINISHED":
        raise RuntimeError("Media processing timed out.")
    return cid

def _instagram_publish(video_path, caption, title=None, public_url=None, **kw):
    name = "instagram"
    if not _cfg(["INSTAGRAM_USER_ID", "INSTAGRAM_ACCESS_TOKEN"]):
        return _not_configured(name)
    if not public_url:
        public_url = resolve_public_url(video_path)
    if not public_url:
        return _result(name, False, error=_missing_url_msg(name))
    ig_user_id = _env("INSTAGRAM_USER_ID")
    token = _env("INSTAGRAM_ACCESS_TOKEN")
    try:
        cid = create_reel_container(ig_user_id, token, public_url, caption)
        base = _meta_base()
        r = requests.post(f"{base}/{ig_user_id}/media_publish", data={"creation_id": cid, "access_token": token}, timeout=45)
        r.raise_for_status()
        mid = r.json().get("id")
        return _result(name, True, post_id=mid, url=f"https://www.instagram.com/reel/{mid}/" if mid else None)
    except Exception as e:
        return _result(name, False, error=str(e))

def _threads_publish(video_path, caption, title=None, public_url=None, **kw):
    name = "threads"
    if not _cfg(["THREADS_USER_ID", "THREADS_ACCESS_TOKEN"]):
        return _not_configured(name)
    if not public_url:
        public_url = resolve_public_url(video_path)
    if not public_url:
        return _result(name, False, error=_missing_url_msg(name))
    user_id = _env("THREADS_USER_ID")
    token = _env("THREADS_ACCESS_TOKEN")
    version = _env("META_GRAPH_API_VERSION") or _META_VERSION
    try:
        ig_user = _env("INSTAGRAM_USER_ID") or user_id
        try:
            cid = create_reel_container(ig_user, token, public_url, caption)
        except Exception:
            r = requests.post(f"https://graph.threads.net/{version}/{user_id}/threads",
                              data={"media_type": "REELS", "video_url": public_url, "text": caption, "access_token": token}, timeout=45)
            r.raise_for_status()
            cid = r.json().get("id")
        r = requests.post(f"https://graph.threads.net/{version}/{user_id}/threads",
                          data={"media_type": "REELS", "media_id": cid, "text": caption, "access_token": token}, timeout=45)
        r.raise_for_status()
        tid = r.json().get("id")
        return _result(name, True, post_id=tid, url=None)
    except Exception as e:
        return _result(name, False, error=str(e))

def _mastodon_publish(video_path, caption, title=None, public_url=None, **kw):
    name = "mastodon"
    if not _cfg(["MASTODON_BASE_URL", "MASTODON_ACCESS_TOKEN"]):
        return _not_configured(name)
    base = _env("MASTODON_BASE_URL").rstrip("/")
    token = _env("MASTODON_ACCESS_TOKEN")
    try:
        with open(video_path, "rb") as f:
            r = requests.post(f"{base}/api/v2/media", headers={"Authorization": f"Bearer {token}"},
                              files={"file": (Path(video_path).name, f, "video/mp4")}, timeout=120)
        r.raise_for_status()
        mid = r.json().get("id")
        r2 = requests.post(f"{base}/api/v1/statuses", headers={"Authorization": f"Bearer {token}"},
                           json={"status": caption, "media_ids": [mid]}, timeout=45)
        r2.raise_for_status()
        sid = r2.json().get("id")
        url = r2.json().get("url")
        return _result(name, True, post_id=sid, url=url)
    except Exception as e:
        return _result(name, False, error=str(e))

def _discord_publish(video_path, caption, title=None, public_url=None, **kw):
    name = "discord"
    if not _cfg(["DISCORD_WEBHOOK_URL"]):
        return _not_configured(name)
    wh = _env("DISCORD_WEBHOOK_URL")
    p = Path(video_path)
    if p.exists() and p.stat().st_size > 25 * 1024 * 1024:
        return _result(name, False, error="discord: file exceeds 25MB cap")
    try:
        payload = json.dumps({"content": caption})
        with open(video_path, "rb") as f:
            r = requests.post(wh, data={"payload_json": payload}, files={"files[0]": (p.name, f, "video/mp4")}, timeout=120)
        if r.status_code in (200, 204):
            return _result(name, True, post_id="ok", url=None)
        r.raise_for_status()
        return _result(name, True, post_id="ok", url=None)
    except Exception as e:
        return _result(name, False, error=str(e))

_reddit_token = {}

def _reddit_token_get():
    if "token" in _reddit_token and _reddit_token.get("expires", 0) > time.time():
        return _reddit_token["token"]
    cid = _env("REDDIT_CLIENT_ID"); secret = _env("REDDIT_CLIENT_SECRET")
    ua = _env("REDDIT_USER_AGENT") or "shorts-studio/1.0"
    r = requests.post("https://www.reddit.com/api/v1/access_token",
                      auth=(cid, secret), data={"grant_type": "client_credentials"},
                      headers={"User-Agent": ua}, timeout=30)
    r.raise_for_status()
    tok = r.json().get("access_token")
    _reddit_token["token"] = tok
    _reddit_token["expires"] = time.time() + r.json().get("expires_in", 3600) - 60
    return tok

def _reddit_publish(video_path, caption, title=None, public_url=None, link=False, **kw):
    name = "reddit"
    if not _cfg(["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_SUBREDDIT"]):
        return _not_configured(name)
    subreddit = _env("REDDIT_SUBREDDIT")
    ua = _env("REDDIT_USER_AGENT") or "shorts-studio/1.0"
    try:
        tok = _reddit_token_get()
    except Exception:
        _reddit_token.clear()
        try:
            tok = _reddit_token_get()
        except Exception as e2:
            return _result(name, False, error=str(e2))
    t = title or (caption[:290] if caption else "short")
    try:
        if link and public_url:
            data = {"sr": subreddit, "kind": "link", "title": t, "url": public_url, "nsfw": False, "resubmit": True, "api_type": "json"}
        else:
            data = {"sr": subreddit, "kind": "video", "title": t, "text": caption, "nsfw": False, "resubmit": True, "api_type": "json"}
        r = requests.post("https://oauth.reddit.com/api/submit", headers={"Authorization": f"Bearer {tok}", "User-Agent": ua},
                          data=data, timeout=45)
        if r.status_code == 401:
            _reddit_token.clear()
            tok = _reddit_token_get()
            r = requests.post("https://oauth.reddit.com/api/submit", headers={"Authorization": f"Bearer {tok}", "User-Agent": ua},
                              data=data, timeout=45)
        r.raise_for_status()
        j = r.json()
        post_id = None
        url = None
        if isinstance(j, dict):
            d = j.get("json", {}).get("data", {}) if isinstance(j.get("json"), dict) else {}
            post_id = d.get("id") or d.get("name")
            url = d.get("url")
        return _result(name, True, post_id=post_id, url=url)
    except Exception as e:
        return _result(name, False, error=str(e))

def _pinterest_publish(video_path, caption, title=None, public_url=None, **kw):
    name = "pinterest"
    if not _cfg(["PINTEREST_ACCESS_TOKEN", "PINTEREST_BOARD_ID"]):
        return _not_configured(name)
    token = _env("PINTEREST_ACCESS_TOKEN")
    board_id = _env("PINTEREST_BOARD_ID")
    t = title or "short"
    try:
        p = Path(video_path)
        if p.exists():
            r = requests.post("https://api.pinterest.com/v5/videos", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"},
                              data=p.read_bytes(), timeout=120)
            r.raise_for_status()
            vid = r.json().get("id")
            body = {"board_id": board_id, "media_source": {"source_type": "video_upload", "video_upload_id": vid},
                    "title": t, "description": caption}
        else:
            if not public_url:
                return _result(name, False, error=_missing_url_msg(name))
            body = {"board_id": board_id, "media_source": {"source_type": "image_url", "url": public_url},
                    "title": t, "description": caption, "link": public_url}
        r2 = requests.post("https://api.pinterest.com/v5/pins", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                           json=body, timeout=45)
        r2.raise_for_status()
        pid = r2.json().get("id")
        return _result(name, True, post_id=pid, url=f"https://www.pinterest.com/pin/{pid}/" if pid else None)
    except Exception as e:
        return _result(name, False, error=str(e))

def _gbp_publish(video_path, caption, title=None, public_url=None, **kw):
    name = "gbp"
    if not _cfg(["GBP_ACCESS_TOKEN", "GBP_LOCATION_ID"]):
        return _not_configured(name)
    if not public_url:
        public_url = resolve_public_url(video_path)
    if not public_url:
        return _result(name, False, error=_missing_url_msg(name))
    token = _env("GBP_ACCESS_TOKEN")
    loc = _env("GBP_LOCATION_ID")
    try:
        r = requests.post(f"https://mybusiness.googleapis.com/v4/{loc}/localPosts",
                          headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                          json={"languageCode": "en-US", "summary": caption, "media": [{"mediaFormat": "VIDEO", "sourceUrl": public_url}], "topicType": "STANDARD"},
                          timeout=45)
        r.raise_for_status()
        pid = r.json().get("name") or r.json().get("id")
        return _result(name, True, post_id=pid, url=None)
    except Exception as e:
        return _result(name, False, error=str(e))

def _whatsapp_publish(video_path, caption, title=None, public_url=None, **kw):
    name = "whatsapp"
    if not _cfg(["WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_ACCESS_TOKEN", "WHATSAPP_RECIPIENT"]):
        return _not_configured(name)
    phone_id = _env("WHATSAPP_PHONE_NUMBER_ID")
    token = _env("WHATSAPP_ACCESS_TOKEN")
    recipient = _env("WHATSAPP_RECIPIENT")
    try:
        with open(video_path, "rb") as f:
            r = requests.post(f"https://graph.facebook.com/v18.0/{phone_id}/media",
                              headers={"Authorization": f"Bearer {token}"},
                              files={"file": (Path(video_path).name, f, "video/mp4")},
                              data={"type": "video/mp4", "messaging_product": "whatsapp"}, timeout=120)
        r.raise_for_status()
        media_id = r.json().get("id")
        r2 = requests.post(f"https://graph.facebook.com/v18.0/{phone_id}/messages",
                           headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                           json={"messaging_product": "whatsapp", "recipient_type": "individual", "to": recipient,
                                 "type": "video", "video": {"id": media_id, "caption": caption}}, timeout=45)
        r2.raise_for_status()
        mid = None
        j2 = r2.json()
        if isinstance(j2.get("messages"), list) and j2["messages"]:
            mid = j2["messages"][0].get("id")
        else:
            mid = j2.get("id")
        return _result(name, True, post_id=mid, url=None)
    except Exception as e:
        return _result(name, False, error=str(e))

def _telegram_publish(video_path, caption, title=None, public_url=None, **kw):
    name = "telegram"
    if not _cfg(["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]):
        return _not_configured(name)
    token = _env("TELEGRAM_BOT_TOKEN")
    chat_id = _env("TELEGRAM_CHAT_ID")
    p = Path(video_path)
    if p.exists() and p.stat().st_size > 50 * 1024 * 1024:
        return _result(name, False, error="telegram: file exceeds 50MB cap")
    try:
        with open(video_path, "rb") as f:
            r = requests.post(f"https://api.telegram.org/bot{token}/sendVideo",
                              data={"chat_id": chat_id, "caption": caption, "supports_streaming": "true"},
                              files={"video": (p.name, f, "video/mp4")}, timeout=180)
        r.raise_for_status()
        mid = r.json().get("result", {}).get("message_id")
        return _result(name, True, post_id=mid, url=None)
    except Exception as e:
        return _result(name, False, error=str(e))

def _uploadpost_publish(video_path, caption, title=None, public_url=None, **kw):
    name = "uploadpost"
    if not _cfg(["UPLOAD_POST_API_KEY", "UPLOAD_POST_PROFILE"]):
        return _not_configured(name)
    if not public_url:
        public_url = resolve_public_url(video_path)
    if not public_url:
        return _result(name, False, error=_missing_url_msg(name))
    key = _env("UPLOAD_POST_API_KEY")
    profile = _env("UPLOAD_POST_PROFILE")
    t = title or "short"
    try:
        r = requests.post("https://api.upload-post.com/api/upload",
                          headers={"Authorization": key, "Content-Type": "application/json"},
                          json={"user": profile, "platforms": ["tiktok", "instagram", "youtube"],
                                "content": [{"type": "video", "url": public_url, "title": t, "description": caption}]},
                          timeout=60)
        r.raise_for_status()
        j = r.json()
        pid = j.get("id") or j.get("post_id")
        return _result(name, True, post_id=pid, url=j.get("url"))
    except Exception as e:
        return _result(name, False, error=str(e))

def _relayapi_publish(video_path, caption, title=None, public_url=None, **kw):
    name = "relayapi"
    if not _cfg(["RELAY_API_KEY"]):
        return _not_configured(name)
    if not public_url:
        public_url = resolve_public_url(video_path)
    if not public_url:
        return _result(name, False, error=_missing_url_msg(name))
    key = _env("RELAY_API_KEY")
    t = title or "short"
    try:
        r = requests.post("https://api.relayapi.dev/v1/posts",
                          headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                          json={"platforms": ["instagram", "tiktok", "youtube"],
                                "content": [{"type": "video", "url": public_url, "title": t, "description": caption}]},
                          timeout=60)
        r.raise_for_status()
        j = r.json()
        pid = j.get("id") or j.get("post_id")
        return _result(name, True, post_id=pid, url=j.get("url"))
    except Exception as e:
        return _result(name, False, error=str(e))

_bsky_session = {}

def _bsky_publish(video_path, caption, title=None, public_url=None, **kw):
    name = "bluesky"
    if not _cfg(["BLUESKY_IDENTIFIER", "BLUESKY_APP_PASSWORD"]):
        return _not_configured(name)
    ident = _env("BLUESKY_IDENTIFIER"); pw = _env("BLUESKY_APP_PASSWORD")
    text = caption
    if public_url:
        text = f"{caption}\n{public_url}"
    try:
        if "jwt" not in _bsky_session:
            r = requests.post("https://bsky.social/xrpc/com.atproto.server.createSession",
                              json={"identifier": ident, "password": pw}, timeout=30)
            r.raise_for_status()
            d = r.json()
            _bsky_session["jwt"] = d["accessJwt"]; _bsky_session["did"] = d["did"]
        jwt = _bsky_session["jwt"]; did = _bsky_session["did"]
        r2 = requests.post("https://bsky.social/xrpc/com.atproto.repo.createRecord",
                           headers={"Authorization": f"Bearer {jwt}"},
                           json={"repo": did, "collection": "app.bsky.feed.post",
                                 "record": {"$type": "app.bsky.feed.post", "text": text,
                                            "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                                            "langs": ["en"]}}, timeout=30)
        if r2.status_code == 401:
            _bsky_session.clear()
            r = requests.post("https://bsky.social/xrpc/com.atproto.server.createSession",
                              json={"identifier": ident, "password": pw}, timeout=30)
            r.raise_for_status()
            d = r.json()
            _bsky_session["jwt"] = d["accessJwt"]; _bsky_session["did"] = d["did"]
            jwt = _bsky_session["jwt"]; did = _bsky_session["did"]
            r2 = requests.post("https://bsky.social/xrpc/com.atproto.repo.createRecord",
                               headers={"Authorization": f"Bearer {jwt}"},
                               json={"repo": did, "collection": "app.bsky.feed.post",
                                     "record": {"$type": "app.bsky.feed.post", "text": text,
                                                "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                                                "langs": ["en"]}}, timeout=30)
        r2.raise_for_status()
        rec = r2.json()
        return _result(name, True, post_id=rec.get("cid"), url=rec.get("uri"))
    except Exception as e:
        return _result(name, False, error=str(e))

_OTHERS = {
    "threads": (["THREADS_USER_ID", "THREADS_ACCESS_TOKEN"], ["video"]),
    "mastodon": (["MASTODON_BASE_URL", "MASTODON_ACCESS_TOKEN"], ["video"]),
    "discord": (["DISCORD_WEBHOOK_URL"], ["video"]),
    "reddit": (["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_SUBREDDIT"], ["video", "link"]),
    "pinterest": (["PINTEREST_ACCESS_TOKEN", "PINTEREST_BOARD_ID"], ["video", "image"]),
    "gbp": (["GBP_ACCESS_TOKEN", "GBP_LOCATION_ID"], ["video"]),
    "whatsapp": (["WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_ACCESS_TOKEN", "WHATSAPP_RECIPIENT"], ["video"]),
    "telegram": (["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"], ["video"]),
    "uploadpost": (["UPLOAD_POST_API_KEY", "UPLOAD_POST_PROFILE"], ["video"]),
    "relayapi": (["RELAY_API_KEY"], ["video"]),
    "instagram": (["INSTAGRAM_USER_ID", "INSTAGRAM_ACCESS_TOKEN"], ["video"]),
    "bluesky": (["BLUESKY_IDENTIFIER", "BLUESKY_APP_PASSWORD"], ["text", "video"]),
}

_PUBMAP = {
    "threads": _threads_publish, "mastodon": _mastodon_publish, "discord": _discord_publish,
    "reddit": _reddit_publish, "pinterest": _pinterest_publish, "gbp": _gbp_publish,
    "whatsapp": _whatsapp_publish, "telegram": _telegram_publish, "uploadpost": _uploadpost_publish,
    "relayapi": _relayapi_publish, "instagram": _instagram_publish, "bluesky": _bsky_publish,
}

for n, (keys, caps) in _OTHERS.items():
    _make(n, keys, caps, (lambda k: (lambda: _cfg(k)))(keys), _PUBMAP[n])

def publish(platform, video_path, caption, title=None, hashtags=None, public_url=None, dry_run=False):
    if dry_run:
        return _result(platform, True, post_id="DRY_RUN", url=None, error=None)
    if platform not in PLATFORMS:
        return _result(platform, False, error="unknown platform")
    if not PLATFORMS[platform]["configured"]():
        return _result(platform, False, error=f"{platform} not configured")
    fp = _fingerprint(platform, caption, video_path)
    if _already(platform, fp):
        return _result(platform, False, error="duplicate (ledger)")
    adapter = PLATFORMS[platform]["publish"]
    res = adapter(video_path=video_path, caption=caption, title=title, public_url=public_url)
    if res.get("ok"):
        _record(platform, fp, res.get("post_id"), res.get("url"))
    return res

def publish_all_social(video_path, caption, title=None, platforms=None, hashtags=None,
                       allow_partial=True, require_approval=True, dry_run=True):
    if require_approval:
        try:
            import approval_integrity
            approval_file = ROOT / "review_approved.json"
            approval = json.loads(approval_file.read_text()) if approval_file.exists() else {}
            err = None
            try:
                import publish_all as _pa
                err = _pa.approval_matches_current_content()
            except Exception:
                err = None
            if err:
                return {"results": [], "published": 0, "failed": 0, "skipped": 0, "error": err}
            if not approval or not approval_integrity.approved_today(approval.get("approved_at")):
                return {"results": [], "published": 0, "failed": 0, "skipped": 0, "error": "approval required (run approve_review.py)"}
        except Exception as e:
            return {"results": [], "published": 0, "failed": 0, "skipped": 0, "error": str(e)}
    pu = resolve_public_url(video_path)
    targets = platforms if platforms else list(PLATFORMS.keys())
    results = []
    published = failed = skipped = 0
    for p in targets:
        if p not in PLATFORMS:
            skipped += 1
            continue
        if not PLATFORMS[p]["configured"]():
            skipped += 1
            results.append(_result(p, False, error="not configured"))
            continue
        r = publish(p, video_path, caption, title=title, hashtags=hashtags, public_url=pu, dry_run=dry_run)
        results.append(r)
        if r["ok"]:
            published += 1
        else:
            failed += 1
            if not allow_partial:
                break
    return {"results": results, "published": published, "failed": failed, "skipped": skipped}

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--publish")
    ap.add_argument("--caption", default="")
    ap.add_argument("--title", default=None)
    ap.add_argument("--platforms", default=None)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--resolve-url")
    args = ap.parse_args()
    if args.list:
        list_platforms()
        return
    if args.resolve_url:
        print(resolve_public_url(args.resolve_url))
        return
    if args.publish:
        plats = [x.strip() for x in args.platforms.split(",")] if args.platforms else None
        dry_run = not args.execute
        out = publish_all_social(args.publish, args.caption, title=args.title, platforms=plats,
                                 require_approval=False, allow_partial=True, dry_run=dry_run)
        print(json.dumps(out, indent=2, default=str))
        return

if __name__ == "__main__":
    main()