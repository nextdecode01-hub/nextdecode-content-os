from __future__ import annotations
import os, json, sqlite3, hashlib, hmac, base64, urllib.request, urllib.parse, urllib.error, csv, argparse, time, datetime
from pathlib import Path
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)
DB_PATH = ROOT / "data" / "workspace.db"

def env(name):
    v = os.getenv(name, "").strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        v = v[1:-1].strip()
    return v

def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def _req(method, url, headers=None, data=None, timeout=30):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            try:
                return r.status, json.loads(raw) if raw else {}, None
            except Exception:
                return r.status, raw, None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body), body
        except Exception:
            return e.code, None, body
    except Exception as e:
        return 0, None, str(e)

# ---- SQLite ----
def init_db():
    con = sqlite3.connect(str(DB_PATH))
    con.execute("""CREATE TABLE IF NOT EXISTS content_records (
        id TEXT PRIMARY KEY, created_at TEXT, platform TEXT, title TEXT, hook TEXT,
        video_path TEXT, public_url TEXT, script_json TEXT, hashtags TEXT,
        review_status TEXT, published_at TEXT, score REAL, metadata_json TEXT)""")
    con.commit(); con.close()
    return {"ok": True, "path": str(DB_PATH)}

def _record_to_row(r):
    return (r.get("id"), r.get("created_at") or _now(), r.get("platform"), r.get("title"), r.get("hook"),
            r.get("video_path"), r.get("public_url"), json.dumps(r.get("script")) if r.get("script") is not None else None,
            json.dumps(r.get("hashtags")) if r.get("hashtags") is not None else None,
            r.get("review_status"), r.get("published_at"),
            r.get("score"), json.dumps(r.get("metadata")) if r.get("metadata") is not None else None)

def sqlite_push(record):
    try:
        init_db()
        con = sqlite3.connect(str(DB_PATH))
        con.execute("""INSERT OR REPLACE INTO content_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", _record_to_row(record))
        con.commit(); con.close()
        return {"ok": True, "id": record.get("id")}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def sqlite_pull(limit=50):
    try:
        init_db()
        con = sqlite3.connect(str(DB_PATH)); con.row_factory = sqlite3.Row
        rows = con.execute("SELECT * FROM content_records ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception:
        return []

def sqlite_list(platform=None, limit=50):
    try:
        init_db()
        con = sqlite3.connect(str(DB_PATH)); con.row_factory = sqlite3.Row
        if platform:
            rows = con.execute("SELECT * FROM content_records WHERE platform=? ORDER BY created_at DESC LIMIT ?", (platform, limit)).fetchall()
        else:
            rows = con.execute("SELECT * FROM content_records ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception:
        return []

def sqlite_update_status(rid, status):
    try:
        init_db()
        con = sqlite3.connect(str(DB_PATH))
        con.execute("UPDATE content_records SET review_status=? WHERE id=?", (status, rid))
        con.commit(); con.close()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def sqlite_search(q):
    try:
        init_db()
        like = f"%{q}%"
        con = sqlite3.connect(str(DB_PATH)); con.row_factory = sqlite3.Row
        rows = con.execute("SELECT * FROM content_records WHERE title LIKE ? OR hook LIKE ? OR hashtags LIKE ? ORDER BY created_at DESC LIMIT 50", (like, like, like)).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception:
        return []

# ---- Backends registry ----
def _configured(keys):
    return all(env(k) for k in keys)

BACKENDS = ["sqlite","airtable","notion","supabase","cloudinary","r2"]

def available_backends():
    out = []
    out.append({"name":"sqlite","configured":True,"missing_keys":[],"kind":"store"})
    out.append({"name":"airtable","configured":_configured(["AIRTABLE_API_KEY","AIRTABLE_BASE_ID","AIRTABLE_TABLE"]),"missing_keys":[k for k in ["AIRTABLE_API_KEY","AIRTABLE_BASE_ID","AIRTABLE_TABLE"] if not env(k)],"kind":"store"})
    out.append({"name":"notion","configured":_configured(["NOTION_API_KEY","NOTION_DATABASE_ID"]),"missing_keys":[k for k in ["NOTION_API_KEY","NOTION_DATABASE_ID"] if not env(k)],"kind":"store"})
    out.append({"name":"supabase","configured":_configured(["SUPABASE_URL","SUPABASE_SERVICE_KEY"]),"missing_keys":[k for k in ["SUPABASE_URL","SUPABASE_SERVICE_KEY"] if not env(k)],"kind":"store"})
    out.append({"name":"cloudinary","configured":_configured(["CLOUDINARY_CLOUD_NAME","CLOUDINARY_API_KEY","CLOUDINARY_API_SECRET"]),"missing_keys":[k for k in ["CLOUDINARY_CLOUD_NAME","CLOUDINARY_API_KEY","CLOUDINARY_API_SECRET"] if not env(k)],"kind":"storage"})
    out.append({"name":"r2","configured":_configured(["R2_ACCOUNT_ID","R2_ACCESS_KEY_ID","R2_SECRET_ACCESS_KEY","R2_BUCKET"]),"missing_keys":[k for k in ["R2_ACCOUNT_ID","R2_ACCESS_KEY_ID","R2_SECRET_ACCESS_KEY","R2_BUCKET"] if not env(k)],"kind":"storage"})
    return out

# ---- Airtable ----
def airtable_configured():
    return _configured(["AIRTABLE_API_KEY","AIRTABLE_BASE_ID","AIRTABLE_TABLE"])
def airtable_push(record):
    if not airtable_configured():
        return {"ok": False, "error": "missing keys: " + ",".join([k for k in ["AIRTABLE_API_KEY","AIRTABLE_BASE_ID","AIRTABLE_TABLE"] if not env(k)])}
    base = env("AIRTABLE_BASE_ID"); table = env("AIRTABLE_TABLE"); key = env("AIRTABLE_API_KEY")
    fields = {"Title": record.get("title"), "Hook": record.get("hook"), "Platform": record.get("platform"),
              "VideoPath": record.get("video_path"), "PublicURL": record.get("public_url"),
              "Hashtags": ",".join(record.get("hashtags") or []), "ReviewStatus": record.get("review_status"),
              "Score": record.get("score"), "CreatedAt": record.get("created_at"), "PublishedAt": record.get("published_at")}
    body = json.dumps({"records":[{"fields":fields}]}).encode()
    st, data, err = _req("POST", f"https://api.airtable.com/v0/{base}/{urllib.parse.quote(table)}", headers={"Authorization": f"Bearer {key}", "Content-Type":"application/json"}, data=body)
    if st in (200,201):
        rid = (data.get("records") or [{}])[0].get("id") if isinstance(data, dict) else None
        return {"ok": True, "id": rid}
    return {"ok": False, "error": err or str(data)}

def airtable_pull(limit=50):
    if not airtable_configured():
        return []
    base = env("AIRTABLE_BASE_ID"); table = env("AIRTABLE_TABLE"); key = env("AIRTABLE_API_KEY")
    url = f"https://api.airtable.com/v0/{base}/{urllib.parse.quote(table)}?maxRecords={limit}"
    st, data, err = _req("GET", url, headers={"Authorization": f"Bearer {key}"})
    if st == 200 and isinstance(data, dict):
        out = []
        for r in data.get("records", []):
            f = r.get("fields", {})
            out.append({"id": r.get("id"), "title": f.get("Title"), "hook": f.get("Hook"), "platform": f.get("Platform"),
                        "video_path": f.get("VideoPath"), "public_url": f.get("PublicURL"), "hashtags": (f.get("Hashtags") or "").split(","),
                        "review_status": f.get("ReviewStatus"), "score": f.get("Score"), "created_at": f.get("CreatedAt"),
                        "published_at": f.get("PublishedAt")})
        return out
    return []

# ---- Notion ----
def notion_configured():
    return _configured(["NOTION_API_KEY","NOTION_DATABASE_ID"])
NOTION_VER = "2022-06-28"
def notion_push(record):
    if not notion_configured():
        return {"ok": False, "error": "missing notion keys"}
    key = env("NOTION_API_KEY"); db = env("NOTION_DATABASE_ID")
    props = {
        "Title": {"title": [{"text": {"content": str(record.get("title") or "")}}]},
        "Hook": {"rich_text": [{"text": {"content": str(record.get("hook") or "")}}]},
        "Platform": {"rich_text": [{"text": {"content": str(record.get("platform") or "")}}]},
        "ReviewStatus": {"select": {"name": str(record.get("review_status") or "pending")}},
        "Score": {"number": record.get("score")},
        "Hashtags": {"rich_text": [{"text": {"content": ",".join(record.get("hashtags") or [])}}]},
        "CreatedAt": {"date": {"start": record.get("created_at") or _now()}},
    }
    if record.get("public_url"):
        props["PublicURL"] = {"url": record.get("public_url")}
    body = json.dumps({"parent": {"database_id": db}, "properties": props}).encode()
    st, data, err = _req("POST", "https://api.notion.com/v1/pages", headers={"Authorization": f"Bearer {key}", "Notion-Version": NOTION_VER, "Content-Type":"application/json"}, data=body)
    if st in (200, 201):
        return {"ok": True, "id": data.get("id") if isinstance(data, dict) else None}
    return {"ok": False, "error": err or str(data)}

def notion_pull(limit=50):
    if not notion_configured():
        return []
    key = env("NOTION_API_KEY"); db = env("NOTION_DATABASE_ID")
    body = json.dumps({"page_size": min(limit, 100)}).encode()
    st, data, err = _req("POST", f"https://api.notion.com/v1/databases/{db}/query", headers={"Authorization": f"Bearer {key}", "Notion-Version": NOTION_VER, "Content-Type":"application/json"}, data=body)
    if st == 200 and isinstance(data, dict):
        out = []
        for p in data.get("results", []):
            props = p.get("properties", {})
            def txt(name):
                arr = props.get(name, {}).get("title") or props.get(name, {}).get("rich_text") or []
                return "".join(t.get("plain_text","") for t in arr)
            out.append({"id": p.get("id"), "title": txt("Title"), "hook": txt("Hook"), "platform": txt("Platform"),
                        "review_status": (props.get("ReviewStatus",{}).get("select") or {}).get("name"),
                        "score": props.get("Score",{}).get("number"),
                        "created_at": (props.get("CreatedAt",{}).get("date") or {}).get("start")})
        return out
    return []

def create_database_if_missing():
    # Notion DBs must be created under a page; we instead verify the configured db is reachable.
    if not notion_configured():
        return {"ok": False, "error": "missing notion keys"}
    key = env("NOTION_API_KEY"); db = env("NOTION_DATABASE_ID")
    st, data, err = _req("GET", f"https://api.notion.com/v1/databases/{db}", headers={"Authorization": f"Bearer {key}", "Notion-Version": NOTION_VER})
    if st == 200:
        return {"ok": True, "exists": True}
    return {"ok": False, "error": err or str(data)}

# ---- Supabase ----
def supabase_configured():
    return _configured(["SUPABASE_URL","SUPABASE_SERVICE_KEY"])
def supabase_push(record):
    if not supabase_configured():
        return {"ok": False, "error": "missing supabase keys"}
    url = env("SUPABASE_URL").rstrip("/"); key = env("SUPABASE_SERVICE_KEY")
    row = {"id": record.get("id"), "created_at": record.get("created_at") or _now(), "platform": record.get("platform"),
           "title": record.get("title"), "hook": record.get("hook"), "video_path": record.get("video_path"),
           "public_url": record.get("public_url"), "script_json": json.dumps(record.get("script")) if record.get("script") is not None else None,
           "hashtags": json.dumps(record.get("hashtags")) if record.get("hashtags") is not None else None,
           "review_status": record.get("review_status"), "published_at": record.get("published_at"),
           "score": record.get("score"), "metadata_json": json.dumps(record.get("metadata")) if record.get("metadata") is not None else None}
    body = json.dumps([row]).encode()
    st, data, err = _req("POST", f"{url}/rest/v1/content_records", headers={"apikey": key, "Authorization": f"Bearer {key}", "Prefer": "resolution=merge-duplicates", "Content-Type":"application/json"}, data=body)
    if st in (200, 201, 204):
        return {"ok": True, "id": record.get("id")}
    return {"ok": False, "error": err or str(data)}

def supabase_pull(limit=50):
    if not supabase_configured():
        return []
    url = env("SUPABASE_URL").rstrip("/"); key = env("SUPABASE_SERVICE_KEY")
    st, data, err = _req("GET", f"{url}/rest/v1/content_records?select=*&order=created_at.desc&limit={limit}", headers={"apikey": key, "Authorization": f"Bearer {key}"})
    if st == 200 and isinstance(data, list):
        return data
    return []

def supabase_ensure_table():
    # Try RPC exec_sql if exists
    if not supabase_configured():
        return {"ok": False, "error": "missing keys"}
    url = env("SUPABASE_URL").rstrip("/"); key = env("SUPABASE_SERVICE_KEY")
    ddl = """CREATE TABLE IF NOT EXISTS content_records (
  id TEXT PRIMARY KEY, created_at TEXT, platform TEXT, title TEXT, hook TEXT,
  video_path TEXT, public_url TEXT, script_json TEXT, hashtags TEXT,
  review_status TEXT, published_at TEXT, score DOUBLE PRECISION, metadata_json TEXT
);"""
    body = json.dumps({"query": ddl}).encode()
    st, data, err = _req("POST", f"{url}/rest/v1/rpc/exec_sql", headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type":"application/json"}, data=body)
    if st in (200, 201, 204):
        return {"ok": True, "method": "rpc"}
    return {"ok": False, "error": "exec_sql RPC not available; run the DDL manually", "sql": ddl}

def print_sql():
    ddl = """CREATE TABLE IF NOT EXISTS content_records (
  id TEXT PRIMARY KEY, created_at TEXT, platform TEXT, title TEXT, hook TEXT,
  video_path TEXT, public_url TEXT, script_json TEXT, hashtags TEXT,
  review_status TEXT, published_at TEXT, score DOUBLE PRECISION, metadata_json TEXT
);"""
    print(ddl)

# ---- Cloudinary ----
def cloudinary_configured():
    return _configured(["CLOUDINARY_CLOUD_NAME","CLOUDINARY_API_KEY","CLOUDINARY_API_SECRET"])
def cloudinary_upload(path, kind="image"):
    if not cloudinary_configured():
        return {"ok": False, "error": "missing cloudinary keys"}
    cloud = env("CLOUDINARY_CLOUD_NAME"); api_key = env("CLOUDINARY_API_KEY"); secret = env("CLOUDINARY_API_SECRET")
    timestamp = str(int(time.time()))
    to_sign = f"timestamp={timestamp}{secret}"
    sig = hashlib.sha1(to_sign.encode()).hexdigest()
    endpoint = f"https://api.cloudinary.com/v1_1/{cloud}/{ 'image' if kind!='video' else 'video'}/upload"
    # multipart
    boundary = "----ndboundary"
    p = Path(path)
    file_bytes = p.read_bytes()
    parts = []
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"api_key\"\r\n\r\n{api_key}\r\n")
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"timestamp\"\r\n\r\n{timestamp}\r\n")
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"signature\"\r\n\r\n{sig}\r\n")
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{p.name}\"\r\nContent-Type: application/octet-stream\r\n\r\n")
    body = "".join(parts).encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()
    st, data, err = _req("POST", endpoint, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, data=body, timeout=120)
    if st in (200,201) and isinstance(data, dict):
        return {"ok": True, "url": data.get("secure_url"), "public_id": data.get("public_id")}
    return {"ok": False, "error": err or str(data)}

# ---- R2 (SigV4 manual) ----
def r2_configured():
    return _configured(["R2_ACCOUNT_ID","R2_ACCESS_KEY_ID","R2_SECRET_ACCESS_KEY","R2_BUCKET"])
def _sigv4_sign(method, url, headers, payload, access, secret, region="auto", service="s3"):
    from urllib.parse import urlparse
    parsed = urlparse(url)
    host = parsed.netloc
    path = parsed.path or "/"
    query = parsed.query
    t = datetime.datetime.now(datetime.timezone.utc)
    amz_date = t.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = t.strftime("%Y%m%d")
    payload_hash = hashlib.sha256(payload if isinstance(payload, (bytes, bytearray)) else payload.encode()).hexdigest()
    headers = dict(headers)
    headers["host"] = host
    headers["x-amz-date"] = amz_date
    headers["x-amz-content-sha256"] = payload_hash
    signed_headers = sorted(k.lower() for k in headers.keys())
    canonical_headers = "".join(f"{k}:{headers[k].strip()}\n" if False else f"{k}:{str(headers[k]).strip()}\n" for k in signed_headers)
    # fix canonical header construction
    canonical_headers = ""
    for k in signed_headers:
        canonical_headers += f"{k}:{str(headers[k]).strip()}\n"
    canonical_request = f"{method}\n{path}\n{query}\n{canonical_headers}\n{';'.join(signed_headers)}\n{payload_hash}"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
    def hmac_sha256(key, msg):
        return hmac.new(key, msg.encode() if isinstance(msg, str) else msg, hashlib.sha256).digest()
    k_date = hmac_sha256(("AWS4"+secret).encode(), date_stamp)
    k_region = hmac_sha256(k_date, region)
    k_service = hmac_sha256(k_region, service)
    k_signing = hmac_sha256(k_service, "aws4_request")
    signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()
    auth = f"AWS4-HMAC-SHA256 Credential={access}/{credential_scope}, SignedHeaders={';'.join(signed_headers)}, Signature={signature}"
    headers["Authorization"] = auth
    return headers, amz_date

def r2_upload(path, key=None):
    if not r2_configured():
        return {"ok": False, "error": "missing r2 keys"}
    account = env("R2_ACCOUNT_ID"); access = env("R2_ACCESS_KEY_ID"); secret = env("R2_SECRET_ACCESS_KEY"); bucket = env("R2_BUCKET")
    p = Path(path)
    if key is None:
        key = p.name
    url = f"https://{account}.r2.cloudflarestorage.com/{bucket}/{urllib.parse.quote(key)}"
    data = p.read_bytes()
    headers = {"Content-Type": "application/octet-stream", "Content-Length": str(len(data))}
    headers, amz_date = _sigv4_sign("PUT", url, headers, data, access, secret)
    st, resp, err = _req("PUT", url, headers=headers, data=data, timeout=120)
    if st in (200, 201, 204):
        pub = env("R2_PUBLIC_BASE_URL")
        if pub:
            return {"ok": True, "url": f"{pub.rstrip('/')}/{key}", "key": key}
        # presigned GET
        get_url = _r2_presign_get(account, access, secret, bucket, key, 3600)
        return {"ok": True, "url": get_url, "key": key}
    return {"ok": False, "error": err or str(resp)}

def _r2_presign_get(account, access, secret, bucket, key, expires):
    url = f"https://{account}.r2.cloudflarestorage.com/{bucket}/{urllib.parse.quote(key)}"
    t = datetime.datetime.now(datetime.timezone.utc)
    amz_date = t.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = t.strftime("%Y%m%d")
    region = "auto"; service = "s3"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    # query params
    params = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": f"{access}/{credential_scope}",
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(expires),
        "X-Amz-SignedHeaders": "host",
    }
    from urllib.parse import urlencode
    query = urlencode(sorted(params.items()))
    canonical_request = f"GET\n/{bucket}/{urllib.parse.quote(key)}\n{query}\nhost:{account}.r2.cloudflarestorage.com\n\nhost\nUNSIGNED-PAYLOAD"
    string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
    def hmac_sha256(keyb, msg):
        return hmac.new(keyb, msg.encode() if isinstance(msg, str) else msg, hashlib.sha256).digest()
    k_date = hmac_sha256(("AWS4"+secret).encode(), date_stamp)
    k_region = hmac_sha256(k_date, region)
    k_service = hmac_sha256(k_region, service)
    k_signing = hmac_sha256(k_service, "aws4_request")
    signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()
    return f"{url}?{query}&X-Amz-Signature={signature}"

# ---- Public API ----
def push_record(record, backends=None):
    if backends is None:
        backends = [b["name"] for b in available_backends() if b["configured"] and b["kind"]=="store"]
    res = {}
    for b in backends:
        if b == "sqlite":
            res[b] = sqlite_push(record)
        elif b == "airtable":
            res[b] = airtable_push(record)
        elif b == "notion":
            res[b] = notion_push(record)
        elif b == "supabase":
            res[b] = supabase_push(record)
        else:
            res[b] = {"ok": False, "error": "not a store backend"}
    return res

def pull_records(backend="sqlite", limit=50):
    if backend == "sqlite":
        return sqlite_pull(limit)
    if backend == "airtable":
        return airtable_pull(limit)
    if backend == "notion":
        return notion_pull(limit)
    if backend == "supabase":
        return supabase_pull(limit)
    return []

def sync_all(record):
    stores = [b["name"] for b in available_backends() if b["configured"] and b["kind"]=="store"]
    return push_record(record, backends=stores)

def upload_asset(path, backends=None):
    if backends is None:
        backends = [b["name"] for b in available_backends() if b["configured"] and b["kind"]=="storage"]
    res = {}
    for b in backends:
        if b == "cloudinary":
            kind = "video" if str(path).lower().endswith((".mp4",".mov",".webm")) else "image"
            res[b] = cloudinary_upload(path, kind=kind)
        elif b == "r2":
            res[b] = r2_upload(path)
        else:
            res[b] = {"ok": False, "error": "not a storage backend"}
    return res

def list_backends():
    for b in available_backends():
        print(f"{b['name']:12} configured={b['configured']} kind={b['kind']} missing={b['missing_keys']}")

def list_records(platform=None, limit=50):
    return sqlite_list(platform, limit)

def update_status(rid, status):
    return sqlite_update_status(rid, status)

def search(q):
    return sqlite_search(q)

# ---- CLI ----
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--push")
    parser.add_argument("--pull", action="store_true")
    parser.add_argument("--backend", default="sqlite")
    parser.add_argument("--upload")
    parser.add_argument("--init-db", action="store_true")
    parser.add_argument("--print-sql", action="store_true")
    args = parser.parse_args()
    if args.list:
        list_backends(); return 0
    if args.init_db:
        print(json.dumps(init_db())); return 0
    if args.print_sql:
        print_sql(); return 0
    if args.push:
        rec = json.loads(Path(args.push).read_text())
        print(json.dumps(push_record(rec), indent=2)); return 0
    if args.pull:
        print(json.dumps(pull_records(args.backend, 50), indent=2)); return 0
    if args.upload:
        print(json.dumps(upload_asset(args.upload), indent=2)); return 0
    return 0

if __name__ == "__main__":
    raise SystemExit(main())