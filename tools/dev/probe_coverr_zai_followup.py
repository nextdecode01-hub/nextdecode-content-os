import os,json,time,requests
from dotenv import load_dotenv
load_dotenv('.env',override=True)
def run(name,fn):
 t=time.perf_counter()
 try: print(json.dumps({name:{'latency_ms':round((time.perf_counter()-t)*1000),**fn()}},ensure_ascii=False),flush=True)
 except Exception as e: print(json.dumps({name:{'latency_ms':round((time.perf_counter()-t)*1000),'error':type(e).__name__}}),flush=True)
def coverr():
 r=requests.get('https://api.coverr.co/videos',params={'query':'city','page_size':3},headers={'x-api-key':os.getenv('COVERR_API_KEY','')},timeout=20);d=r.json();return {'status':r.status_code,'hits':len(d.get('hits') or []),'nbHits':d.get('nbHits'),'first_fields':list((d.get('hits') or [{}])[0].keys())[:10] if d.get('hits') else []}
def zai():
 r=requests.post('https://api.z.ai/api/paas/v4/chat/completions',headers={'Authorization':'Bearer '+os.getenv('Z_API_KEY',''),'Content-Type':'application/json'},json={'model':'glm-4.5-flash','messages':[{'role':'user','content':'Reply in one sentence: what does an MoE router do?'}],'temperature':0.2,'max_tokens':250},timeout=40);d=r.json();c=(d.get('choices') or [{}])[0];return {'status':r.status_code,'content':str((c.get('message') or {}).get('content') or '')[:400],'usage':d.get('usage'),'error':d.get('error')}
run('coverr_city',coverr);run('zai_glm_4_5_flash',zai)
