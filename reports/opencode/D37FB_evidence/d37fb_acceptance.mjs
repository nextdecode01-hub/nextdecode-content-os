// D37-FB — Studio Workspace Runtime Acceptance driver.
// Real headless-Chromium (Edge) execution over raw Chrome DevTools Protocol.
// Zero external dependencies (Node >= 22 global WebSocket + fetch).
// Drives the real UI (clicks, native dialogs, React controlled inputs) and
// inspects the real IndexedDB the app owns. Nothing is simulated.
import fs from 'node:fs';
import path from 'node:path';

const CDP_HTTP = 'http://127.0.0.1:9223';
const APP_ROOT = 'http://127.0.0.1:5174';
const STUDIO_URL = APP_ROOT + '/studio';
const SHOTS = 'C:/Users/yadav/AppData/Local/Temp/opencode/d37fb_shots';
const RESULTS = 'C:/Users/yadav/AppData/Local/Temp/opencode/d37fb/d37fb_results.json';
fs.mkdirSync(SHOTS, { recursive: true });

const LEGACY_WS = 'nextdecode-studio-workspace-main';
const MAIN_DRAFT = 'nextdecode-shorts-studio-main';

// ---------- CDP plumbing ----------
const version = await (await fetch(CDP_HTTP + '/json/version')).json();
const ws = new WebSocket(version.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

let msgId = 0;
const pending = new Map();
const eventHandlers = new Map();
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) {
    const { res, rej } = pending.get(m.id);
    pending.delete(m.id);
    if (m.error) rej(new Error(m.error.message + ' (' + methodOf(m.id) + ')'));
    else res(m.result);
  } else if (m.method) {
    const h = eventHandlers.get(m.method);
    if (h) h(m.params, m.sessionId);
  }
};
const methodById = new Map();
function send(method, params = {}, sessionId) {
  const id = ++msgId;
  methodById.set(id, method);
  const payload = { id, method, params };
  if (sessionId) payload.sessionId = sessionId;
  return new Promise((res, rej) => {
    pending.set(id, { res, rej });
    ws.send(JSON.stringify(payload));
  });
}
function methodOf(id) { return methodById.get(id) || '?'; }
function on(method, fn) { eventHandlers.set(method, fn); }

const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
const { sessionId: sid } = await send('Target.attachToTarget', { targetId, flatten: true });

await send('Page.enable', {}, sid);
await send('Runtime.enable', {}, sid);
await send('Log.enable', {}, sid);
await send('Network.enable', {}, sid);

// ---------- evidence collectors ----------
const consoleIssues = [];
const idbIssues = [];
const networkFails = []; // {url, errorText, type}
const requestUrls = new Map();
on('Network.requestWillBeSent', (p) => { requestUrls.set(p.requestId, p.request.url); });
on('Network.responseReceived', (p) => {
  const status = p.response?.status || 0;
  if (status >= 400) networkFails.push({ url: requestUrls.get(p.requestId) || p.response?.url || '(unknown)', errorText: 'HTTP ' + status, type: p.type, at: new Date().toISOString() });
});
on('Network.loadingFailed', (p) => {
  networkFails.push({ url: requestUrls.get(p.requestId) || '(unknown)', errorText: p.errorText, type: p.type, at: new Date().toISOString() });
});
on('Runtime.consoleAPICalled', (p) => {
  if (p.type === 'error' || p.type === 'warning' || p.type === 'assert') {
    consoleIssues.push({ level: p.type, text: p.args.map(a => a.value ?? a.description ?? '').join(' ').slice(0, 500), at: new Date().toISOString() });
  }
});
on('Runtime.exceptionThrown', (p) => {
  const d = p.exceptionDetails;
  consoleIssues.push({ level: 'exception', text: (d.exception?.description || d.text || '').slice(0, 500), at: new Date().toISOString() });
});
on('Log.entryAdded', (p) => {
  const e = p.entry;
  if (e.level === 'error') consoleIssues.push({ level: 'log.' + e.source, text: e.text.slice(0, 500), at: new Date().toISOString() });
  if (e.source === 'storage' && (e.level === 'error' || e.level === 'warning')) idbIssues.push({ level: e.level, text: e.text.slice(0, 300), at: new Date().toISOString() });
});

// Real JS dialogs (window.prompt for New workspace / New Short)
let pendingPrompt = null;
let lastDialog = null;
on('Page.javascriptDialogOpening', (p) => {
  lastDialog = { type: p.type, message: p.message, responded: new Date().toISOString() };
  send('Page.handleJavaScriptDialog', { accept: pendingPrompt !== null, promptText: pendingPrompt ?? '' }, sid);
  pendingPrompt = null;
});

// ---------- helpers ----------
async function evalJs(expression) {
  const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true, userGesture: true }, sid);
  if (r.exceptionDetails) throw new Error('page eval failed: ' + (r.exceptionDetails.exception?.description || r.exceptionDetails.text).slice(0, 400));
  return r.result.value;
}
async function shot(name) {
  const { data } = await send('Page.captureScreenshot', { format: 'png' }, sid);
  fs.writeFileSync(path.join(SHOTS, name + '.png'), Buffer.from(data, 'base64'));
}
async function navigate(url) {
  await send('Page.navigate', { url }, sid);
  await waitDomReady();
  await evalJs(setNative);
}
function waitDomReady() {
  return new Promise((res) => {
    const h = (p, s) => { if (s === sid) { eventHandlers.delete('Page.loadEventFired'); res(); } };
    eventHandlers.set('Page.loadEventFired', h);
  });
}
async function reload() {
  await send('Page.reload', { ignoreCache: true }, sid);
  await waitDomReady();
  await evalJs(setNative);
}
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
async function waitForJs(expression, timeout = 8000, interval = 250) {
  const t0 = Date.now();
  for (;;) {
    let v = null;
    try { v = await evalJs(expression); } catch { /* page busy */ }
    if (v) return v;
    if (Date.now() - t0 > timeout) throw new Error('waitForJs timeout: ' + expression.slice(0, 120));
    await sleep(interval);
  }
}
const dumpIdb = () => evalJs(`(async()=>{
  const db=await new Promise((res,rej)=>{const r=indexedDB.open('nextdecode-studio-workbench');r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)});
  const out={version:db.version,stores:[...db.objectStoreNames]};
  for(const s of ['workspaces','drafts','versions','taskLinks']){
    if(!db.objectStoreNames.contains(s)){out[s]=null;continue}
    out[s]=await new Promise((res,rej)=>{const tx=db.transaction(s,'readonly');const rq=tx.objectStore(s).getAll();rq.onsuccess=()=>res(rq.result);rq.onerror=()=>rej(rq.error)});
  }
  db.close();return out;
})()`);

const setNative = `(()=>{window.__setVal=(el,value)=>{if(!el)return'missing';const proto=el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:el.tagName==='SELECT'?HTMLSelectElement.prototype:HTMLInputElement.prototype;Object.getOwnPropertyDescriptor(proto,'value').set.call(el,value);el.dispatchEvent(new Event(el.tagName==='SELECT'?'change':'input',{bubbles:true}));return 'ok'};return 'installed'})()`;
await evalJs(setNative);

async function clickByText(text, scope = 'button') {
  const r = await evalJs(`(()=>{const el=[...document.querySelectorAll(${JSON.stringify(scope)})].find(e=>e.textContent.trim()===${JSON.stringify(text)});if(!el)return 'missing';if(el.disabled)return 'disabled';el.click();return 'clicked'})()`);
  if (r === 'missing') throw new Error('button not found: ' + text);
  if (r === 'disabled') throw new Error('button is disabled: ' + text);
}
async function clickEnabledByText(text, scope = 'button', timeout = 8000) {
  await waitForJs(`(()=>{const el=[...document.querySelectorAll(${JSON.stringify(scope)})].find(e=>e.textContent.trim()===${JSON.stringify(text)});return el&&!el.disabled})()`, timeout);
  await clickByText(text, scope);
}
async function clickRestoreFor(versionIdPrefix) {
  const r = await evalJs(`(()=>{const btns=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Restore as new version'&&!b.disabled);for(const b of btns){const row=b.closest('div');const label=row?row.querySelector('b'):null;if(label&&label.textContent.startsWith(${JSON.stringify(versionIdPrefix)})){b.click();return 'clicked'}}return 'missing'})()`);
  if (r === 'missing') throw new Error('restore button not found for ' + versionIdPrefix);
}
async function sceneTitleInput() {
  return evalJs(`(()=>{const label=[...document.querySelectorAll('label')].find(l=>(l.childNodes[0]?.textContent||'').trim().startsWith('Scene title'));const el=label?.querySelector('input');if(!el)return null;el.focus();return 'ok'})()`);
}
async function setSceneTitle(value) {
  const r = await evalJs(`(()=>{const label=[...document.querySelectorAll('label')].find(l=>(l.childNodes[0]?.textContent||'').trim().startsWith('Scene title'));const el=label?.querySelector('input');if(!el)return 'missing';return window.__setVal(el,${JSON.stringify(value)})})()`);
  if (r !== 'ok') throw new Error('scene title input not set: ' + r);
}
async function selectByAriaLabel(aria, optionText) {
  const r = await evalJs(`(()=>{const sel=document.querySelector('select[aria-label=${JSON.stringify(aria)}]');if(!sel)return 'missing';const opt=[...sel.options].find(o=>o.text===${JSON.stringify(optionText)});if(!opt)return 'no-option:'+${JSON.stringify(optionText)};return window.__setVal(sel,opt.value)})()`);
  if (r !== 'ok') throw new Error('select failed: ' + r);
  await sleep(350); // let React flush the controlled re-render so later handlers see fresh state
}
async function selectOptions(aria) {
  return evalJs(`(()=>{const sel=document.querySelector('select[aria-label=${JSON.stringify(aria)}]');return sel?[...sel.options].map(o=>({value:o.value,text:o.text})):null})()`);
}
const storageErrorText = () => evalJs(`(()=>{const el=document.querySelector('.studio-handoff-error[role=alert]');return el?el.textContent:null})()`);
const versionNoticeText = () => evalJs(`(()=>{const els=[...document.querySelectorAll('.studio-note[role=status]')];return els.length?els[els.length-1].textContent:null})()`);
const inspectorTitle = () => evalJs(`(()=>{const label=[...document.querySelectorAll('label')].find(l=>(l.childNodes[0]?.textContent||'').trim().startsWith('Scene title'));const el=label?.querySelector('input');return el?el.value:null})()`);
const beatCount = () => evalJs(`document.querySelectorAll('.studio-beats .studio-beat').length`);
const activeVersionBadge = () => evalJs(`(()=>{const b=[...document.querySelectorAll('.studio-flow, .panel, div')].length;const el=[...document.querySelectorAll('small')].find(s=>s.textContent.includes('Versioned draft')||s.textContent.includes('Draft storyboard'));return el?el.textContent:null})()`);
async function addSceneIfEmpty() {
  const n = await beatCount();
  if (n === 0) { await clickByText('Add scene'); await sleep(300); }
}
function withPrompt(text, action) { pendingPrompt = text; return action(); }

// ---------- scenario ledger ----------
const ledger = [];
let shotIdx = 0;
async function record(id, title, fn) {
  const entry = { id, title, status: 'PASS', detail: '', evidence: [] };
  const t0 = Date.now();
  try { await fn(entry); }
  catch (e) {
    entry.status = 'FAIL';
    entry.detail = String(e.message || e).slice(0, 600);
  }
  entry.ms = Date.now() - t0;
  ledger.push(entry);
  console.log(`[${entry.status}] ${id} ${title} ${entry.detail ? '— ' + entry.detail : ''}`);
  return entry;
}
function ok(entry, cond, message) { if (!cond) throw new Error(message); entry.evidence.push(message); }

// ================= RUN =================
const dbMeta = [];
let entryFinding = null;

// ---------- S10 FIRST: seed authentic D37-E legacy data in a virgin profile, then load Studio ----------
await navigate(APP_ROOT + '/'); // page origin for IndexedDB; /studio not yet visited
const seeded = await evalJs(`(async()=>{
  const beats=[
    {id:1,name:'Legacy hook',start:0,end:6,kind:'Kinetic typography',description:'Legacy D37-E scene one',caption:'Legacy caption one'},
    {id:2,name:'Legacy evidence',start:6,end:14,kind:'B-roll',description:'Legacy D37-E scene two',caption:'Legacy caption two'}];
  const canonical=JSON.stringify({schema:'nextdecode.studio.storyboard.v1',title:'AI Accelerates Research?',beats});
  const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical)))].map(b=>b.toString(16).padStart(2,'0')).join('');
  const V='legacy-version-'+'a'.repeat(17), T='legacy-task-'+'a'.repeat(20), L='legacy-link-'+'a'.repeat(20);
  const db=await new Promise((res,rej)=>{const r=indexedDB.open('nextdecode-studio-workbench',1);
    r.onupgradeneeded=()=>{const d=r.result;const ds=d.createObjectStore('drafts',{keyPath:'draftId'});
      const vs=d.createObjectStore('versions',{keyPath:'versionId'});vs.createIndex('byDraft','draftId',{unique:false});
      const tl=d.createObjectStore('taskLinks',{keyPath:'linkId'});tl.createIndex('byVersion','versionId',{unique:false});tl.createIndex('byTask','taskId',{unique:true});};
    r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)});
  const put=(store,val)=>new Promise((res,rej)=>{const tx=db.transaction(store,'readwrite');tx.objectStore(store).put(val);tx.oncomplete=()=>res();tx.onerror=()=>rej(tx.error)});
  // D37-E legacy draft shape: no workspaces store, no byWorkspace index, no workspaceId field.
  await put('drafts',{draftId:'nextdecode-shorts-studio-main',title:'AI Accelerates Research?',beats,currentVersionId:V,updatedAt:'2026-11-01T00:00:00.000Z'});
  await put('versions',{versionId:V,draftId:'nextdecode-shorts-studio-main',title:'AI Accelerates Research?',beats,contentDigest:digest,createdAt:'2026-11-01T00:00:00.000Z',parentVersionId:null,restoreOfVersionId:null});
  await put('taskLinks',{linkId:L,draftId:'nextdecode-shorts-studio-main',versionId:V,taskId:T,linkedAt:'2026-11-01T00:00:00.000Z'});
  db.close();return 'seeded:v1 legacy 1 draft / 1 version / 1 task link';
})()`);
dbMeta.push({ step: 'legacy-seed', seeded, legacyDigestKnown: true });

await navigate(STUDIO_URL);
await waitForJs(`/local storage ready|storage issue/i.test(document.body.innerText)`, 15000);
const migrated = await dumpIdb();
dbMeta.push({ step: 'after-first-studio-load', dbVersion: migrated.version, stores: migrated.stores });
await shot('10_legacy_migration');

await record('S10', 'D37-E legacy data migrates without loss or duplication', (e) => {
  ok(e, migrated.version === 2, 'IndexedDB upgraded to schema version 2 (saw ' + migrated.version + ')');
  ok(e, Array.isArray(migrated.workspaces) && migrated.workspaces.length === 1, 'exactly 1 workspace after migration: ' + JSON.stringify(migrated.workspaces?.map(w => w.workspaceId)));
  const ws0 = migrated.workspaces?.[0] || {};
  ok(e, ws0.workspaceId === LEGACY_WS && ws0.name === 'NEXTDECODE Shorts', 'legacy workspace record present: ' + ws0.workspaceId);
  const d0 = (migrated.drafts || []).find(d => d.draftId === MAIN_DRAFT);
  ok(e, !!d0, 'legacy draft still present after migration');
  ok(e, d0.workspaceId === LEGACY_WS, 'legacy draft tagged to legacy workspace (no orphan)');
  ok(e, d0.title === 'AI Accelerates Research?' && d0.beats.length === 2, 'legacy draft title + 2 beats preserved');
  ok(e, (migrated.versions || []).length === 1, 'exactly 1 version (no duplication): ' + (migrated.versions || []).length);
  ok(e, (migrated.taskLinks || []).length === 1, 'exactly 1 validation-task link (no duplication): ' + (migrated.taskLinks || []).length);
  ok(e, consoleIssues.filter(i => i.level !== 'warning' && i.level !== 'log.network').length === 0, 'no console errors during migration');
});

// ---------- S1: two workspaces, separation after reload ----------
await record('S1', 'Create two workspaces; both remain separate after reload', async (e) => {
  withPrompt('Alpha Workspace', () => clickByText('New workspace'));
  await waitForJs(`[...document.querySelectorAll('select[aria-label="Selected workspace"] option')].some(o=>o.text==='Alpha Workspace')`, 5000);
  await sleep(250);
  withPrompt('Beta Workspace', () => clickByText('New workspace'));
  await waitForJs(`[...document.querySelectorAll('select[aria-label="Selected workspace"] option')].some(o=>o.text==='Beta Workspace')`, 5000);
  await sleep(250);
  await reload();
  await waitForJs(`/local storage ready|storage issue/i.test(document.body.innerText)`, 15000);
  const opts = await selectOptions('Selected workspace');
  const names = opts.map(o => o.text);
  ok(e, names.includes('NEXTDECODE Shorts') && names.includes('Alpha Workspace') && names.includes('Beta Workspace'), 'after reload workspace selector lists: ' + names.join(' | '));
  const after = await dumpIdb();
  ok(e, after.workspaces.length === 3, 'IndexedDB holds exactly 3 workspaces: ' + after.workspaces.map(w => w.name).join(', '));
  dbMeta.push({ step: 'S1-workspaces', count: after.workspaces.length });
  await shot('01_two_workspaces_after_reload');
});

// ---------- S2: multiple Shorts per workspace, workspace-scoped ----------
await record('S2', 'Create multiple Shorts per workspace; lists stay workspace-scoped', async (e) => {
  await selectByAriaLabel('Selected workspace', 'Alpha Workspace');
  withPrompt('Alpha Short One', () => clickByText('New Short'));
  await waitForJs(`[...document.querySelectorAll('select[aria-label="Selected Short"] option')].some(o=>o.text==='Alpha Short One')`, 5000);
  await sleep(300);
  await selectByAriaLabel('Selected workspace', 'Alpha Workspace');
  withPrompt('Alpha Short Two', () => clickByText('New Short'));
  await waitForJs(`[...document.querySelectorAll('select[aria-label="Selected Short"] option')].some(o=>o.text==='Alpha Short Two')`, 5000);
  await sleep(300);
  await selectByAriaLabel('Selected workspace', 'Beta Workspace');
  withPrompt('Beta Short One', () => clickByText('New Short'));
  await waitForJs(`[...document.querySelectorAll('select[aria-label="Selected Short"] option')].some(o=>o.text==='Beta Short One')`, 5000);
  await sleep(300);
  // scope checks
  await selectByAriaLabel('Selected workspace', 'Alpha Workspace');
  await sleep(250);
  let opts = (await selectOptions('Selected Short')).map(o => o.text);
  ok(e, opts.includes('Alpha Short One') && opts.includes('Alpha Short Two') && !opts.includes('Beta Short One'), 'Alpha workspace lists its 2 Shorts only: ' + opts.join(' | '));
  await selectByAriaLabel('Selected workspace', 'Beta Workspace');
  await sleep(250);
  opts = (await selectOptions('Selected Short')).map(o => o.text);
  ok(e, opts.includes('Beta Short One') && !opts.some(t => t.startsWith('Alpha Short')), 'Beta workspace lists only its own Short: ' + opts.join(' | '));
  const after = await dumpIdb();
  const alpha = after.drafts.filter(d => after.workspaces.find(w => w.name === 'Alpha Workspace')?.workspaceId === d.workspaceId);
  const beta = after.drafts.filter(d => after.workspaces.find(w => w.name === 'Beta Workspace')?.workspaceId === d.workspaceId);
  ok(e, alpha.length === 2 && beta.length === 1, 'IndexedDB drafts scoped by workspaceId: Alpha=' + alpha.length + ' Beta=' + beta.length + ' legacy=' + (after.drafts.length - 3));
  await shot('02_shorts_scoped_per_workspace');
});

// ---------- S3: autosave survives reload ----------
const AUTOSAVE_MARKER = 'AUTOSAVE-MARKER-ALPHA-1';
await record('S3', 'Edit one Short; autosave persists after reload', async (e) => {
  await selectByAriaLabel('Selected workspace', 'Alpha Workspace');
  await sleep(250);
  await selectByAriaLabel('Selected Short', 'Alpha Short One');
  await sleep(400);
  await addSceneIfEmpty();
  await setSceneTitle(AUTOSAVE_MARKER);
  await waitForJs(`(async()=>{const db=await new Promise((res,rej)=>{const r=indexedDB.open('nextdecode-studio-workbench');r.onsuccess=()=>res(r.result)});const tx=db.transaction('drafts','readonly');const rq=tx.objectStore('drafts').getAll();const rows=await new Promise(res=>{rq.onsuccess=()=>res(rq.result)});db.close();return rows.some(d=>d.title==='Alpha Short One'&&(d.beats[0]?.name)===${JSON.stringify(AUTOSAVE_MARKER)})})()`, 6000);
  await shot('03_autosave_edited');
  await reload();
  await waitForJs(`/local storage ready|storage issue/i.test(document.body.innerText)`, 15000);
  const after = await dumpIdb();
  const row = after.drafts.find(d => d.title === 'Alpha Short One');
  ok(e, row && row.beats[0]?.name === AUTOSAVE_MARKER, 'after reload the persisted draft still holds the edit: ' + (row?.beats[0]?.name ?? 'MISSING'));
  // and the UI shows it after re-selecting
  await selectByAriaLabel('Selected workspace', 'Alpha Workspace');
  await sleep(250);
  await selectByAriaLabel('Selected Short', 'Alpha Short One');
  await sleep(500);
  const shown = await inspectorTitle();
  ok(e, shown === AUTOSAVE_MARKER, 'scene inspector renders the persisted edit after reload: ' + shown);
});

// ---------- S4: edits never cross Shorts ----------
await record('S4', 'Editing one Short never modifies another Short', async (e) => {
  await selectByAriaLabel('Selected workspace', 'Alpha Workspace');
  await sleep(250);
  await selectByAriaLabel('Selected Short', 'Alpha Short Two');
  await sleep(400);
  await addSceneIfEmpty();
  await setSceneTitle('ISOLATION-MARKER-B');
  await sleep(800); // autosave debounce + margin
  await selectByAriaLabel('Selected workspace', 'Beta Workspace');
  await sleep(250);
  await selectByAriaLabel('Selected Short', 'Beta Short One');
  await sleep(400);
  await addSceneIfEmpty();
  await setSceneTitle('ISOLATION-MARKER-C');
  await sleep(800);
  const after = await dumpIdb();
  const one = after.drafts.find(d => d.title === 'Alpha Short One');
  const two = after.drafts.find(d => d.title === 'Alpha Short Two');
  const beta = after.drafts.find(d => d.title === 'Beta Short One');
  const legacy = after.drafts.find(d => d.draftId === MAIN_DRAFT);
  ok(e, one?.beats[0]?.name === AUTOSAVE_MARKER, 'Alpha Short One untouched: ' + (one?.beats[0]?.name ?? 'MISSING'));
  ok(e, two?.beats[0]?.name === 'ISOLATION-MARKER-B', 'Alpha Short Two has its own edit: ' + (two?.beats[0]?.name ?? 'MISSING'));
  ok(e, beta?.beats[0]?.name === 'ISOLATION-MARKER-C', 'Beta Short One has its own edit: ' + (beta?.beats[0]?.name ?? 'MISSING'));
  ok(e, legacy?.beats[0]?.name === 'Legacy hook', 'legacy migrated Short untouched: ' + (legacy?.beats[0]?.name ?? 'MISSING'));
  await reload();
  await waitForJs(`/local storage ready|storage issue/i.test(document.body.innerText)`, 15000);
  const post = await dumpIdb();
  ok(e, post.drafts.find(d => d.title === 'Alpha Short One')?.beats[0]?.name === AUTOSAVE_MARKER
     && post.drafts.find(d => d.title === 'Alpha Short Two')?.beats[0]?.name === 'ISOLATION-MARKER-B'
     && post.drafts.find(d => d.title === 'Beta Short One')?.beats[0]?.name === 'ISOLATION-MARKER-C',
     'after reload each Short still holds exactly its own edit');
  await shot('04_isolation_after_reload');
});

// ---------- S5: multiple immutable versions; history unchanged ----------
let v1 = null, v2 = null;
await record('S5', 'Save multiple immutable versions; earlier versions remain unchanged', async (e) => {
  await selectByAriaLabel('Selected workspace', 'Alpha Workspace');
  await sleep(250);
  await selectByAriaLabel('Selected Short', 'Alpha Short One');
  await sleep(500);
  await clickEnabledByText('Save version');
  await waitForJs(`/version saved · sha-256/i.test(document.body.innerText)`, 8000);
  const before = await dumpIdb();
  v1 = before.versions.filter(v => v.draftId === before.drafts.find(d => d.title === 'Alpha Short One').draftId).sort((a, b) => a.createdAt.localeCompare(b.createdAt))[0];
  await setSceneTitle(AUTOSAVE_MARKER + ' / edited-for-v2');
  await sleep(800);
  await clickEnabledByText('Save version');
  await waitForJs(`/version saved · sha-256/i.test(document.body.innerText)`, 8000);
  const after = await dumpIdb();
  const alphaDraftId = after.drafts.find(d => d.title === 'Alpha Short One').draftId;
  const history = after.versions.filter(v => v.draftId === alphaDraftId).sort((a, b) => a.createdAt.localeCompare(b.createdAt));
  v1 = history[0]; v2 = history[1];
  ok(e, history.length === 2, 'two immutable versions recorded: ' + history.map(v => v.versionId.slice(0, 8)).join(', '));
  ok(e, v1.contentDigest !== v2.contentDigest, 'versions have distinct SHA-256 digests');
  ok(e, v1.beats[0].name === AUTOSAVE_MARKER, 'version 1 snapshot preserved the pre-edit title: ' + v1.beats[0].name);
  ok(e, v2.beats[0].name === AUTOSAVE_MARKER + ' / edited-for-v2', 'version 2 snapshot holds the new title: ' + v2.beats[0].name);
  ok(e, v2.parentVersionId === v1.versionId, 'version 2 parent link: ' + v2.parentVersionId?.slice(0, 8));
  await reload();
  await waitForJs(`/local storage ready|storage issue/i.test(document.body.innerText)`, 15000);
  const post = await dumpIdb();
  const hist2 = post.versions.filter(v => v.draftId === alphaDraftId);
  ok(e, hist2.length === 2 && hist2.some(v => v.contentDigest === v1.contentDigest) && hist2.some(v => v.contentDigest === v2.contentDigest), 'both versions intact after reload');
  await shot('05_two_versions');
});

// ---------- S6: SHA-256 digest consistency ----------
await record('S6', 'SHA-256 digest consistency for every stored version', async (e) => {
  const data = await dumpIdb();
  const recomputed = await evalJs(`(async()=>{const rows=${JSON.stringify((data.versions || []))};const out=[];for(const v of rows){const canonical=JSON.stringify({schema:'nextdecode.studio.storyboard.v1',title:v.title,beats:v.beats});const d=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical));out.push({versionId:v.versionId,stored:v.contentDigest,recomputed:[...new Uint8Array(d)].map(b=>b.toString(16).padStart(2,'0')).join('')})}return out})()`);
  const bad = recomputed.filter(r => r.stored !== r.recomputed);
  ok(e, recomputed.length >= 2, 'checked ' + recomputed.length + ' stored versions (incl. migrated legacy version)');
  ok(e, bad.length === 0, bad.length === 0 ? 'every stored digest matches a fresh SHA-256 of its canonical content' : 'MISMATCHES: ' + JSON.stringify(bad.slice(0, 3)));
  await shot('06_digest_check');
});

// ---------- S7: restore creates a new version ----------
await record('S7', 'Restoration creates a NEW version; source version unchanged', async (e) => {
  await selectByAriaLabel('Selected workspace', 'Alpha Workspace');
  await sleep(250);
  await selectByAriaLabel('Selected Short', 'Alpha Short One');
  await sleep(500);
  const before = await dumpIdb();
  const alphaDraftId = before.drafts.find(d => d.title === 'Alpha Short One').draftId;
  const n0 = before.versions.filter(v => v.draftId === alphaDraftId).length;
  const v1Row = before.versions.find(v => v.versionId === v1.versionId);
  await clickRestoreFor(v1.versionId.slice(0, 12));
  await waitForJs(`/restored as a new immutable version/i.test(document.body.innerText)`, 8000);
  const after = await dumpIdb();
  const history = after.versions.filter(v => v.draftId === alphaDraftId);
  const restored = history.find(v => v.restoreOfVersionId === v1.versionId);
  ok(e, history.length === n0 + 1, 'version count grew by exactly 1: ' + n0 + ' -> ' + history.length);
  ok(e, !!restored, 'new version records restoreOfVersionId=' + v1.versionId.slice(0, 8));
  ok(e, restored && restored.versionId !== v1.versionId, 'restoration is a distinct new version');
  ok(e, restored && restored.beats[0].name === v1Row.beats[0].name && restored.contentDigest === v1Row.contentDigest, 'restored content equals the source version byte-for-byte');
  const v1After = after.versions.find(v => v.versionId === v1.versionId);
  ok(e, v1After.contentDigest === v1Row.contentDigest && v1After.beats[0].name === v1Row.beats[0].name, 'source version row unchanged after restore');
  ok(e, after.drafts.find(d => d.draftId === alphaDraftId).currentVersionId === restored.versionId, 'draft now points at the restored version');
  await shot('07_restore_new_version');
});

// ---------- S8: corrupted version cannot be restored ----------
await record('S8', 'Corrupted/altered version cannot be restored (fail closed)', async (e) => {
  const before = await dumpIdb();
  const alphaDraftId = before.drafts.find(d => d.title === 'Alpha Short One').draftId;
  const n0 = before.versions.filter(v => v.draftId === alphaDraftId).length;
  // corrupt v2 in the real IndexedDB
  const corrupt = await evalJs(`(async()=>{const db=await new Promise((res,rej)=>{const r=indexedDB.open('nextdecode-studio-workbench');r.onsuccess=()=>res(r.result)});const tx=db.transaction('versions','readwrite');const st=tx.objectStore('versions');const row=await new Promise(res=>{const rq=st.get(${JSON.stringify(v2.versionId)});rq.onsuccess=()=>res(rq.result)});const original=row.contentDigest;row.contentDigest='f'.repeat(64);st.put(row);await new Promise(res=>{tx.oncomplete=res});db.close();return original})()`);
  ok(e, corrupt === v2.contentDigest, 'test corrupted version ' + v2.versionId.slice(0, 8) + ' (digest altered in IndexedDB)');
  await reload();
  await waitForJs(`/local storage ready|storage issue/i.test(document.body.innerText)`, 15000);
  await selectByAriaLabel('Selected workspace', 'Alpha Workspace');
  await sleep(250);
  await selectByAriaLabel('Selected Short', 'Alpha Short One');
  await sleep(600);
  await clickRestoreFor(v2.versionId.slice(0, 12));
  await waitForJs(`!!document.querySelector('.studio-handoff-error[role=alert]')`, 8000);
  const err = await storageErrorText();
  ok(e, /verif|SHA-256/i.test(err || ''), 'restore blocked with fail-closed error: ' + (err || '').slice(0, 120));
  const after = await dumpIdb();
  const n1 = after.versions.filter(v => v.draftId === alphaDraftId).length;
  ok(e, n1 === n0, 'no new version was created from the corrupted row: count still ' + n1);
  // repair the test corruption so later evidence stays clean
  await evalJs(`(async()=>{const db=await new Promise((res,rej)=>{const r=indexedDB.open('nextdecode-studio-workbench');r.onsuccess=()=>res(r.result)});const tx=db.transaction('versions','readwrite');const st=tx.objectStore('versions');const row=await new Promise(res=>{const rq=st.get(${JSON.stringify(v2.versionId)});rq.onsuccess=()=>res(rq.result)});row.contentDigest=${JSON.stringify(corrupt)};st.put(row);await new Promise(res=>{tx.oncomplete=res});db.close();return 'repaired'})()`);
  await reload(); // clear the fail-closed error state and re-sync the version list from repaired storage
  await waitForJs(`/local storage ready|storage issue/i.test(document.body.innerText)`, 15000);
  const repaired = await dumpIdb();
  ok(e, (repaired.versions || []).find(v => v.versionId === v2.versionId)?.contentDigest === corrupt, 'test corruption repaired; stored digest restored to the original value');
  await shot('08_corrupt_restore_blocked');
});

// ---------- S9: exact-version validation task link ----------
let linkedTaskId = null, linkedVersionId = null;
const s9 = (...a) => console.log('  [S9 step]', ...a);
await record('S9', 'Validation task linked to an exact version; association persists and is exclusive', async (e) => {
  s9('select workspace/short');
  await selectByAriaLabel('Selected workspace', 'Alpha Workspace');
  await sleep(250);
  await selectByAriaLabel('Selected Short', 'Alpha Short One');
  await sleep(500);
  s9('click submit');
  await clickEnabledByText('Submit storyboard for validation', 'button', 12000);
  s9('wait for notice');
  await waitForJs(`/saved immutable version/i.test(document.body.innerText)`, 12000);
  const notice = await versionNoticeText();
  s9('notice read');
  ok(e, /Saved immutable version .* and linked validation task /.test(notice || ''), 'UI confirmation: ' + (notice || ''));
  const mid = await dumpIdb();
  s9('idb dump done');
  const alphaDraftId = mid.drafts.find(d => d.title === 'Alpha Short One').draftId;
  const withLink = (mid.taskLinks || []).filter(l => l.draftId === alphaDraftId && !l.taskId.startsWith('legacy-'));
  ok(e, withLink.length === 1, 'one new task link recorded: ' + JSON.stringify(withLink.map(l => l.taskId.slice(0, 10))));
  linkedTaskId = withLink[0].taskId; linkedVersionId = withLink[0].versionId;
  const verRow = (mid.versions || []).find(v => v.versionId === linkedVersionId);
  ok(e, !!verRow, 'linked version exists in the versions store');
  ok(e, mid.drafts.find(d => d.draftId === alphaDraftId).currentVersionId === linkedVersionId, 'draft current version points at the linked version');
  // exactness after reload
  s9('reload for exactness check');
  await reload();
  s9('reload done');
  await waitForJs(`/local storage ready|storage issue/i.test(document.body.innerText)`, 15000);
  const post = await dumpIdb();
  s9('post-reload dump done');
  const linkAfter = (post.taskLinks || []).find(l => l.taskId === linkedTaskId);
  ok(e, !!linkAfter && linkAfter.versionId === linkedVersionId, 'after reload the task still binds the exact same version: ' + linkedVersionId.slice(0, 8));
  // exclusivity: the same taskId cannot bind a different version (IndexedDB unique index)
  const uniqueness = await evalJs(`(async()=>{const db=await new Promise((res,rej)=>{const r=indexedDB.open('nextdecode-studio-workbench');r.onsuccess=()=>res(r.result)});const out=await new Promise((res)=>{const tx=db.transaction('taskLinks','readwrite');const rq=tx.objectStore('taskLinks').add({linkId:'probe-'+'x'.repeat(20),draftId:${JSON.stringify(alphaDraftId)},versionId:${JSON.stringify(v1.versionId)},taskId:${JSON.stringify(linkedTaskId)},linkedAt:new Date().toISOString()});rq.onsuccess=()=>res('ALLOWED');rq.onerror=(ev)=>{ev.preventDefault();res('blocked:'+((rq.error||{}).name||'Error'))}});db.close();return out})()`);
  ok(e, uniqueness.startsWith('blocked:'), 're-linking the same task to a different version is rejected by the store: ' + uniqueness);
  s9('uniqueness probe done');
  // UI reflection after reload
  await selectByAriaLabel('Selected workspace', 'Alpha Workspace');
  await sleep(250);
  await selectByAriaLabel('Selected Short', 'Alpha Short One');
  await sleep(600);
  const rowHasTask = await evalJs(`(()=>{const rows=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Restore as new version');return rows.some(b=>{const s=b.closest('div')?.querySelector('small');return s&&s.textContent.includes('Task '+${JSON.stringify(linkedTaskId)})})})()`);
  ok(e, rowHasTask === true, 'version history row renders the exact task association after reload');
  await shot('09_task_link_persisted');
});

// ---------- S11: empty states, switching, reload ----------
await record('S11', 'Empty states, workspace/Short switching, reload stability', async (e) => {
  withPrompt('Gamma Empty', () => clickByText('New workspace'));
  await waitForJs(`[...document.querySelectorAll('select[aria-label="Selected workspace"] option')].some(o=>o.text==='Gamma Empty')`, 5000);
  await sleep(250);
  const emptyOpts = await selectOptions('Selected Short');
  ok(e, emptyOpts.length === 0, 'fresh workspace shows an empty Short selector (empty state rendered)');
  const emptyBeats = await beatCount();
  const staleInspector = await inspectorTitle();
  entryFinding = { emptyShortOptions: emptyOpts.length, workbenchBeatsWhileEmpty: emptyBeats, inspectorStillShowing: staleInspector };
  // switch back
  await selectByAriaLabel('Selected workspace', 'Alpha Workspace');
  await sleep(250);
  await selectByAriaLabel('Selected Short', 'Alpha Short One');
  await sleep(500);
  const backTitle = await inspectorTitle();
  ok(e, backTitle === AUTOSAVE_MARKER + ' / edited-for-v2' || backTitle === AUTOSAVE_MARKER || /edited-for-v2/.test(backTitle || ''), 'switching back restores the edited Short in the workbench: ' + backTitle);
  await reload();
  await waitForJs(`/local storage ready|storage issue/i.test(document.body.innerText)`, 15000);
  const opts = (await selectOptions('Selected workspace')).map(o => o.text);
  ok(e, opts.includes('Gamma Empty') && opts.includes('Alpha Workspace') && opts.includes('Beta Workspace'), 'all workspaces survive reload: ' + opts.join(' | '));
  const final = await dumpIdb();
  ok(e, final.workspaces.length === 4, 'IndexedDB holds 4 workspaces at the end: ' + final.workspaces.map(w => w.name).join(', '));
  ok(e, final.drafts.length === 4, 'IndexedDB holds 4 Shorts (legacy + 2 Alpha + 1 Beta): ' + final.drafts.map(d => d.title).join(', '));
  await shot('11_empty_state_and_final');
});

// ---------- S12: console / IndexedDB errors ----------
await record('S12', 'Browser console and IndexedDB error sweep', (e) => {
  const hardErrors = consoleIssues.filter(i => i.level !== 'warning' && i.level !== 'log.network');
  e.evidence.push('console entries captured: ' + consoleIssues.length + ' (errors/exceptions: ' + hardErrors.length + ')');
  e.evidence.push('network-level failures: ' + networkFails.map(f => f.url + ' — ' + f.errorText).join(' ; '));
  e.evidence.push('IndexedDB/storage log issues: ' + idbIssues.length);
  const faviconOnly = networkFails.every(f => /favicon/i.test(f.url));
  if (hardErrors.length > 0) throw new Error(hardErrors.length + ' hard console errors: ' + hardErrors[0].text);
  if (!faviconOnly) throw new Error('non-favicon network failure: ' + networkFails.filter(f => !/favicon/i.test(f.url)).map(f => f.url).join(', '));
  if (networkFails.length) e.evidence.push('only benign favicon.ico 404s observed (no app resource failures)');
});

// ---------- finalize ----------
const summary = {
  browser: version.Browser,
  ranAt: new Date().toISOString(),
  scenarios: ledger,
  dbMeta,
  consoleIssues,
  networkFails,
  idbIssues,
  extraFinding: entryFinding,
  tally: {
    pass: ledger.filter(l => l.status === 'PASS').length,
    fail: ledger.filter(l => l.status === 'FAIL').length,
  },
};
fs.writeFileSync(RESULTS, JSON.stringify(summary, null, 2));
console.log('==== TALLY: ' + summary.tally.pass + ' PASS / ' + summary.tally.fail + ' FAIL ====');
ws.close();
process.exit(summary.tally.fail > 0 ? 2 : 0);
