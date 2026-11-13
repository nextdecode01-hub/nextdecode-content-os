import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path.home()/'.config/nextdecode/autonomy-db.env',override=False)
load_dotenv(Path.home()/'.config/nextdecode/api.env',override=False)
import urllib.request, urllib.error, json
base='http://127.0.0.1:8765'
for path in ['/health','/autonomy/health','/tasks?limit=100','/capabilities','/tool-catalog']:
    req=urllib.request.Request(base+path,headers={'Authorization':'Bearer '+os.environ.get('SHORTS_STUDIO_API_KEY','')})
    try:
        with urllib.request.urlopen(req,timeout=3) as r:
            raw=r.read(); print(path,'STATUS',r.status,'BYTES',len(raw),'CONTENT_TYPE',r.headers.get('Content-Type'))
            try:
                data=json.loads(raw)
                if path=='/tasks?limit=100': print('TASKS_COUNT',len(data.get('tasks',[])))
                elif path=='/capabilities': print('CAPABILITIES_COUNT',len(data.get('capabilities',[])))
                elif path=='/autonomy/health': print('HEALTH_KEYS',sorted(data.keys()))
            except Exception: pass
    except urllib.error.HTTPError as e: print(path,'HTTP_ERROR',e.code)
    except Exception as e: print(path,'UNAVAILABLE',type(e).__name__,str(e).splitlines()[0][:180])
