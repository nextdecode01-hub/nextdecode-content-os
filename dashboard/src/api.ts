export type Worker={worker_id:string;hostname:string;pid:number;state:string;started_at:string;heartbeat_at:string;alive:boolean;stale:boolean};
export type Task={task_id:string;plan_id?:string|null;task_type:string;status:string;priority:number;attempts:number;max_attempts:number;created_at:string;updated_at:string;lease_owner?:string|null;lease_until?:string|null;error_code?:string|null;payload_json?:string|null;result_json?:string|null};
export type TaskEvent={event_id:number;task_id:string;event:string;at:string;detail_json?:string|null};
export type StuckTask={task_id:string;task_type:string;lease_owner?:string|null;lease_until?:string|null;attempts:number;updated_at:string;last_execution_heartbeat?:string|null};
export type EventFeed={events:TaskEvent[];next_after_event_id:number};
export type ToolCandidate={id:string;capability:string;role:string;rank:number;deployment:string;license:string;cost_model:string;status:string;strengths:string[];limitations:string[];replacement_for?:string|null;requires_approval:boolean};
export type ToolCatalogIndex={capabilities:string[]};
export type ToolCatalogCandidates={capability:string;candidates:ToolCandidate[]};
export type ProductionRun={run_id:string;topic:string;quality?:string;status:string;started_at?:string|null;finished_at?:string|null;stage_count:number;active_stage?:string|null;artifact_count:number;failure_stage?:string|null;error_type?:string|null;error_category?:string|null};
export type ProductionRunAssets={script:{title:string;hook:string;voice_text:string;word_count?:number;duration_seconds?:number;source_urls:string[];tags:string[]};assets:{id:string;path:string;media_type:string;available:boolean;bytes?:number|null;url?:string|null}[];evidence_source:string};
export type ProductionRunDetail={run:ProductionRun;schema_version?:number;stages:{name:string;started_at?:string|null;finished_at?:string|null;status:string}[];artifacts:{name:string;path?:string|null;sha256:string;computed_sha256?:string|null;bytes?:number|null;actual_bytes?:number|null;stage:string;exists:boolean;metadata_status?:string;integrity_status?:string}[];failure?:{stage:string;error_type:string;error_category:string}|null;promotion?:{status:string;started_at?:string|null;finished_at?:string|null}|null;evidence_source:string;trace_completeness:string;canonical_workflow_linked:boolean};

export type ProductionStoryboardScene={index:number;start?:number;end?:number;narration:string;scene_type:string;visual_type:string;provider:string;asset_id:string;relevance:string;relevance_confidence:string;review_reason:string;fallback_reason:string;relevance_reason:string;image_url?:string|null};
export type ProductionStoryboard={run_id:string;title:string;scene_count:number;review_status:string;approved:boolean;review_required:boolean;review_reasons:string[];summary:Record<string,unknown>;scenes:ProductionStoryboardScene[]};
export type StudioStoryboardScene={id:number;name:string;start:number;end:number;kind:string;description:string;caption:string};
export type StudioStoryboardPayload=Record<string,unknown>&{title:string;target_duration_seconds:number;scenes:StudioStoryboardScene[];studio_version_id:string;studio_content_sha256:string};
export type ApiLiveness={ok:boolean};
export type Health={database:string;database_accessible:boolean;queue_counts:Record<string,number>;total_tasks:number;expired_running_leases:number;workers:Worker[];active_workers:number;stale_workers:number;stopped_workers:number};
export type LegacyJob={status:string;topic?:string;quality?:string;dry_run?:boolean;error?:string;log_tail?:string;log_file?:string;video_path?:string;title?:string;notified?:boolean;created_at?:string;updated_at?:string;started_at?:string;finished_at?:string;[key:string]:unknown};
export type StartProductionResponse={job_id:string;already_running?:boolean};
export type StudioJob={job_id:string;name:string;status:'running'|'finished'|'unknown'|'error';pid?:number;exit_code?:number|null;log_file?:string;log_tail?:string;run_id?:string|null;outcome?:'success'|'failed'|'awaiting_review';started_at?:string};
export type StudioStartResponse={status:string;job_id:string;log_file?:string};
export type StudioApproval={approved:boolean;reviewer:string;note?:string;approved_at?:string;contact_sheet_sha256?:string;review_status?:string;scene_count?:number;scene_digest?:string};
export type ManifestStage={name:string;started_at?:string|null;finished_at?:string|null;status:string;provenance?:Record<string,unknown>};
export type StudioManifest={run_id:string;manifest:Record<string,unknown>&{stages?:ManifestStage[]}};
export type LibraryItem={run_id:string;status:string;topic:string|null;title:string|null;hook:string|null;word_count:number|null;duration_seconds:number|null;tags:string[];platform_copy:{youtube_description?:string|null;instagram_caption?:string|null;facebook_title?:string|null;facebook_description?:string|null};artifacts:{video:boolean;storyboard:boolean;contact_sheet:boolean};artifacts_count:number;started_at?:string|null;finished_at?:string|null};

export type ReviewPackage={status:string;created_at?:string;video_sha256?:string;metadata_sha256?:string;title?:string;content_pillar?:string;script_profile?:string;target_duration_seconds?:number;word_count?:number;word_range?:number[];hook?:string;source_urls?:string[];visuals?:{mode?:string;asset_count?:number};visual_quality_status?:string;platform_copy?:Record<string,string>;checklist?:Record<string,boolean>;benchmark_references?:string[];notes?:string};
export type PendingReview={status:string;review_package_sha256:string;package:ReviewPackage};
export class ApiError extends Error {
 readonly status:number;readonly endpoint:string;readonly requestId?:string;
 constructor(status:number,endpoint:string,detail:string,requestId?:string){super('API '+status+' · '+endpoint+': '+detail);this.name='ApiError';this.status=status;this.endpoint=endpoint;this.requestId=requestId;}
}
function safeDetail(raw:string):string{
 if(!raw.trim())return 'No error detail was returned.';
 try{const body=JSON.parse(raw) as Record<string,unknown>;const value=body.detail??body.error??body.message;
  if(typeof value==='string')return value.replace(/Bearer\s+[^\s,;]+/gi,'Bearer [redacted]').slice(0,240);
  if(value!==undefined)return JSON.stringify(value).slice(0,240);
 }catch{/* Do not echo arbitrary HTML or raw server responses. */}
 return 'The server returned an unreadable error response.';
}
async function request<T>(path:string,init:RequestInit={},notFoundAsNull=false):Promise<T>{
 let response:Response;
 try{response=await fetch('/api'+path,{...init,headers:{Accept:'application/json',...init.headers}});}
 catch(error){if(error instanceof DOMException&&error.name==='AbortError')throw error;throw new Error('Cannot reach the local API for '+path+'. Check that the API server and dashboard proxy are running.');}
 const requestId=response.headers.get('x-request-id')||undefined,raw=await response.text();
 if(notFoundAsNull&&response.status===404)return null as T;
 if(!response.ok)throw new ApiError(response.status,path,safeDetail(raw),requestId);
 if(!raw.trim())throw new ApiError(response.status,path,'The server returned an empty response.',requestId);
 try{return JSON.parse(raw) as T;}catch{throw new ApiError(response.status,path,'The server response was not valid JSON.',requestId);}
}
const get=<T>(path:string)=>request<T>(path);
const post=<T>(path:string,body:unknown)=>request<T>(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});

async function studioRequest<T>(path:string,init:RequestInit={}):Promise<T>{
 let response:Response;
 try{response=await fetch('/studio'+path,{...init,headers:{Accept:'application/json',...init.headers}});}
 catch(error){if(error instanceof DOMException&&error.name==='AbortError')throw error;throw new Error('Cannot reach the Studio write server for '+path+'. Check that it is running on port 5181.');}
 const raw=await response.text();
 if(!response.ok)throw new ApiError(response.status,'/studio'+path,safeDetail(raw));
 if(!raw.trim())throw new ApiError(response.status,'/studio'+path,'The server returned an empty response.');
 try{return JSON.parse(raw) as T;}catch{throw new ApiError(response.status,'/studio'+path,'The server response was not valid JSON.');}
}
const studioGet=<T>(path:string)=>studioRequest<T>(path);
const studioPost=<T>(path:string,body:unknown)=>studioRequest<T>(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
export const studio={
 health:()=>studioGet<{ok:boolean;service:string}>('/health'),
 start:(topic:string)=>studioPost<StudioStartResponse>('/start',{topic}),
 job:(jobId:string)=>studioGet<StudioJob>('/jobs/'+encodeURIComponent(jobId)),
 approveStoryboard:(runId:string,reviewer:string,note?:string)=>studioPost<{status:string;approval:StudioApproval}>('/runs/'+encodeURIComponent(runId)+'/approve-storyboard',{reviewer,note}),
 resumeRun:(runId:string)=>studioPost<StudioStartResponse>('/runs/'+encodeURIComponent(runId)+'/resume',{}),
 library:()=>studioGet<{items:LibraryItem[];source:string}>('/library'),
 manifest:(runId:string)=>studioGet<StudioManifest>('/manifest/'+encodeURIComponent(runId)),
};

export const api={
 health:()=>get<Health>('/autonomy/health'),
 ping:()=>get<ApiLiveness>('/health'),
 tasks:()=>get<{tasks:Task[];limit:number}>('/tasks?limit=200'),
 caps:()=>get<{capabilities:any[]}>('/capabilities'),
 toolCatalog:(capability?:string)=>get<ToolCatalogIndex|ToolCatalogCandidates>(capability?'/tool-catalog?capability='+encodeURIComponent(capability):'/tool-catalog'),
 jobs:()=>get<Record<string,LegacyJob>>('/jobs'),
 startProduction:(topic:string)=>post<StartProductionResponse>('/start',{dry_run:false,topic,quality:'strong'}),
 productionRuns:()=>get<{runs:ProductionRun[];limit:number;source:string}>('/production-runs?limit=100'),
 productionRun:(id:string)=>get<ProductionRunDetail>('/production-runs/'+encodeURIComponent(id)),
 productionStoryboard:(id:string)=>get<ProductionStoryboard>('/production-runs/'+encodeURIComponent(id)+'/storyboard'),
 productionRunAssets:(id:string)=>get<ProductionRunAssets>('/production-runs/'+encodeURIComponent(id)+'/assets'),
 pendingReview:()=>request<PendingReview|null>('/review/pending',{},true),
 deadLetters:()=>get<{dead_letters:Task[]}>('/autonomy/dead-letters?limit=100'),
 eventFeed:(afterEventId=0,limit=100)=>get<EventFeed>('/autonomy/events?after_event_id='+Math.max(0,Math.trunc(afterEventId))+'&limit='+Math.max(1,Math.min(500,Math.trunc(limit)))),
 stuckTasks:(staleAfterSeconds=120,limit=100)=>get<{stuck_tasks:StuckTask[];stale_after_seconds:number}>('/autonomy/stuck-tasks?stale_after_seconds='+Math.max(1,Math.min(3600,Math.trunc(staleAfterSeconds)))+'&limit='+Math.max(1,Math.min(500,Math.trunc(limit)))),
 plan:(id:string)=>get<any>('/plans/'+encodeURIComponent(id)),
 task:(id:string)=>get<{task:Task;events:TaskEvent[]}>('/tasks/'+encodeURIComponent(id)),
 createTask:(task_type:string,payload:Record<string,unknown>,idempotency_key:string)=>post<{task_id:string;status:string;task_type:string}>('/tasks',{task_type,payload,idempotency_key}),
};
