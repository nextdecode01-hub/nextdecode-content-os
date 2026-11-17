export type StudioBeat = { id:number; name:string; start:number; end:number; kind:string; description:string; caption:string };
export type StudioWorkspace = { workspaceId:string; name:string; createdAt:string; updatedAt:string };
export type StudioDraft = { draftId:string; workspaceId:string; title:string; beats:StudioBeat[]; currentVersionId:string|null; updatedAt:string };
export type StudioVersion = { versionId:string; draftId:string; title:string; beats:StudioBeat[]; contentDigest:string; createdAt:string; parentVersionId:string|null; restoreOfVersionId:string|null };
export type StudioTaskLink = { linkId:string; draftId:string; versionId:string; taskId:string; linkedAt:string };

export const STUDIO_DRAFT_ID = 'nextdecode-shorts-studio-main';
export const LEGACY_WORKSPACE_ID = 'nextdecode-studio-workspace-main';
export const LEGACY_SHORT_TITLE = 'AI Accelerates Research?';
const DB_NAME = 'nextdecode-studio-workbench', DB_VERSION = 2;
const WORKSPACES = 'workspaces', DRAFTS = 'drafts', VERSIONS = 'versions', TASK_LINKS = 'taskLinks';

function openDb(): Promise<IDBDatabase> {
  if (typeof indexedDB === 'undefined') return Promise.reject(new Error('Persistent Studio storage is unavailable in this browser'));
  return new Promise((resolve,reject)=>{ const request=indexedDB.open(DB_NAME,DB_VERSION);
    request.onupgradeneeded=()=>{const db=request.result;const upgrade=request.transaction;
      if(!db.objectStoreNames.contains(WORKSPACES)) db.createObjectStore(WORKSPACES,{keyPath:'workspaceId'});
      if(!db.objectStoreNames.contains(DRAFTS)){const store=db.createObjectStore(DRAFTS,{keyPath:'draftId'});store.createIndex('byWorkspace','workspaceId',{unique:false});}
      else if(upgrade&&!upgrade.objectStore(DRAFTS).indexNames.contains('byWorkspace')) upgrade.objectStore(DRAFTS).createIndex('byWorkspace','workspaceId',{unique:false});
      if(!db.objectStoreNames.contains(VERSIONS)){const store=db.createObjectStore(VERSIONS,{keyPath:'versionId'});store.createIndex('byDraft','draftId',{unique:false});}
      if(!db.objectStoreNames.contains(TASK_LINKS)){const store=db.createObjectStore(TASK_LINKS,{keyPath:'linkId'});store.createIndex('byVersion','versionId',{unique:false});store.createIndex('byTask','taskId',{unique:true});}
    };
    request.onsuccess=async()=>{try{await migrateLegacyStudioData(request.result);resolve(request.result);}catch(error){request.result.close();reject(error);}};
    request.onerror=()=>reject(request.error??new Error('Could not open Studio storage')); request.onblocked=()=>reject(new Error('Studio storage upgrade is blocked by another open tab'));
  });
}
function requestResult<T>(request:IDBRequest<T>):Promise<T>{return new Promise((resolve,reject)=>{request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error??new Error('Studio storage request failed'));});}
function transactionDone(tx:IDBTransaction):Promise<void>{return new Promise((resolve,reject)=>{tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error??new Error('Studio storage transaction failed'));tx.onabort=()=>reject(tx.error??new Error('Studio storage transaction aborted'));});}
const cloneBeats=(beats:StudioBeat[])=>beats.map(beat=>({...beat}));
const now=()=>new Date().toISOString();
const newId=()=>crypto.randomUUID();

async function migrateLegacyStudioData(db:IDBDatabase):Promise<void>{
  const tx=db.transaction([WORKSPACES,DRAFTS],'readwrite');const workspaceStore=tx.objectStore(WORKSPACES);const draftStore=tx.objectStore(DRAFTS);
  const workspace=await requestResult(workspaceStore.get(LEGACY_WORKSPACE_ID)) as StudioWorkspace|undefined;
  if(!workspace) workspaceStore.put({workspaceId:LEGACY_WORKSPACE_ID,name:'NEXTDECODE Shorts',createdAt:now(),updatedAt:now()} satisfies StudioWorkspace);
  const legacy=await requestResult(draftStore.get(STUDIO_DRAFT_ID)) as (Partial<StudioDraft>&{title:string;beats:StudioBeat[];currentVersionId:string|null;updatedAt:string})|undefined;
  if(legacy && !legacy.workspaceId) draftStore.put({...legacy,draftId:STUDIO_DRAFT_ID,workspaceId:LEGACY_WORKSPACE_ID});
  await transactionDone(tx);
}
async function digestBeats(title:string,beats:StudioBeat[]):Promise<string>{
  if(!globalThis.crypto?.subtle) throw new Error('Web Crypto is required to create a verified storyboard version');
  const canonical=JSON.stringify({schema:'nextdecode.studio.storyboard.v1',title,beats:cloneBeats(beats)});
  const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical));
  return Array.from(new Uint8Array(digest),byte=>byte.toString(16).padStart(2,'0')).join('');
}

export async function listStudioWorkspaces():Promise<StudioWorkspace[]>{const db=await openDb();try{const tx=db.transaction(WORKSPACES,'readonly');const rows=await requestResult(tx.objectStore(WORKSPACES).getAll()) as StudioWorkspace[];await transactionDone(tx);return rows.sort((a,b)=>a.createdAt.localeCompare(b.createdAt));}finally{db.close();}}
export async function createStudioWorkspace(name:string):Promise<StudioWorkspace>{const clean=name.trim();if(!clean)throw new Error('A workspace name is required');const db=await openDb();try{const workspace:StudioWorkspace={workspaceId:newId(),name:clean,createdAt:now(),updatedAt:now()};const tx=db.transaction(WORKSPACES,'readwrite');tx.objectStore(WORKSPACES).add(workspace);await transactionDone(tx);return workspace;}finally{db.close();}}
export async function listStudioDrafts(workspaceId:string):Promise<StudioDraft[]>{const db=await openDb();try{const tx=db.transaction(DRAFTS,'readonly');const rows=await requestResult(tx.objectStore(DRAFTS).index('byWorkspace').getAll(workspaceId)) as StudioDraft[];await transactionDone(tx);return rows.sort((a,b)=>b.updatedAt.localeCompare(a.updatedAt));}finally{db.close();}}
export async function createStudioDraft(workspaceId:string,title:string,beats:StudioBeat[]=[]):Promise<StudioDraft>{const clean=title.trim();if(!workspaceId||!clean)throw new Error('A workspace and Short title are required');const db=await openDb();try{const tx=db.transaction([WORKSPACES,DRAFTS],'readwrite');const workspace=await requestResult(tx.objectStore(WORKSPACES).get(workspaceId));if(!workspace){tx.abort();throw new Error('The selected workspace could not be found');}const draft:StudioDraft={draftId:newId(),workspaceId,title:clean,beats:cloneBeats(beats),currentVersionId:null,updatedAt:now()};tx.objectStore(DRAFTS).add(draft);await transactionDone(tx);return draft;}finally{db.close();}}
export async function loadStudioDraft(draftId=STUDIO_DRAFT_ID):Promise<StudioDraft|null>{const db=await openDb();try{const tx=db.transaction(DRAFTS,'readonly');const row=await requestResult(tx.objectStore(DRAFTS).get(draftId)) as StudioDraft|undefined;await transactionDone(tx);return row?{...row,workspaceId:row.workspaceId??LEGACY_WORKSPACE_ID}:null;}finally{db.close();}}
export async function saveStudioDraft(title:string,beats:StudioBeat[],draftId=STUDIO_DRAFT_ID,workspaceId=LEGACY_WORKSPACE_ID):Promise<StudioDraft>{const db=await openDb();try{const tx=db.transaction(DRAFTS,'readwrite');const store=tx.objectStore(DRAFTS);const existing=await requestResult(store.get(draftId)) as StudioDraft|undefined;const draft:StudioDraft={draftId,workspaceId:existing?.workspaceId??workspaceId,title,beats:cloneBeats(beats),currentVersionId:existing?.currentVersionId??null,updatedAt:now()};store.put(draft);await transactionDone(tx);return draft;}finally{db.close();}}
export async function createStudioVersion(title:string,beats:StudioBeat[],options:{draftId?:string;workspaceId?:string;restoreOfVersionId?:string|null}={}):Promise<StudioVersion>{const draftId=options.draftId??STUDIO_DRAFT_ID;const contentDigest=await digestBeats(title,beats);const db=await openDb();try{const tx=db.transaction([DRAFTS,VERSIONS],'readwrite');const done=transactionDone(tx);const prior=await requestResult(tx.objectStore(DRAFTS).get(draftId)) as StudioDraft|undefined;const version:StudioVersion={versionId:newId(),draftId,title,beats:cloneBeats(beats),contentDigest,createdAt:now(),parentVersionId:prior?.currentVersionId??null,restoreOfVersionId:options.restoreOfVersionId??null};tx.objectStore(DRAFTS).put({draftId,workspaceId:prior?.workspaceId??options.workspaceId??LEGACY_WORKSPACE_ID,title,beats:cloneBeats(beats),currentVersionId:version.versionId,updatedAt:version.createdAt} satisfies StudioDraft);tx.objectStore(VERSIONS).add(version);await done;return version;}finally{db.close();}}
export async function verifyStudioVersion(version:StudioVersion):Promise<boolean>{return (await digestBeats(version.title,version.beats))===version.contentDigest;}
export async function listStudioVersions(draftId=STUDIO_DRAFT_ID):Promise<StudioVersion[]>{const db=await openDb();try{const tx=db.transaction(VERSIONS,'readonly');const rows=await requestResult(tx.objectStore(VERSIONS).index('byDraft').getAll(draftId)) as StudioVersion[];await transactionDone(tx);return rows.sort((a,b)=>b.createdAt.localeCompare(a.createdAt));}finally{db.close();}}
export async function linkStudioValidationTask(versionId:string,taskId:string,draftId=STUDIO_DRAFT_ID):Promise<StudioTaskLink>{if(!versionId||!taskId)throw new Error('A saved version and validation task ID are required');const db=await openDb();try{const tx=db.transaction([VERSIONS,TASK_LINKS],'readwrite');const version=await requestResult(tx.objectStore(VERSIONS).get(versionId)) as StudioVersion|undefined;if(!version||version.draftId!==draftId){tx.abort();throw new Error('The storyboard version could not be verified for this draft');}const link:StudioTaskLink={linkId:newId(),draftId,versionId,taskId,linkedAt:now()};tx.objectStore(TASK_LINKS).add(link);await transactionDone(tx);return link;}finally{db.close();}}
export async function listStudioTaskLinks(versionId:string):Promise<StudioTaskLink[]>{const db=await openDb();try{const tx=db.transaction(TASK_LINKS,'readonly');const rows=await requestResult(tx.objectStore(TASK_LINKS).index('byVersion').getAll(versionId)) as StudioTaskLink[];await transactionDone(tx);return rows.sort((a,b)=>a.linkedAt.localeCompare(b.linkedAt));}finally{db.close();}}
