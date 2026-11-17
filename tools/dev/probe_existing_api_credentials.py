#!/usr/bin/env python3
"""Safe, bounded probes for owner-configured media/chat APIs. No generations or paid jobs."""
import os,json,time,requests
from dotenv import load_dotenv
load_dotenv('.env',override=True)
S={}
def result(name,fn):
 t=time.perf_counter()
 try:
  data=fn();S[name]={'latency_ms':round((time.perf_counter()-t)*1000),**data}
 except Exception as e:S[name]={'latency_ms':round((time.perf_counter()-t)*1000),'error':type(e).__name__}
 print(json.dumps({name:S[name]},ensure_ascii=False),flush=True)

def coverr():
 k=os.getenv('COVERR_API_KEY','').strip()
 if not k:return {'configured':False}
 r=requests.get('https://api.coverr.co/videos',params={'query':'technology data centre','page_size':2},headers={'x-api-key':k},timeout=20)
 body=r.json() if r.headers.get('content-type','').startswith('application/json') else {}
 return {'configured':True,'http_status':r.status_code,'result_count':len(body.get('hits') or body.get('videos') or []) if isinstance(body,dict) else 0,'body_keys':sorted(body.keys())[:12] if isinstance(body,dict) else []}

def instudio(path):
 k=os.getenv('INSTUDIO_API_KEY','').strip()
 if not k:return {'configured':False}
 r=requests.get('https://studio.instadatahelp.com/api/v1/'+path,headers={'Authorization':'Bearer '+k},timeout=20)
 body=r.json() if r.headers.get('content-type','').startswith('application/json') else {}
 out={'configured':True,'http_status':r.status_code}
 if path=='account' and isinstance(body,dict):
  d=body.get('data') if isinstance(body.get('data'),dict) else body
  for field in ('plan','credits','credit_balance','rate_limit'): 
   if field in d:out[field]=d[field]
 if path=='models' and isinstance(body,dict):
  arr=body.get('models') or (body.get('data') if isinstance(body.get('data'),list) else [])
  out['model_count']=len(arr) if isinstance(arr,list) else None
  out['model_ids']=[str(x.get('id') or x.get('model') or x.get('name')) for x in arr[:8] if isinstance(x,dict)] if isinstance(arr,list) else []
 if r.status_code>=400:out['error_body']=r.text[:250]
 return out

def zai(model, multimodal=False):
 k=os.getenv('Z_API_KEY','').strip()
 if not k:return {'configured':False}
 prompt='Return a concise JSON object with keys status and summary. Explain what this AI model can do.'
 content=[{'type':'text','text':'Describe only the visible scene in this image in one sentence.'},{'type':'image_url','image_url':{'url':'https://assets.ngc.nvidia.com/products/api-catalog/phi-3-5-vision/example1a.jpg'}}] if multimodal else prompt
 r=requests.post('https://api.z.ai/api/paas/v4/chat/completions',headers={'Authorization':'Bearer '+k,'Content-Type':'application/json'},json={'model':model,'messages':[{'role':'user','content':content}],'temperature':0.2,'max_tokens':800},timeout=60)
 body=r.json() if r.headers.get('content-type','').startswith('application/json') else {}
 choice=(body.get('choices') or [{}])[0] if isinstance(body,dict) else {}
 msg=choice.get('message') or {}
 return {'configured':True,'model':model,'http_status':r.status_code,'content_present':bool(msg.get('content')),'finish_reason':choice.get('finish_reason'),'sample':str(msg.get('content') or '')[:500],'usage':body.get('usage') if isinstance(body,dict) else None,'error_body':r.text[:250] if r.status_code>=400 else None}

result('coverr',coverr)
result('instudio_account',lambda:instudio('account'))
result('instudio_models',lambda:instudio('models'))
result('zai_glm_4_7_flash',lambda:zai('glm-4.7-flash'))
result('zai_glm_4_6v_flash',lambda:zai('glm-4.6v-flash',True))
Path='data/provider_probes/existing_api_credentials.v1.json'
from pathlib import Path as P
P(Path).parent.mkdir(parents=True,exist_ok=True)
P(Path).write_text(json.dumps({'schema':'nextdecode.existing-api-probes.v1','results':S},indent=2)+'\n',encoding='utf-8')
