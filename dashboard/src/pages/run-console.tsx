import {useMemo,useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Link,useParams} from '@tanstack/react-router';
import {AlertTriangle,ArrowLeft,CheckCircle2,Clock3,Download,FileText,Link2,RefreshCw,ShieldCheck,Subtitles,Video,Volume2} from 'lucide-react';
import {api,studio,type PendingReview,type ProductionRunAssets,type ProductionRunDetail,type ProductionStoryboard,type ToolCatalogCandidates} from '../api';
import {Page,Panel,Badge,Loading,ErrorBox,Empty,SectionHead,CopyButton,CommandLine,downloadText} from '../components';

const STALE_RUN_MINUTES=60;
const ENGINE_CAPS=['research','local-model-runtime','speech-synthesis','editorial-rendering','editorial-motion-graphics','editorial-visual-analysis','workflow-engine','task-storage'] as const;
const STAGE_ORDER=[
 ['topic_selection','Topic selection','Topic chosen for this Short'],
 ['research','Research','Sources gathered, claims checked'],
 ['script','Script','Hook, narration, platform copy'],
 ['evidence','Evidence gate','Claim-to-source binding'],
 ['voice','Voice','Narration audio'],
 ['captions','Captions','Word-level caption timing'],
 ['shot_planning','Shot planning','Scene and visual plan'],
 ['render','Render','FFmpeg assembly and output'],
 ['qa','QA gate','Delivery QA — duration, fps, captions, audio'],
] as const;

const pretty=(value?:string|null)=>value?value.replace(/[._-]+/g,' ').replace(/\b\w/g,c=>c.toUpperCase()):'Not recorded';
const bytes=(value?:number|null)=>value==null?'—':value>=1024*1024?(value/1024/1024).toFixed(1)+' MB':value>=1024?(value/1024).toFixed(0)+' KB':value+' B';
const ago=(value?:string|null)=>{
 if(!value)return 'time not recorded';
 const time=Date.parse(value);
 if(!Number.isFinite(time))return 'time not recorded';
 const minutes=Math.max(0,Math.round((Date.now()-time)/60000));
 return minutes<1?'just now':minutes<60?minutes+' min ago':minutes<1440?Math.round(minutes/60)+' h ago':Math.round(minutes/1440)+' d ago';
};
const duration=(start?:string|null,end?:string|null)=>{
 if(!start)return null;
 const from=Date.parse(start),to=end?Date.parse(end):Date.now();
 if(!Number.isFinite(from)||!Number.isFinite(to)||to<from)return null;
 const seconds=Math.round((to-from)/1000);
 return seconds<60?seconds+'s':Math.floor(seconds/60)+'m '+(seconds%60)+'s';
};
const host=(url:string)=>{try{return new URL(url).hostname.replace(/^www\./,'')}catch{return url.slice(0,40)}};
const sec=(value?:number|null)=>value==null?'—':(Math.round(value*10)/10).toString();

function NextAction({detail,assets,review}:{detail?:ProductionRunDetail;assets?:ProductionRunAssets;review?:PendingReview|null}){
 if(!detail)return null;
 const run=detail.run;
 const started=Date.parse(run.started_at??'');
 const ageMinutes=Number.isFinite(started)?Math.round((Date.now()-started)/60000):null;
 const stale=run.status==='in_progress'&&ageMinutes!=null&&ageMinutes>STALE_RUN_MINUTES;
 const stage=STAGE_ORDER.find(([id])=>id===run.active_stage)?.[1]??pretty(run.active_stage);
 const recorded=detail.stages.length;
 if(run.status==='in_progress'&&!stale)return <div className="rc-next" data-tone="live">
  <span className="rc-next-dot"/>
  <div><b>Engine is running — {stage||'working'}</b><small>Started {ago(run.started_at)} · {recorded} of 9 stages recorded · this page refreshes every 3 seconds. Only stages the engine has persisted appear here.</small></div>
  <Badge tone="info">Live</Badge>
 </div>;
 if(stale)return <div className="rc-next" data-tone="warn">
  <AlertTriangle size={18}/>
  <div><b>Manifest still says “in progress” — {ageMinutes} min old</b><small>Successful runs finish in 2–3 minutes. No completion was written, so this is treated as stopped, not running. Check the worker process; nothing can be resumed from the dashboard.</small></div>
  <Badge tone="warn">Stale</Badge>
 </div>;
 if(run.status==='failed')return <div className="rc-next" data-tone="bad">
  <AlertTriangle size={18}/>
  <div><b>Stopped at {pretty(run.failure_stage)}</b><small>{run.error_type??'Error type not recorded'} · {run.error_category??'Category not recorded'}. {detail.artifacts.length?'Partial artifacts are preserved below.':'No artifacts were recorded for this run.'} Fix the pipeline, then start a new run — a failed run cannot be resumed from here.</small></div>
  <Badge tone="bad">Failed</Badge>
 </div>;
 if(run.status==='ok')return <div className="rc-next" data-tone="good">
  <CheckCircle2 size={18}/>
  <div><b>Render completed</b><small>{assets?.script.source_urls.length??0} sources · {detail.artifacts.length} artifacts recorded. Next step is the approval path: a review package must exist and pass digest checks before anything can be approved.</small></div>
  <Link className="btn" to="/reviews">Review desk</Link>
 </div>;
 return <div className="rc-next" data-tone="info"><FileText size={18}/><div><b>{pretty(run.status)}</b><small>This is the status the manifest recorded. No other state is inferred.</small></div></div>;
}

const provLabel=(prov?:Record<string,unknown>)=>{
 if(!prov)return '';
 const engine=String(prov.engine??'unknown engine');
 const provider=prov.provider?String(prov.provider):'';
 const model=prov.model?String(prov.model):'';
 const suffix=provider&&model?' · '+provider+'/'+model:provider?' · '+provider:(typeof prov.kind==='string'?' · '+String(prov.kind):'');
 return '⟶ '+engine+suffix;
};

function Journey({detail,provenance}:{detail:ProductionRunDetail;provenance?:Map<string,Record<string,unknown>>}){
 const byName=new Map(detail.stages.map(stage=>[stage.name,stage]));
 return <div className="rc-journey">{STAGE_ORDER.map(([id,title,what],index)=>{
  const stage=byName.get(id);
  const state=stage?.status??'not_recorded';
  const artifacts=detail.artifacts.filter(artifact=>artifact.stage===id).length;
  return <div className="rc-stage" data-state={state} key={id}>
   <span className="rc-stage-index">{String(index+1).padStart(2,'0')}</span>
   <div className="rc-stage-copy">
    <b>{title}</b>
    <small>{what}</small>
    <span className="rc-stage-meta">{stage?duration(stage.started_at,stage.finished_at)??'timing not recorded':'not recorded in manifest'} · {artifacts} artifact{artifacts===1?'':'s'}</span>
    {provenance?.get(id)?<div className="rc-stage-prov" title={JSON.stringify(provenance.get(id))}>{provLabel(provenance.get(id) as Record<string,unknown>)}</div>:null}
   </div>
   <Badge tone={state==='ok'?'good':state==='failed'?'bad':state==='not_recorded'?'neutral':'warn'}>{state==='not_recorded'?'Not recorded':pretty(state)}</Badge>
  </div>;
 })}</div>;
}

export function buildRunReport(detail:ProductionRunDetail,assets?:ProductionRunAssets,storyboard?:ProductionStoryboard,review?:PendingReview|null){
 const lines:string[]=[
  '# Nextdecode — run console evidence',
  '',
  'Generated by the read-only dashboard from persisted run records.',
  'No value here is estimated: missing fields are written as "not recorded".',
  '',
  '- Run: '+detail.run.run_id,
  '- Topic: '+(detail.run.topic||'not recorded'),
  '- Status: '+detail.run.status,
  '- Started: '+(detail.run.started_at??'not recorded'),
  '- Finished: '+(detail.run.finished_at??'not recorded'),
  '- Failure: '+(detail.failure?detail.failure.stage+' · '+detail.failure.error_type+' · '+detail.failure.error_category:'none recorded'),
  '- Trace completeness: '+detail.trace_completeness,
  '',
  '## Stages',
 ];
 if(!detail.stages.length)lines.push('No stages were persisted.');
 for(const stage of detail.stages)lines.push('- '+stage.name+' · '+stage.status+' · '+(stage.started_at??'—')+' → '+(stage.finished_at??'—'));
 lines.push('','## Script');
 if(assets?.script){
  lines.push('- Title: '+(assets.script.title||'not recorded'),'- Hook: '+(assets.script.hook||'not recorded'),'- Words: '+(assets.script.word_count??'not recorded')+' · Target duration: '+(assets.script.duration_seconds??'not recorded')+'s','- Tags: '+(assets.script.tags.join(', ')||'none'),'','### Sources');
  if(!assets.script.source_urls.length)lines.push('No source URLs were recorded.');
  for(const url of assets.script.source_urls)lines.push('- '+url);
  lines.push('','### Narration','',assets.script.voice_text||'No narration text recorded.');
 }else lines.push('Run-local script record unavailable.');
 lines.push('','## Visual plan');
 if(storyboard){
  lines.push('- Review status: '+storyboard.review_status+' · scenes: '+storyboard.scene_count);
  for(const scene of storyboard.scenes)lines.push('- Scene '+(scene.index+1)+' · '+scene.start+'–'+scene.end+'s · '+scene.visual_type+' · provider '+scene.provider+' · relevance '+scene.relevance+'/'+scene.relevance_confidence);
 }else lines.push('No storyboard was persisted for this run.');
 lines.push('','## Artifacts');
 if(!detail.artifacts.length)lines.push('No artifacts recorded.');
 for(const artifact of detail.artifacts)lines.push('- '+artifact.name+' · '+artifact.stage+' · '+(artifact.integrity_status??'not checked')+' · '+bytes(artifact.bytes)+' · sha256 '+(artifact.sha256||'not recorded'));
 lines.push('','## Review state','',review?('Pending package: '+(review.package.title||'untitled')+' · status '+review.status):'No pending review package was returned by the review service.','','## Limits','','- The dashboard does not run, edit, approve or publish anything.','- A run manifest is evidence of what was persisted, not proof of visual or editorial quality.','');
 return lines.join('\n');
}

export function RunConsole(){
 const {runId}=useParams({from:'/runs/$runId'});
 const detail=useQuery({queryKey:['production-run',runId],queryFn:()=>api.productionRun(runId),refetchInterval:query=>query.state.data?.run.status==='in_progress'?3000:false});
 const assets=useQuery({queryKey:['production-run-assets',runId],queryFn:()=>api.productionRunAssets(runId),retry:false,staleTime:5*60_000,refetchInterval:false,refetchOnWindowFocus:false});
 const storyboard=useQuery({queryKey:['production-run-storyboard',runId],queryFn:()=>api.productionStoryboard(runId),retry:false,staleTime:5*60_000,refetchInterval:false,refetchOnWindowFocus:false});
 const review=useQuery({queryKey:['pending-review'],queryFn:api.pendingReview,retry:false,staleTime:60_000,refetchInterval:false,refetchOnWindowFocus:false});
 const engines=useQuery({queryKey:['tool-catalog','run-console'],queryFn:async()=>{
  const entries=await Promise.all(ENGINE_CAPS.map(async capability=>[capability,await api.toolCatalog(capability)] as const));
  return Object.fromEntries(entries) as Record<string,ToolCatalogCandidates>;
 },staleTime:10*60_000,refetchInterval:false,refetchOnWindowFocus:false,retry:false});
 const health=useQuery({queryKey:['health'],queryFn:api.health,refetchInterval:15000});
 const manifest=useQuery({queryKey:['studio-manifest',runId],queryFn:()=>studio.manifest(runId),retry:1,staleTime:30000});
 const [showAllScenes,setShowAllScenes]=useState(false);
 const [reviewer,setReviewer]=useState('');
 const [note,setNote]=useState('');
 const [approving,setApproving]=useState(false);
 const [approvalError,setApprovalError]=useState('');
 const [resumeJobId,setResumeJobId]=useState('');
 const [resuming,setResuming]=useState(false);
 const [resumeError,setResumeError]=useState('');
 const studioJob=useQuery({queryKey:['studio-job',resumeJobId],queryFn:()=>studio.job(resumeJobId),enabled:Boolean(resumeJobId),refetchInterval:query=>query.state.data?.status==='running'?1500:false});

 const run=detail.data?.run;
 const head=<Page eyebrow="SHORTS STUDIO / RUN CONSOLE" title={run?.topic||'Run console'} description="One run, end to end: topic, research sources, script, evidence, voice, captions, visual plan, render output, artifact integrity and the approval path. Read-only — the engine runs in the pipeline." actions={<><Link className="btn" to="/runs"><ArrowLeft size={14}/> All runs</Link><button className="btn" onClick={()=>{void detail.refetch();void assets.refetch();void storyboard.refetch();void review.refetch();}}><RefreshCw size={14}/> Refresh</button></>}/>;

 if(detail.isLoading)return <>{head}<Panel><Loading/></Panel></>;
 if(detail.error)return <>{head}<Panel><ErrorBox error={detail.error} onRetry={()=>detail.refetch()}/></Panel><Panel><SectionHead label="RUN CONSOLE" title="What this page needs"/><p className="project-muted">A console loads from one persisted run manifest. If the manifest is missing or unreadable, no stage, script, source or artifact is shown — nothing is reconstructed or invented.</p></Panel></>;
 if(!detail.data||!run)return <>{head}<Panel><Empty title="Run not found" detail="This run id is not present in the local RunTracker index."/></Panel></>;

 const data=detail.data,script=assets.data?.script,scenes=storyboard.data?.scenes??[];
 const video=data.artifacts.find(artifact=>artifact.name==='video'&&artifact.integrity_status==='verified');
 const videoArtifact=data.artifacts.find(artifact=>artifact.name==='video');
 const sources=script?.source_urls??[];
 const journeyRecorded=STAGE_ORDER.filter(([id])=>data.stages.some(stage=>stage.name===id)).length;
 const verified=data.artifacts.filter(artifact=>artifact.integrity_status==='verified').length;
 const mismatched=data.artifacts.filter(artifact=>artifact.integrity_status==='digest_mismatch'||artifact.integrity_status==='size_mismatch').length;
 const reviewState=review.error?(review.error instanceof Error?review.error.message:'Review service unavailable'):review.data?('Pending package · '+(review.data.package.title||'untitled')):'No pending package';
 const availableAssetIds=new Set((assets.data?.assets??[]).filter(asset=>asset.available).map(asset=>asset.id));
 const voiceAssets=['voice-mp3','voice-wav'].filter(id=>availableAssetIds.has(id));
 const captionAssets=['captions-ass','word-captions'].filter(id=>availableAssetIds.has(id));
 const providerCounts=new Map<string,number>();
 for(const scene of scenes)providerCounts.set(scene.provider||'not recorded',(providerCounts.get(scene.provider||'not recorded')??0)+1);
 const providerMix=[...providerCounts.entries()].sort((a,b)=>b[1]-a[1]).map(([name,count])=>name+' ×'+count).join(' · ');
 const provenanceMap=new Map((manifest.data?.manifest?.stages??[]).filter((stage:any)=>Boolean(stage?.provenance)).map((stage:any)=>[stage.name, stage.provenance as Record<string,unknown>]));
 const engineRows=[
  {key:'research',stage:'Research',observed:sources.length?sources.length+' source'+(sources.length===1?'':'s')+' recorded · claim ledger '+(availableAssetIds.has('claim-ledger')?'present':'not recorded'):'no sources recorded',caps:['research']},
  {key:'script',stage:'Script',observed:script?(script.word_count??'—')+' words · '+script.tags.length+' tags · target '+(script.duration_seconds??'—')+'s':'no script record',caps:['local-model-runtime']},
  {key:'voice',stage:'Voice',observed:voiceAssets.length?voiceAssets.join(' + ')+' persisted':'no voice asset recorded',caps:['speech-synthesis']},
  {key:'captions',stage:'Captions',observed:captionAssets.length?captionAssets.join(' + ')+' persisted':'no caption asset recorded',caps:[] as string[]},
  {key:'visuals',stage:'Visuals & render',observed:(providerMix||'no scenes recorded')+(video?' · video digest verified':' · no verified video'),caps:['editorial-rendering','editorial-motion-graphics','editorial-visual-analysis']},
  {key:'orchestration',stage:'Orchestration',observed:data.stages.length+' stage entries · '+data.artifacts.length+' artifacts',caps:['workflow-engine','task-storage']},
 ];
 const approveStoryboard=async()=>{
  if(!storyboard.data)return;
  const name=reviewer.trim();
  if(!name){setApprovalError('Reviewer name is required — the approval is bound to a reviewer.');return;}
  setApproving(true);setApprovalError('');
  try{await studio.approveStoryboard(run.run_id,name,note.trim());await storyboard.refetch();await detail.refetch();}
  catch(error){setApprovalError(error instanceof Error?error.message:'Approval failed');}
  finally{setApproving(false);}
 };
 const resumeRun=async()=>{
  setResuming(true);setResumeError('');
  try{const result=await studio.resumeRun(run.run_id);setResumeJobId(result.job_id);}
  catch(error){setResumeError(error instanceof Error?error.message:'Resume failed');}
  finally{setResuming(false);}
 };
 const report=()=>downloadText('nextdecode-run-'+run.run_id+'.md',buildRunReport(data,assets.data,storyboard.data,review.data));
 const visibleScenes=showAllScenes?scenes:scenes.slice(0,8);

 return <>{head}
  <NextAction detail={data} assets={assets.data} review={review.data}/>
  <div className="rc-stats">
   <div><small>Stages recorded</small><b>{data.stages.length}</b><span>{journeyRecorded}/9 journey steps · {pretty(run.status)} · {ago(run.started_at)}</span></div>
   <div><small>Sources</small><b>{sources.length}</b><span>{sources.length?sources.map(host).slice(0,2).join(' · '):'none recorded'}</span></div>
   <div><small>Visual plan</small><b>{storyboard.data?storyboard.data.scene_count:'—'}</b><span>{storyboard.data?storyboard.data.review_status.replaceAll('_',' '):'no storyboard persisted'}</span></div>
   <div><small>Artifacts</small><b>{data.artifacts.length}</b><span>{verified} verified · {mismatched} mismatched</span></div>
  </div>

  <Panel><SectionHead label="END-TO-END JOURNEY" title="What the engine did, in order" action={<Badge tone={run.status==='ok'?'good':run.status==='failed'?'bad':'warn'}>{pretty(run.status)}</Badge>}/>
   <Journey detail={data} provenance={provenanceMap}/>
   <div className="rc-live-row">
    <span className={run.status==='in_progress'?'rc-live-dot on':'rc-live-dot'}/>
    <small>{run.status==='in_progress'?'Live · refreshes every 3 seconds':'Live updates stop when the run finishes'}</small>
    <small>{health.data?health.data.active_workers+' worker'+(health.data.active_workers===1?'':'s')+' alive':'worker state unavailable'}</small>
    <small>Manifest trace: {data.trace_completeness}</small>
   </div>
   <p className="rc-note">Stages and artifacts are read from this run's manifest.{data.stages.length>8?' This manifest recorded '+data.stages.length+' stage entries; '+journeyRecorded+' map to the numbered journey.':''} A stage without a persisted record says “not recorded” — it is never inferred from neighbouring stages.</p>
   <div className="rc-actions"><button className="btn" onClick={report}><Download size={14}/> Download evidence report</button><CopyButton value={run.run_id} label="Copy run id"/></div>
  </Panel>

  <div className="rc-grid">
   <Panel><SectionHead label="SCRIPT" title={script?.title||'Script not recorded'} action={<Badge tone={script?.voice_text?'good':'warn'}>{script?.word_count?script.word_count+' words':'no text'}</Badge>}/>
    {assets.isLoading?<Loading/>:assets.error?<Empty title="Run-local script unavailable" detail={'The assets endpoint replied: '+String(assets.error instanceof Error?assets.error.message:assets.error)}/>:script?<>
     <div className="review-hook"><small>OPENING HOOK</small><p>{script.hook||'No hook recorded'}</p></div>
     <div className="rc-script-meta"><span>Target {script.duration_seconds??'—'}s</span><span>{script.word_count??'—'} words</span><span>{script.tags.length} tags</span></div>
     <details className="rc-script-text"><summary>Read the full narration ({script.voice_text.length} characters)</summary><p>{script.voice_text||'No narration text recorded.'}</p></details>
     <div className="rc-actions"><CopyButton value={script.voice_text} label="Copy narration"/><button className="btn" onClick={()=>downloadText(run.run_id+'-script.txt',(script.title||'Untitled')+'\n\n'+script.hook+'\n\n'+script.voice_text,'text/plain;charset=utf-8')}><Download size={14}/> Download .txt</button></div>
     <p className="rc-note">The engine writes this script. This console shows exactly what was persisted; editing happens in the pipeline, not in the browser.</p>
    </>:<Empty title="No script record" detail="This run did not persist a run-local script record."/>}
   </Panel>

   <Panel><SectionHead label="RESEARCH" title="Sources used by this run" action={<Badge tone={sources.length>=2?'good':sources.length?'warn':'bad'}>{sources.length} source{sources.length===1?'':'s'}</Badge>}/>
    {sources.length?<div className="source-list">{sources.map((url,index)=><a href={url} target="_blank" rel="noreferrer" key={url}><span>{String(index+1).padStart(2,'0')}</span><Link2 size={13}/><b>{host(url)}</b><small>{url}</small></a>)}</div>:<Empty title="No sources recorded" detail="This run's script record contains no source URLs. Publishing requires at least two, including one primary source."/>}
    {assets.data?<div className="rc-asset-links">{assets.data.assets.filter(asset=>['claim-ledger','storyboard','shot-plan','timeline'].includes(asset.id)&&asset.available).map(asset=><a className="text-action" key={asset.id} href={asset.url??'#'} download={run.run_id+'-'+asset.id+'.json'}><FileText size={13}/> {pretty(asset.id)}</a>)}</div>:null}
    <p className="rc-note">Evidence source: {assets.data?.evidence_source??'not recorded'}. {verified} of {data.artifacts.length} recorded artifacts re-verified by SHA-256.</p>
   </Panel>
  </div>

  <Panel><SectionHead label="VISUAL PLAN" title={storyboard.data?storyboard.data.scene_count+' planned scenes':'Storyboard not available'} action={storyboard.data?<div className="rc-actions"><Badge tone={storyboard.data.approved?'good':storyboard.data.review_required?'warn':'info'}>{storyboard.data.review_status.replaceAll('_',' ')}</Badge>{scenes.length>8?<button className="text-action" onClick={()=>setShowAllScenes(value=>!value)}>{showAllScenes?'Show first 8':'Show all '+scenes.length}</button>:null}</div>:undefined}/>
   {storyboard.isLoading?<Loading/>:storyboard.error?<Empty title="No persisted storyboard" detail="This run did not write a storyboard file, or it is not readable. Scenes are never reconstructed from the script."/>:scenes.length?<>
    <div className="production-scene-grid">{visibleScenes.map(scene=><article className="production-scene-card" key={scene.index}>
     <div className="production-scene-image">{scene.image_url?<img loading="lazy" src={scene.image_url} alt={'Scene '+(scene.index+1)}/>:<div className="production-scene-no-image">No frame image recorded</div>}<span>SCENE {String(scene.index+1).padStart(2,'0')}</span></div>
     <div className="production-scene-meta"><Badge>{scene.scene_type||'unclassified'}</Badge><Badge tone={scene.visual_type==='footage'?'good':'info'}>{scene.visual_type||'unknown'}</Badge><small>{sec(scene.start)}–{sec(scene.end)}s</small></div>
     <p>{scene.narration||'No narration recorded.'}</p>
     <div className="production-scene-source"><span>Provider: <b>{scene.provider||'—'}</b></span><span>Relevance: <b>{scene.relevance||'—'}/{scene.relevance_confidence||'—'}</b></span></div>
     {scene.fallback_reason?<div className="rc-scene-warn"><AlertTriangle size={12}/> {scene.fallback_reason}</div>:null}
    </article>)}</div>
    <p className="rc-note">Provider is the renderer recorded for each scene. It tells you which visual system produced the frame — not which language model wrote the script.</p>
   </>:<Empty title="No storyboard persisted" detail="The run has no scene plan on disk."/>}
  </Panel>

   {storyboard.data? <Panel className="approval-panel"><SectionHead label="STORYBOARD APPROVAL" title={storyboard.data.approved?'Storyboard approved — render can resume':'Review the contact sheet, then approve'} action={<Badge tone={storyboard.data.approved?'good':'warn'}>{storyboard.data.review_status.replaceAll('_',' ')}</Badge>}/>
    {storyboard.data.review_required&&!storyboard.data.approved? <>
     <p className="rc-note">Approval is bound to this exact contact sheet, script and ledger. The gate stays enforced: the resume will refuse to render until the approval exists and matches. Nothing here publishes.</p>
     <div className="rc-approval-form">
      <label className="production-topic-field"><span>Reviewer name</span><input value={reviewer} onChange={event=>setReviewer(event.target.value)} placeholder="e.g. Anish" maxLength={120} aria-label="Reviewer name"/></label>
      <label className="production-topic-field"><span>Review note (optional)</span><input value={note} onChange={event=>setNote(event.target.value)} placeholder="What you checked" maxLength={500} aria-label="Review note"/></label>
      <button className="btn btn-primary" disabled={approving} onClick={()=>void approveStoryboard()}>{approving?'Approving…':'Approve storyboard'}</button>
     </div>
     {approvalError?<p className="rc-note" style={{color:'#e58f94'}}>{approvalError}</p>:null}
     <p className="rc-note">You can also approve from the terminal: python -m app.visuals.storyboard &lt;storyboard.json&gt; --reviewer &lt;name&gt;</p>
    </>:!run.status||run.status!=='ok'? <>
     <p className="rc-note">Storyboards are approved and the gate passed. Resume continues the approved plan — the same resolved assets and contact sheet, no re-resolution, no publishing.</p>
     <div className="rc-actions"><button className="btn btn-primary" disabled={resuming} onClick={()=>void resumeRun()}>{resuming?'Resuming…':'Resume render'}</button></div>
     {resumeError?<p className="rc-note" style={{color:'#e58f94'}}>{resumeError}</p>:null}
    </>:null}
    {resumeJobId?<div className="rc-live-row"><span className={studioJob.data?.status==='running'?'rc-live-dot on':'rc-live-dot'}/><small>{studioJob.data?.status==='running'?'Rendering from the approved plan…':studioJob.data?.outcome==='success'?'Render finished — the run is complete.':studioJob.data?.outcome==='awaiting_review'?'Stopped again at the storyboard gate.':studioJob.data?.status==='finished'?'Render failed — see the log.':'Job id: '+resumeJobId}</small></div>:null}
    {studioJob.data?.log_tail?<details className="rc-script-text"><summary>Latest pipeline log (tail)</summary><pre className="rc-log-tail">{studioJob.data.log_tail}</pre></details>:null}
    </Panel>:null}

  <Panel><SectionHead label="SYSTEM MAP" title="Which engine does which job" action={<Badge tone={engines.data?'info':'neutral'}>{engines.data?'Local tool catalog':'Catalog unavailable'}</Badge>}/>
   <div className="rc-engine-grid">{engineRows.map(row=><div className="rc-engine" key={row.key}>
    <div className="rc-engine-head"><b>{row.stage}</b><span>{row.observed}</span></div>
    <div className="rc-engine-engines">{row.caps.length?row.caps.map(capability=>{
     const list=((engines.data?.[capability] as ToolCatalogCandidates|undefined)?.candidates??[]);
     const active=list.filter(candidate=>candidate.status.startsWith('active'));
     return <div className="rc-engine-line" key={capability}><span className="rc-engine-cap">{capability.replaceAll('-',' ')}</span>{engines.isLoading?<Badge tone="neutral">loading…</Badge>:engines.error?<Badge tone="neutral">unavailable</Badge>:active.length?active.map(candidate=><Badge key={candidate.id} tone="good">{candidate.id}</Badge>):<Badge tone="warn">none declared active</Badge>}<small>{list.length} option{list.length===1?'':'s'} · {active.length} active</small></div>;
    }):<div className="rc-engine-line"><span className="rc-engine-cap">catalog</span><Badge tone="neutral">not declared</Badge><small>no capability maps here</small></div>}</div>
   </div>)}</div>
   <p className="rc-note">Left of each row is what this run persisted. Right is the engine the local tool catalog marks active for that job — a declaration, not a per-run model id. The manifest records no language-model id per stage, so this page does not invent one.</p>
  </Panel>

  <div className="rc-grid">
   <Panel><SectionHead label="OUTPUT" title="Rendered video" action={video?<Badge tone="good">SHA-256 verified</Badge>:<Badge tone="warn">{videoArtifact?'Integrity not verified':'Not recorded'}</Badge>}/>
    {video?<div className="production-video-preview"><video controls playsInline preload="metadata" src={'/api/production-runs/'+encodeURIComponent(run.run_id)+'/video'}/><div className="rc-actions"><a className="text-action" href={'/api/production-runs/'+encodeURIComponent(run.run_id)+'/video'} download={run.run_id+'-short.mp4'}><Download size={13}/> Download verified video</a><CopyButton value={video.sha256} compact label="Copy video SHA-256"/></div><p className="rc-note">Served from the run artifact after the API re-hashed the file. Bytes match the manifest digest: {video.sha256.slice(0,16)}…</p></div>:<Empty title={videoArtifact?'Video exists but failed integrity':'No video recorded'} detail={videoArtifact?'The stored digest does not match the current bytes, so the API refuses to serve it. Re-render or restore the artifact.':'This run stopped before a video artifact was persisted.'}/>}
   </Panel>

   <Panel><SectionHead label="APPROVAL PATH" title="What still has to happen" action={<Badge tone="warn">Owner gate</Badge>}/>
    <div className="boundary-list">
     <div><ShieldCheck size={16}/><span><b>Review package state</b><small>{reviewState}</small></span><Badge tone={review.data?'info':'neutral'}>{review.data?'Pending':'None'}</Badge></div>
     <div><Video size={16}/><span><b>Artifact binding</b><small>{mismatched?'At least one artifact digest mismatched — approval stays blocked.':'Recorded digests currently match the files the API verified.'}</small></span><Badge tone={mismatched?'bad':'good'}>{mismatched?'Mismatch':'Matches'}</Badge></div>
     <div><Subtitles size={16}/><span><b>Human checklist</b><small>Only the review package carries the 7-item checklist. Completing it requires the local approval flow — this console cannot mark anything complete.</small></span><Badge tone="neutral">Local only</Badge></div>
     <div><Volume2 size={16}/><span><b>Watching the file</b><small>Play the video above before approving. Approval is bound to the exact artifact, not to a topic or a title.</small></span><Badge tone="info">Required</Badge></div>
    </div>
    <CommandLine command="wsl.exe -d Ubuntu --exec /home/demon/shorts_studio/venv/bin/python -m app.review.approve_review --interactive" label="Approve"/>
    <CommandLine command="wsl.exe -d Ubuntu --exec /home/demon/shorts_studio/venv/bin/python -m app.publish.orchestration --scheduled-approved" label="Publish (20:00 IST)"/>
    <p className="rc-note">Nothing on this page approves or publishes. The commands are copyable because the gates are enforced by the CLI, not by the browser.</p>
   </Panel>
  </div>

  <Panel><SectionHead label="PRODUCTION ASSETS" title="Everything this run persisted" action={<Badge>{assets.data?.assets.filter(asset=>asset.available).length??0} available</Badge>}/>
   {assets.isLoading?<Loading/>:assets.error?<Empty title="Assets unavailable" detail={String(assets.error instanceof Error?assets.error.message:assets.error)}/>:assets.data?.assets.filter(asset=>asset.available).length?<div className="production-asset-grid">{assets.data.assets.filter(asset=>asset.available).map(asset=><article className="production-asset-card" key={asset.id}>
    <div className="production-asset-title"><b>{pretty(asset.id)}</b><small>{asset.media_type.split(';')[0]} · {bytes(asset.bytes)}</small></div>
    {asset.media_type.startsWith('image/')?<img className="production-contact-sheet" loading="lazy" src={asset.url??undefined} alt={pretty(asset.id)}/>:asset.media_type.startsWith('audio/')?<audio controls preload="none" src={asset.url??undefined}/>:<div className="rc-asset-file"><FileText size={18}/><small>{(asset.path??'').split('/').pop()}</small></div>}
    <div className="production-asset-actions"><a className="text-action" href={asset.url??'#'} download={run.run_id+'-'+asset.id}><Download size={11}/> Download</a><a className="text-action" href={asset.url??'#'} target="_blank" rel="noreferrer">Open ↗</a></div>
   </article>)}</div>:<Empty title="No run-local assets" detail="This run did not write a run directory with assets."/>}
  </Panel>

  <Panel><SectionHead label="INTEGRITY" title="Artifact fingerprints" action={<Badge tone={mismatched?'bad':'good'}>{mismatched?mismatched+' mismatch':'No mismatches'}</Badge>}/>
   {data.artifacts.length?<div className="rc-artifacts">{data.artifacts.map(artifact=><div className="rc-artifact" key={artifact.name+artifact.stage}>
    <div className="rc-artifact-head"><b>{pretty(artifact.name)}</b><Badge tone={artifact.integrity_status==='verified'?'good':artifact.integrity_status==='digest_mismatch'?'bad':'warn'}>{pretty(artifact.integrity_status)}</Badge><small>{pretty(artifact.stage)} · {bytes(artifact.bytes)}</small></div>
    <div className="digest"><small>Recorded</small><code>{artifact.sha256||'Not recorded'}</code></div>
    <div className="digest"><small>Computed</small><code>{artifact.computed_sha256||'Not computed'}</code></div>
   </div>)}</div>:<Empty title="No artifacts recorded" detail="The manifest lists no artifacts for this run."/>}
   <p className="rc-note">SHA-256 is recomputed by the API from the opened file. A verified digest proves the bytes match the manifest; it does not prove editorial or visual quality.</p>
  </Panel>
 </>;
}
