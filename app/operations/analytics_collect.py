from __future__ import annotations
import os, json, argparse, datetime, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=True)
HISTORY = ROOT / "data" / "analytics_history.json"
LATEST = ROOT / "data" / "analytics_latest.json"

def env(name):
    v = os.getenv(name, "").strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        v = v[1:-1].strip()
    return v

def _req(method, url, headers=None, data=None, timeout=30):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8","replace")
            try: return r.status, json.loads(raw) if raw else {}, None
            except: return r.status, raw, None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8","replace")
        try: return e.code, json.loads(body), body
        except: return e.code, None, body
    except Exception as e:
        return 0, None, str(e)

SOURCES = ["youtube_analytics","youtube_data","meta_insights","ga4","local"]

def available_sources():
    out = []
    out.append({"name":"youtube_analytics","configured": bool(env("YOUTUBE_CLIENT_ID") and env("YOUTUBE_CLIENT_SECRET") and Path(ROOT/"youtube_token.json").exists()), "missing_keys": [k for k in ["YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET"] if not env(k)] + (["youtube_token.json"] if not (ROOT/"youtube_token.json").exists() else [])})
    out.append({"name":"youtube_data","configured": bool(env("YOUTUBE_DATA_API_KEY")), "missing_keys": [] if env("YOUTUBE_DATA_API_KEY") else ["YOUTUBE_DATA_API_KEY"]})
    out.append({"name":"meta_insights","configured": bool(env("INSTAGRAM_ACCESS_TOKEN") or env("FACEBOOK_PAGE_ACCESS_TOKEN")), "missing_keys": []})
    out.append({"name":"ga4","configured": bool(env("GA4_ACCESS_TOKEN") or env("GA4_SERVICE_ACCOUNT_JSON")), "missing_keys": [] if (env("GA4_ACCESS_TOKEN") or env("GA4_SERVICE_ACCOUNT_JSON")) else ["GA4_ACCESS_TOKEN or GA4_SERVICE_ACCOUNT_JSON"]})
    out.append({"name":"local","configured": True, "missing_keys": []})
    return out

# YouTube token refresh cache
_YT_TOKEN = {"access": None, "exp": 0}
def yt_access_token():
    if _YT_TOKEN["access"] and time.time() < _YT_TOKEN["exp"]:
        return _YT_TOKEN["access"], None
    if not Path(ROOT/"youtube_token.json").exists():
        return None, "youtube_token.json missing"
    td = json.loads((ROOT/"youtube_token.json").read_text())
    rt = td.get("refresh_token")
    cid = env("YOUTUBE_CLIENT_ID"); csec = env("YOUTUBE_CLIENT_SECRET")
    if not (rt and cid and csec):
        return None, "missing refresh_token/client creds"
    data = urllib.parse.urlencode({"client_id": cid, "client_secret": csec, "refresh_token": rt, "grant_type": "refresh_token"}).encode()
    st, resp, err = _req("POST", "https://oauth2.googleapis.com/token", headers={"Content-Type":"application/x-www-form-urlencoded"}, data=data)
    if st == 200 and isinstance(resp, dict) and resp.get("access_token"):
        _YT_TOKEN["access"] = resp["access_token"]
        _YT_TOKEN["exp"] = time.time() + int(resp.get("expires_in", 3600)) - 60
        return _YT_TOKEN["access"], None
    # surface scope hint
    msg = err or str(resp)
    if "insufficient" in msg.lower() or "403" in msg or st == 403:
        msg += " | HINT: ensure OAuth token has yt-analytics.readonly scope (add in Google Cloud Console and re-consent)"
    return None, msg

def collect_youtube_analytics(days=30):
    tok, err = yt_access_token()
    if err:
        return {"ok": False, "error": err}
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    url = ("https://youtubeanalytics.googleapis.com/v2/reports?ids=channel==MINE"
           f"&startDate={start.isoformat()}&endDate={end.isoformat()}"
           "&metrics=views,estimatedMinutesWatched,subscribersGained,likes,comments,impressions,ctr,averageViewDuration"
           "&dimensions=day&sort=day")
    st, data, e = _req("GET", url, headers={"Authorization": f"Bearer {tok}"})
    if st != 200:
        msg = e or str(data)
        if st == 403:
            msg += " | HINT: token likely lacks yt-analytics.readonly scope; add scope in Google Cloud Console and re-consent"
        return {"ok": False, "error": msg, "status": st}
    # parse
    rows = data.get("rows", []) if isinstance(data, dict) else []
    cols = [c.get("name") for c in data.get("columnHeaders", [])] if isinstance(data, dict) else []
    daily = []
    totals = {}
    for r in rows:
        d = dict(zip(cols, r))
        daily.append(d)
        for k, v in d.items():
            if k != "day" and isinstance(v, (int, float)):
                totals[k] = totals.get(k, 0) + v
    return {"ok": True, "totals": totals, "daily": daily, "columnHeaders": cols}

def collect_youtube_data(video_id=None, days=30):
    key = env("YOUTUBE_DATA_API_KEY")
    if not key:
        return {"ok": False, "error": "YOUTUBE_DATA_API_KEY missing"}
    if not video_id:
        return {"ok": True, "note": "pass video_id for per-video stats", "example": "collect('youtube_data') with video_id in record"}
    st, data, e = _req("GET", f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={key}")
    if st != 200:
        return {"ok": False, "error": e or str(data)}
    items = data.get("items", []) if isinstance(data, dict) else []
    if not items:
        return {"ok": False, "error": "video not found"}
    return {"ok": True, "statistics": items[0].get("statistics", {})}

def _meta_rate():
    # simple per-hour counter stored in file
    p = ROOT / "data" / "meta_rate_counter.json"
    now = time.time()
    if p.exists():
        d = json.loads(p.read_text())
    else:
        d = {"calls": [], "hour_start": now}
    d["calls"] = [c for c in d["calls"] if now - c < 3600]
    if len(d["calls"]) >= 30:
        return False, f"IG insights rate limit reached ({len(d['calls'])}/30 per hour)"
    d["calls"].append(now)
    p.write_text(json.dumps(d))
    return True, None

def collect_meta(days=30):
    ver = env("META_GRAPH_API_VERSION") or "v19.0"
    ig_user = env("INSTAGRAM_USER_ID"); ig_tok = env("INSTAGRAM_ACCESS_TOKEN")
    fb_page = env("FACEBOOK_PAGE_ID"); fb_tok = env("FACEBOOK_PAGE_ACCESS_TOKEN") or ig_tok
    out = {}
    # IG insights
    if ig_user and ig_tok:
        ok, msg = _meta_rate()
        if not ok:
            out["instagram_insights"] = {"ok": False, "error": msg}
        else:
            st, data, e = _req("GET", f"https://graph.facebook.com/{ver}/{ig_user}/insights?metric=reach,views,plays,saved,shares,comments&period=day&access_token={ig_tok}")
            out["instagram_insights"] = {"ok": st==200, "data": data if st==200 else None, "error": None if st==200 else (e or str(data))}
        # media list
        st, data, e = _req("GET", f"https://graph.facebook.com/{ver}/{ig_user}/media?fields=id,caption,media_type,permalink,timestamp,like_count,comments_count&access_token={ig_tok}")
        out["instagram_media"] = {"ok": st==200, "data": data if st==200 else None, "error": None if st==200 else (e or str(data))}
    else:
        out["instagram"] = {"ok": False, "error": "missing IG creds"}
    if fb_page and fb_tok:
        st, data, e = _req("GET", f"https://graph.facebook.com/{ver}/{fb_page}/insights?metric=post_impressions,post_clicks&period=day&access_token={fb_tok}")
        out["facebook_page"] = {"ok": st==200, "data": data if st==200 else None, "error": None if st==200 else (e or str(data))}
    return {"ok": any(v.get("ok") for v in out.values() if isinstance(v, dict)), "sources": out}

def ga4_access_token_from_service_account():
    sa = env("GA4_SERVICE_ACCOUNT_JSON")
    if not sa:
        return None, "GA4_SERVICE_ACCOUNT_JSON not set"
    # RS256 signing requires cryptography; stdlib alone cannot do it.
    return None, "RS256 service-account JWT signing is not possible with stdlib alone. Run: gcloud auth print-access-token and set GA4_ACCESS_TOKEN."

def collect_ga4(days=30):
    tok = env("GA4_ACCESS_TOKEN")
    if not tok and env("GA4_SERVICE_ACCOUNT_JSON"):
        tok, err = ga4_access_token_from_service_account()
        if err:
            return {"ok": False, "error": err}
    if not tok:
        return {"ok": False, "error": "GA4_ACCESS_TOKEN missing"}
    prop = env("GA4_MEASUREMENT_ID")
    if not prop:
        return {"ok": False, "error": "GA4_MEASUREMENT_ID missing"}
    body = json.dumps({"dateRanges":[{"startDate":"30daysAgo","endDate":"today"}],"dimensions":[{"name":"day"}],"metrics":[{"name":"screenPageViews"},{"name":"sessions"},{"name":"engagementRate"}]}).encode()
    st, data, e = _req("POST", f"https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport", headers={"Authorization": f"Bearer {tok}", "Content-Type":"application/json"}, data=body)
    if st != 200:
        return {"ok": False, "error": e or str(data)}
    return {"ok": True, "report": data}

def store_record(source, metrics):
    hist = []
    if HISTORY.exists():
        try: hist = json.loads(HISTORY.read_text())
        except: hist = []
    entry = {"collected_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "source": source, "metrics": metrics}
    hist.append(entry)
    HISTORY.write_text(json.dumps(hist, indent=2))
    # latest
    latest = {}
    if LATEST.exists():
        try: latest = json.loads(LATEST.read_text())
        except: latest = {}
    latest[source] = entry
    LATEST.write_text(json.dumps(latest, indent=2))
    return {"ok": True, "stored": True}

def get_history(source=None, days=30):
    if not HISTORY.exists():
        return []
    try: hist = json.loads(HISTORY.read_text())
    except: hist = []
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    out = []
    for h in hist:
        try:
            ca = datetime.datetime.fromisoformat(h["collected_at"].replace("Z","+00:00"))
        except: ca = None
        if ca and ca < cutoff: continue
        if source and h.get("source") != source: continue
        out.append(h)
    return out

def collect(source=None, days=30):
    results = {}; errors = {}
    if source is None or source == "local":
        # local baseline: just record a marker
        results["local"] = {"ok": True, "metrics": {"note": "local baseline available"}}
    if source in (None, "youtube_analytics"):
        r = collect_youtube_analytics(days)
        if r.get("ok"): results["youtube_analytics"] = r
        else: errors["youtube_analytics"] = r.get("error")
    if source in (None, "youtube_data"):
        r = collect_youtube_data(days=days)
        if r.get("ok"): results["youtube_data"] = r
        else: errors["youtube_data"] = r.get("error")
    if source in (None, "meta_insights"):
        r = collect_meta(days)
        if r.get("ok"): results["meta_insights"] = r
        else: errors["meta_insights"] = r.get("error") if "error" in r else None
        # store sub-errors
        if isinstance(r.get("sources"), dict):
            for k, v in r["sources"].items():
                if isinstance(v, dict) and not v.get("ok") and v.get("error"):
                    errors[f"meta_insights.{k}"] = v["error"]
    if source in (None, "ga4"):
        r = collect_ga4(days)
        if r.get("ok"): results["ga4"] = r
        else: errors["ga4"] = r.get("error")
    # store each successful
    for s, m in results.items():
        store_record(s, m)
    if source is not None and source not in results and source not in errors:
        # single source requested but not handled
        pass
    # if specific source requested, filter
    if source is not None:
        if source in results:
            results = {source: results[source]}
        if source in errors:
            errors = {source: errors[source]}
    return {"source": results, "errors": errors}

def collect_all(days=30):
    return collect(source=None, days=days)

def summarize(days=30):
    h = get_history(days=days)
    kpi = {"days": days, "records": len(h), "by_source": {}}
    for src in SOURCES:
        recs = [r for r in h if r.get("source") == src]
        kpi["by_source"][src] = len(recs)
    return kpi

def send_digest(days=7):
    tok = env("TELEGRAM_BOT_TOKEN"); chat = env("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        return {"ok": False, "error": "telegram not configured"}
    h = get_history(days=days)
    lines = [f"Analytics digest (last {days}d):", f"records={len(h)}"]
    for src in SOURCES:
        n = len([r for r in h if r.get("source")==src])
        lines.append(f"{src}: {n}")
    text = "\n".join(lines)
    import urllib.request
    payload = json.dumps({"chat_id": chat, "text": text[:3500], "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage", data=payload, headers={"Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            res = json.loads(r.read().decode())
            return {"ok": r.status==200 and res.get("ok") is True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def list_sources():
    for s in available_sources():
        print(f"{s['name']:20} configured={s['configured']} missing={s['missing_keys']}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--source")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--collect-all", action="store_true")
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--digest", action="store_true")
    args = parser.parse_args()
    if args.list:
        list_sources(); return 0
    if args.collect_all:
        print(json.dumps(collect_all(args.days), indent=2)); return 0
    if args.collect:
        print(json.dumps(collect(args.source, args.days), indent=2)); return 0
    if args.history:
        print(json.dumps(get_history(args.source, args.days), indent=2)); return 0
    if args.summary:
        print(json.dumps(summarize(args.days), indent=2)); return 0
    if args.digest:
        print(json.dumps(send_digest(7), indent=2)); return 0
    return 0

if __name__ == "__main__":
    raise SystemExit(main())