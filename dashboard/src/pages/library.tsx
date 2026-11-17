import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {AlertTriangle,CheckCircle2,Clapperboard,Copy,Download,Film,Layers3,RefreshCw,ShieldAlert} from 'lucide-react';
import {Link} from '@tanstack/react-router';
import {studio,type LibraryItem} from '../api';
import {Page,Panel,Badge,Loading,ErrorBox,Empty,SectionHead,CopyButton} from '../components';

const prettyDuration=(seconds?:number|null)=>{if(seconds==null)return null;const whole=Math.round(seconds);const minutes=Math.floor(whole/60);const rest=whole%60;return minutes?`${minutes}m ${rest}s`:`${rest}s`;};

function PlatformCopy({label,value}:{label:string;value?:string|null}){
 if(!value)return null;
 return <div className="platform-copy-block"><div className="platform-copy-head"><small>{label}</small><CopyButton value={value} compact label="Copy"/></div><p>{value}</p></div>;
}

function ShortCard({item}:{item:LibraryItem}){
 const[videoError,setVideoError]=useState(false);
 const runVideoUrl="/api/production-runs/"+encodeURIComponent(item.run_id)+"/video";
 const completed=item.status==='ok'&&item.artifacts.video;
 return <Panel className={completed?'library-card library-card-ok':'library-card library-card-pending'}>
  <div className="library-card-media">
   {completed?<video className="library-video" src={runVideoUrl} controls playsInline preload="metadata" onError={()=>setVideoError(true)}/>:<div className="library-no-video"><ShieldAlert size={26}/><b>No played video</b><small>{item.status==='awaiting_review'?'Parked for review — approve and resume to render':'Render not completed for this run'}</small></div>}
   {videoError?<p className="rc-note" style={{color:'#e58f94'}}>Integrity check failed for this video (digest mismatch). It cannot be played or downloaded until a digest-verified re-render lands.</p>:null}
   <div className="rc-actions"><a className="text-action" href={runVideoUrl} download={item.run_id+'.mp4'}><Download size={12}/> Download mp4</a><Link className="text-action" to="/runs/$runId" params={{runId:item.run_id}}>Open console</Link></div>
  </div>
  <div className="library-card-body">
   <div className="production-storyboard-actions"><Badge tone={item.status==='ok'?'good':'warn'}>{item.status==='awaiting_review'?'Awaiting review':item.status}</Badge><small>{new Date(item.started_at ?? item.finished_at ?? '').toLocaleDateString(undefined,{month:'short',day:'numeric'})}</small></div>
   <h2 className="library-title">{item.title??item.topic??'Untitled engine run'}</h2>
   {item.tags.length?<div className="library-tags">{item.tags.slice(0,4).map(tag=><Badge key={tag} tone="neutral">{tag}</Badge>)}</div>:null}
   {item.hook?<div className="review-hook"><small>OPENING HOOK</small><p>{item.hook}</p></div>:null}
   <div className="rc-script-meta"><span>{prettyDuration(item.duration_seconds)??'—'}</span><span>{item.word_count??'—'} words</span><span>{item.artifacts_count} artifacts</span></div>
   <PlatformCopy label="YouTube description" value={item.platform_copy.youtube_description}/>
   <PlatformCopy label="Instagram caption" value={item.platform_copy.instagram_caption}/>
   {item.platform_copy.facebook_title||item.platform_copy.facebook_description?<PlatformCopy label="Facebook" value={[item.platform_copy.facebook_title,item.platform_copy.facebook_description].filter(Boolean).join('\n\n')}/>:null}
   {item.status!=='ok'?<div className="studio-note">Ready when you are — this run is parked at <b>{item.status}</b>. Open the console to review the contact sheet and approve the render.</div>:null}
  </div>
 </Panel>;
}

export function Library(){
 const q=useQuery({queryKey:['studio-library'],queryFn:studio.library,refetchInterval:30000});
 const items=q.data?.items??[];
 const ready=items.filter(item=>item.status==='ok'&&item.artifacts.video);
 const pending=items.filter(item=>item.status==='awaiting_review'&&item.artifacts.storyboard);
 const untouched=items.filter(item=>!item.artifacts.video&&item.status!=='awaiting_review'&&item.status!=='ok').slice(0,3);
 return <><Page eyebrow="CREATE / EVERYTHING THE ENGINE MADE" title="Studio library" description="Every video, script and post the engine has produced — one place to preview, verify and read what was made. Failed runs are deliberately not listed; see Work queue for triage." actions={<button className="btn" onClick={()=>q.refetch()}><RefreshCw size={14}/> Refresh</button>}/>
 {q.isLoading?<Panel><Loading/></Panel>:q.error?<ErrorBox error={q.error} onRetry={()=>q.refetch()}/>:<>
  <div className="page-section"><div className="section-head"><div><span className="eyebrow">VERIFIED DELIVERIES</span><h3>{ready.length} Short{ready.length===1?'':'s'} ready to watch</h3><small>Only runs with a digest-verified video are listed — anything unverified stays honest about itself.</small></div></div>
  {ready.length?<div className="library-grid">{ready.map(item=><ShortCard key={item.run_id} item={item}/>)}</div>:<Empty title="No verified Shorts yet" detail="Runs that complete the gate pass end to end land here with the video, the script and the post copy."/>}
  </div>
  {pending.length?<div className="page-section"><div className="section-head"><div><span className="eyebrow">AWAITING YOUR REVIEW</span><h3>{pending.length} Short{pending.length===1?'':'s'} parked at the storyboard gate</h3><small>Each has a contact sheet ready. Open the run console to approve and resume.</small></div></div>
   <div className="library-grid">{pending.map(item=><ShortCard key={item.run_id} item={item}/>)}</div></div>:null}
  <div className="studio-note">A note on scope: this page shows engine-created deliveries and their exact recorded state. It never shows a metric, view count or upload status that does not exist yet — anything missing simply says nothing.</div>
 </>}
 </>;
}
