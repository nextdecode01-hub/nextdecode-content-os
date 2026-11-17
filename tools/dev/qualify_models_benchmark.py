#!/usr/bin/env python3
"""Repeated exact-model NEXTDECODE benchmark; qualification only."""
import json, time
from datetime import datetime, timezone
from pathlib import Path
from app.providers.model_health import _call_model, _load_dotenv, _schema_ok
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data'/'model_benchmark_v1'; OUT.mkdir(parents=True,exist_ok=True)
REPEATS=3; TIMEOUT=60
CANDIDATES=[('groq','qwen/qwen3.8-27b'),('groq','openai/gpt-oss-20b'),('groq','openai/gpt-oss-120b'),('nvidia','nvidia/nemotron-3.5-bolt-e4b'),('nvidia','nvidia/nemotron-3.5-lightning-30b-a3b')]
TASKS={
'script':'''Act as NEXTDECODE's senior technology editor. Use ONLY this evidence: (1) An MoE model contains multiple expert subnetworks. (2) A router selects a subset of experts for each token/input. (3) Sparse activation can reduce computation relative to activating every expert, but benefits depend on architecture and workload. (4) Routing and load-balancing can introduce complexity. Return raw JSON only with exactly hook,title,voice_text,youtube_tags. voice_text 92-118 words; hook exactly equals first sentence; title <=60 characters; youtube_tags non-empty string array. Strong specific hook, clear explanation, natural spoken pacing, meaningful caveat. Do not invent benchmark numbers, companies, dates or universal claims.''',
'evidence':'''Return raw JSON only with exactly summary,supported_claims,unsupported_claims,caveat. Evidence: A hypothetical controlled test on one MoE prototype reports lower average inference compute when only a subset of experts is activated per token. No public benchmark data, model name, cost data, accuracy comparison, or cross-model results are supplied. Summarize only what is supported; put plausible but unproven generalizations in unsupported_claims. Do not invent details.''',
'visual':'''Return raw JSON only: an array of exactly 5 objects with fields beat,visual_intent,shot_type,asset_query,original_graphic,avoid. Topic: how an MoE model routes a token to specialized expert networks. Each beat must show a distinct narrative step; avoid repeating the same abstract network shot. Mix real-world footage opportunities with purposeful original graphics. Do not invent factual performance metrics.'''}
def parse(raw):
 try:return json.loads(raw)
 except Exception:return None
def evaluate(task,raw):
 obj=parse(raw); r={'valid_json':obj is not None,'schema_ok':False,'checks':{},'score':0}
 if obj is None:return r
 if task=='script':
  r['schema_ok']=_schema_ok(obj); words=len(str(obj.get('voice_text','')).split()); hook=str(obj.get('hook','')).strip(); first=str(obj.get('voice_text','')).strip().split('.',1)[0].strip()
  c={'word_count':words,'word_count_pass':92<=words<=118,'hook_match':hook.rstrip('.!?')==first.rstrip('.!?'),'title_chars':len(str(obj.get('title',''))),'tags_nonempty':isinstance(obj.get('youtube_tags'),list) and bool(obj.get('youtube_tags'))}; r['checks']=c; r['score']=25*sum([c['word_count_pass'],c['hook_match'],c['title_chars']<=60,c['tags_nonempty']])
 elif task=='evidence':
  req={'summary','supported_claims','unsupported_claims','caveat'}; ok=req.issubset(obj) and isinstance(obj.get('supported_claims'),list) and isinstance(obj.get('unsupported_claims'),list); c={'required_fields':ok,'unsupported_caveats_present':bool(obj.get('unsupported_claims')),'no_promoted_universal_claim':not any(x in ' '.join(map(str,obj.get('unsupported_claims',[]))).lower() for x in ['universal speed','lower cost','better accuracy'])}; r['schema_ok']=ok;r['checks']=c;r['score']=(50 if ok else 0)+(25 if c['unsupported_caveats_present'] else 0)+(25 if c['no_promoted_universal_claim'] else 0)
 else:
  req={'beat','visual_intent','shot_type','asset_query','original_graphic','avoid'}; rows=obj if isinstance(obj,list) else []; valid=len(rows)==5 and all(isinstance(x,dict) and req.issubset(x) for x in rows); unique=len({str(x.get('visual_intent','')).strip().lower() for x in rows}) if rows else 0; r['schema_ok']=valid;r['checks']={'five_shots':len(rows)==5,'all_fields':valid,'distinct_intents':unique};r['score']=(70 if valid else 0)+(30 if unique==5 else 0)
 return r
def main():
 _load_dotenv(); started=time.perf_counter(); total=len(CANDIDATES)*len(TASKS)*REPEATS; run={'schema':'nextdecode.model-benchmark.v1','started_at':datetime.now(timezone.utc).isoformat(),'repeats':REPEATS,'timeout_seconds':TIMEOUT,'results':[]}; n=0
 for provider,model in CANDIDATES:
  for task,prompt in TASKS.items():
   for trial in range(1,REPEATS+1):
    n+=1; t=time.perf_counter(); rec={'provider':provider,'model':model,'task':task,'trial':trial,'checked_at':datetime.now(timezone.utc).isoformat(),'usage':'unknown','ok':False}
    try:
     raw=_call_model(provider,model,prompt,TIMEOUT); rec['latency_ms']=round((time.perf_counter()-t)*1000); rec['evaluation']=evaluate(task,raw); rec['ok']=rec['evaluation']['valid_json'] and rec['evaluation']['schema_ok']; name=f'{provider}__{model.replace("/","_")}__{task}__{trial}.txt'; (OUT/name).write_text(raw,encoding='utf-8'); rec['raw_output_file']=name
    except Exception as e: rec['latency_ms']=round((time.perf_counter()-t)*1000);rec['error']=type(e).__name__
    run['results'].append(rec); print(json.dumps({'progress':f'{n}/{total}','provider':provider,'model':model,'task':task,'trial':trial,'ok':rec['ok'],'latency_ms':rec['latency_ms'],'error':rec.get('error','')}),flush=True); (OUT/'latest.partial.json').write_text(json.dumps(run,indent=2),encoding='utf-8')
 agg={}
 for rec in run['results']:
  key=f"{rec['provider']}:{rec['model']}:{rec['task']}"; b=agg.setdefault(key,{'trials':0,'passes':0,'scores':[],'latencies':[]});b['trials']+=1;b['passes']+=int(rec['ok']);b['latencies'].append(rec['latency_ms']);
  if rec.get('evaluation'):b['scores'].append(rec['evaluation']['score'])
 for b in agg.values():b['mean_score']=round(sum(b['scores'])/len(b['scores']),1) if b['scores'] else None;b['mean_latency_ms']=round(sum(b['latencies'])/len(b['latencies']));del b['scores'];del b['latencies']
 run.update({'completed_at':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':round(time.perf_counter()-started,2),'aggregate':agg});(OUT/'latest.json').write_text(json.dumps(run,indent=2),encoding='utf-8');(OUT/'latest.partial.json').unlink(missing_ok=True);print(json.dumps({'completed':True,'elapsed_seconds':run['elapsed_seconds'],'aggregate':agg}),flush=True)
if __name__=='__main__':main()
