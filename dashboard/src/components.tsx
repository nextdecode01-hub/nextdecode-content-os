import {Component,useEffect,useRef,useState,type ReactNode} from 'react';
import {clsx} from 'clsx';
import {AlertTriangle,Check,Copy,Download} from 'lucide-react';
import {ApiError} from './api';

/* Clipboard: works on localhost, LAN IPs and locked-down browsers alike.
   The async Clipboard API is unavailable on insecure origins, so fall back to
   the legacy selection copy. Returns a real boolean — never throws. */
export async function copyText(text:string):Promise<boolean>{
 if(!text)return false;
 try{
  if(navigator.clipboard&&window.isSecureContext){await navigator.clipboard.writeText(text);return true}
 }catch{/* fall through to legacy path */}
 try{
  const area=document.createElement('textarea');
  area.value=text;area.setAttribute('readonly','');
  area.style.cssText='position:fixed;top:0;left:-9999px;opacity:0;pointer-events:none';
  document.body.appendChild(area);
  const previous=document.getSelection();
  const saved=previous&&previous.rangeCount>0?previous.getRangeAt(0):null;
  area.select();area.setSelectionRange(0,text.length);
  const ok=document.execCommand('copy');
  document.body.removeChild(area);
  if(saved&&previous){previous.removeAllRanges();previous.addRange(saved)}
  return ok;
 }catch{return false}
}

export function CopyButton({value,label='Copy',compact=false,className}:{value:string;label?:string;compact?:boolean;className?:string}){
 const [state,setState]=useState<'idle'|'copied'|'failed'>('idle');
 const timer=useRef<number|undefined>(undefined);
 useEffect(()=>()=>{if(timer.current)window.clearTimeout(timer.current)},[]);
 const run=async()=>{
  const ok=await copyText(value);
  setState(ok?'copied':'failed');
  if(timer.current)window.clearTimeout(timer.current);
  timer.current=window.setTimeout(()=>setState('idle'),2200);
 };
 const Icon=state==='copied'?Check:state==='failed'?AlertTriangle:Copy;
 const text=state==='copied'?'Copied':state==='failed'?'Select it':label;
 return <button
   type="button"
   className={clsx('copy-btn',compact&&'compact',state==='copied'&&'copied',state==='failed'&&'failed',className)}
   onClick={run}
   aria-label={state==='copied'?`${label} — copied to clipboard`:state==='failed'?`${label} failed — select the text and press Ctrl+C`:label}
   title={state==='failed'?'Clipboard blocked — select the text and press Ctrl+C':label}>
  <Icon size={compact?14:15}/>
  {!compact&&<span aria-live="polite">{text}</span>}
 </button>
}

export function CommandLine({command,label='Command'}:{command:string;label?:string}){
 return <div className="digest command-line"><small>{label}</small><code title={command}>{command}</code><CopyButton value={command} label="Copy"/></div>
}

export function downloadText(filename:string,contents:string,mime='text/markdown;charset=utf-8'){
 try{
  const blob=new Blob([contents],{type:mime});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;a.download=filename;
  document.body.appendChild(a);a.click();a.remove();
  window.setTimeout(()=>URL.revokeObjectURL(url),2000);
  return true;
 }catch{return false}
}

export function downloadScript(filename:string,contents:string){
 return downloadText(filename,contents,'text/x-shellscript;charset=utf-8');
}

/* Publish control. Deliberately prepares the locally-gated command instead of
   executing an upload from the browser: the CLI re-checks the approval, the
   artifact digest and (for the scheduled path) the 20:00 IST window. */
export type PublishMode='manual'|'auto';
const PUBLISH_PY='/home/demon/shorts_studio/venv/bin/python';
export function publishCommand(mode:PublishMode){
 return mode==='auto'
  ? `wsl.exe -d Ubuntu --exec ${PUBLISH_PY} -m app.publish.orchestration --scheduled-approved`
  : `wsl.exe -d Ubuntu --exec env PUBLISH_MODE=publish AUTO_PUBLISH_APPROVED=true ${PUBLISH_PY} -m app.publish.orchestration`;
}
export function usePublishMode(){
 const [mode,setMode]=useState<PublishMode>(()=>{
  try{return localStorage.getItem('nd-publish-mode')==='manual'?'manual':'auto'}catch{return 'auto'}
 });
 const pick=(next:PublishMode)=>{setMode(next);try{localStorage.setItem('nd-publish-mode',next)}catch{/* private mode */}};
 return [mode,pick] as const;
}
export function PublishControl({blocked,reason,readyNote}:{blocked:boolean;reason?:string;readyNote?:string}){
 const [mode,pick]=usePublishMode();
 const command=publishCommand(mode);
 const script=`#!/usr/bin/env bash\n# NEXTDECODE — ${mode==='auto'?'scheduled 20:00 IST':'manual'} publish\n# Run only after you approved the exact review package for today.\nset -euo pipefail\ncd /home/demon/shorts_studio\n${mode==='auto'?'':'export PUBLISH_MODE=publish\nexport AUTO_PUBLISH_APPROVED=true\n'}exec ${PUBLISH_PY} -m app.publish.orchestration${mode==='auto'?' --scheduled-approved':''}\n`;
 return <div className="publish-control">
  <div className="publish-mode" role="radiogroup" aria-label="Publish mode">
   <button type="button" role="radio" aria-checked={mode==='manual'} className={clsx(mode==='manual'&&'active')} onClick={()=>pick('manual')}>
    <span className="publish-mode-name"><Download size={15}/> Manual</span>
    <small>You run it now, after same-day approval. No scheduler wait.</small>
   </button>
   <button type="button" role="radio" aria-checked={mode==='auto'} className={clsx(mode==='auto'&&'active')} onClick={()=>pick('auto')}>
    <span className="publish-mode-name">⏱ Automatic</span>
    <small>Runs only inside the 20:00–20:59 IST window; outside it the CLI refuses.</small>
   </button>
  </div>
  <div className="publish-state" data-blocked={blocked?'true':'false'}>
   <span className="publish-state-dot"/>
   <div>
    <b>{blocked?'Publishing is locked by failing gates':'Commands prepared — execution still needs the terminal'}</b>
    <small>{blocked?(reason||'A required review gate fails. The command will exit without uploading.'):(readyNote||'The CLI re-verifies approval, digest and time window before any upload.')}</small>
   </div>
  </div>
  <CommandLine command={command} label={mode==='auto'?'Scheduled command':'Manual command'}/>
  <div className="publish-actions">
   <CopyButton value={command} label="Copy command"/>
   <button type="button" className="btn" onClick={()=>downloadScript(mode==='auto'?'nextdecode-publish-scheduled.sh':'nextdecode-publish-manual.sh',script)}>
    <Download size={14}/> Download .sh
   </button>
  </div>
  <p className="publish-note">This dashboard does not upload. It prepares the exact gated local command and script — the browser has no publish endpoint, and the protected-action boundary stays with the CLI and the 20:00 IST scheduler.</p>
 </div>
}
type ErrorBoundaryState={failed:boolean};
export class ErrorBoundary extends Component<{children:ReactNode},ErrorBoundaryState>{
 state:ErrorBoundaryState={failed:false};
 static getDerivedStateFromError(){return {failed:true};}
 componentDidCatch(error:Error){console.error('Dashboard route render failed',error);}
 render(){
  if(this.state.failed)return <main className="page"><div className="error" role="alert"><b>This dashboard view could not be displayed</b><p>An unexpected interface error occurred. This screen has not performed any Studio or runtime action.</p><button className="btn" onClick={()=>window.location.reload()}>Reload dashboard</button></div></main>;
  return this.props.children;
 }
}
export function Page({eyebrow,title,description,actions}:{eyebrow:string;title:string;description:string;actions?:ReactNode}){return <div className="page-head"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{actions&&<div className="actions">{actions}</div>}</div>}
export function Panel({children,className}:{children:ReactNode;className?:string}){return <section className={clsx('panel',className)}>{children}</section>}
export function Badge({children,tone='neutral'}:{children:ReactNode;tone?:string}){return <span className={`badge ${tone}`}>{children}</span>}
export function Metric({label,value,detail,icon:Icon,color='violet'}:{label:string;value:string|number;detail:string;icon:any;color?:string}){return <div className="metric"><div className={`metric-icon ${color}`}><Icon size={17}/></div><small>{label}</small><strong>{value}</strong><span>{detail}</span></div>}
export function Loading(){return <div className="loading">Loading live workspace data…</div>}
function errorTitle(status?:number){if(status===401||status===403)return 'Access denied';if(status===404)return 'Record not found';if(status===409)return 'Request conflicts with current state';if(status!==undefined&&status>=500)return 'Live data unavailable';return 'Could not load live data';}
function errorHint(status?:number){if(status===401||status===403)return 'Check the local API and server-side key configuration. Credentials are never displayed.';if(status===404)return 'The requested record was not found. It may have been removed or never created.';if(status===409)return 'The request conflicts with current server state. Inspect the record before retrying.';if(status===400||status===422)return 'The local API rejected this request as invalid.';if(status!==undefined&&status>=500)return 'The local API reported a server-side failure. Retry after checking the API log.';return 'The local API could not be reached. Check that the API server and dashboard proxy are running.';}
export function ErrorBox({error,onRetry}:{error:unknown;onRetry?:()=>void}){const apiError=error instanceof ApiError?error:null;return <div className="error" role="alert"><b>{errorTitle(apiError?.status)}</b><p>{error instanceof Error?error.message:'Unexpected API error'}</p>{apiError&&<small>HTTP {apiError.status} · {apiError.endpoint}{apiError.requestId?' · Request '+apiError.requestId:''}</small>}<small>{errorHint(apiError?.status)}</small>{onRetry&&<div style={{marginTop:12}}><button className="btn" onClick={onRetry}>Retry</button></div>}</div>}
export const reviewIntegrityBlocked=(error:unknown)=>error instanceof ApiError&&error.status===409;
export function ReviewStatusNotice({error,onRetry}:{error:unknown;onRetry?:()=>void}){const blocked=reviewIntegrityBlocked(error),apiError=error instanceof ApiError?error:null;if(blocked)return <div className="error" role="alert"><b>Review package failed integrity verification</b><p>The artifact on disk no longer matches the SHA-256 digest recorded in the review package. Approval stays blocked until the artifact is restored or the package is regenerated.</p><small>review_artifact_hash_mismatch · HTTP 409{apiError?' · '+apiError.endpoint:''}</small>{onRetry&&<div style={{marginTop:12}}><button className="btn" onClick={onRetry}>Retry check</button></div>}</div>;return <div className="notice" role="status"><AlertTriangle size={16}/><span><b>Review service unavailable</b><small>The review package could not be loaded. No approval state was changed.</small></span>{onRetry&&<button className="btn" onClick={onRetry}>Retry</button>}</div>;}
export function Empty({title,detail,action}:{title:string;detail:string;action?:ReactNode}){return <div className="empty"><b>{title}</b><p>{detail}</p>{action?<div className="empty-action">{action}</div>:null}</div>}
export function SectionHead({label,title,action}:{label:string;title:string;action?:ReactNode}){return <div className="section-head"><div><div className="eyebrow">{label}</div><h3>{title}</h3></div>{action}</div>}
