import {useQuery} from '@tanstack/react-query';
import {Link,useParams} from '@tanstack/react-router';
import {ArrowLeft,RefreshCw,Clock3,AlertTriangle,CheckCircle2,ShieldAlert,ChevronDown,ChevronUp,FileInput,FileOutput} from 'lucide-react';
import {useMemo,useState} from 'react';
import {api,ApiError} from '../api';
import {Page,Panel,Badge,Loading,ErrorBox,Empty} from '../components';
import {taskStateGroup,taskStateIsActive,taskStateLabel,taskStateTone} from '../taskStatus';
import {presentTaskEvent} from '../taskEvents';
export function Task(){
 const {taskId}=useParams({from:'/tasks/$taskId'});
 const q=useQuery({queryKey:['task',taskId],queryFn:()=>api.task(taskId),refetchInterval:(query)=>{const s=query.state.data?.task.status;return s&&taskStateIsActive(s)?3000:false;}});
 const [showInput,setShowInput]=useState(false),[showResult,setShowResult]=useState(false),[eventFilter,setEventFilter]=useState('all');
 const events=useMemo(()=>[...(q.data?.events??[])].sort((a,b)=>a.event_id-b.event_id),[q.data?.events]);
 const visibleEvents=useMemo(()=>events.filter(e=>{
  if(eventFilter==='all')return true;
  if(eventFilter==='errors')return ['failed','blocked','lease_expired'].includes(e.event.toLowerCase());
  if(eventFilter==='worker')return /claim|heartbeat|lease|worker/.test(e.event.toLowerCase());
  return !['failed','blocked','lease_expired'].includes(e.event.toLowerCase())&&!/claim|heartbeat|lease|worker/.test(e.event.toLowerCase());
 }),[events,eventFilter]);
 const head=<Page eyebrow="EXECUTION / TASK DETAIL" title="Task inspection" description="Read-only task inputs, execution outcome and persisted lifecycle history." actions={<><Link className="btn" to="/runs"><ArrowLeft size={14}/> Back to runs</Link><button className="btn" onClick={()=>void q.refetch()}><RefreshCw size={14}/> Refresh</button></>}/>;
 if(q.isLoading)return <>{head}<Panel><Loading/></Panel></>;
 if(q.error instanceof ApiError&&q.error.status===404)return <>
  <Page eyebrow="EXECUTION / TASK DETAIL" title="Task not found" description="No persisted autonomy task matches this identifier." actions={<Link className="btn" to="/runs"><ArrowLeft size={14}/> Back to work queue</Link>}/>
  <Panel><div className="empty"><b>Task {taskId} was not found</b><p>It may have been removed, or the identifier may be mistyped. Task state was not changed.</p></div></Panel>
 </>;
 if(q.error)return <>{head}<Panel><ErrorBox error={q.error} onRetry={()=>void q.refetch()}/></Panel></>;
 if(!q.data)return <>{head}<Panel><div className="empty"><b>Task data unavailable</b><p>The API returned no task payload. Task state was not changed.</p></div></Panel></>;
 const {task}=q.data,active=taskStateIsActive(task.status);
 const inputView=task.payload_json?presentTaskEvent('input',task.payload_json):null;
 const resultView=task.result_json?presentTaskEvent('result',task.result_json):null;
 const firstEvent=events[0],lastEvent=events[events.length-1];
 const elapsed=firstEvent&&lastEvent?Math.max(0,Math.round((Date.parse(lastEvent.at)-Date.parse(firstEvent.at))/1000)):null;
 const durationLabel=elapsed===null?'—':elapsed<60?String(elapsed)+'s':String(Math.floor(elapsed/60))+'m '+String(elapsed%60)+'s';
 return <>
 {head}
 <div className="task-debug-metrics">
  <div><small>Lifecycle events</small><b>{events.length}</b><span>Persisted records</span></div>
  <div><small>Attempt budget</small><b>{task.attempts} / {task.max_attempts}</b><span>Recorded attempts</span></div>
  <div><small>Observed event span</small><b>{durationLabel}</b><span>First to latest event</span></div>
  <div><small>Latest event</small><b>{lastEvent?presentTaskEvent(lastEvent.event).title:'—'}</b><span>{lastEvent?new Date(lastEvent.at).toLocaleTimeString():'No event recorded'}</span></div>
 </div>
 <div className="two-col">
  <Panel>
   <div className="section-head"><div><div className="eyebrow">TASK ID</div><h3 className="mono">{task.task_id}</h3></div><Badge tone={taskStateTone(task.status)}>{taskStateLabel(task.status)}</Badge></div>
   <div className="details">{Object.entries({'Capability':task.task_type,'Priority':task.priority,'Attempts':task.attempts+' / '+task.max_attempts,'Plan ID':task.plan_id||'—','Created':new Date(task.created_at).toLocaleString(),'Updated':new Date(task.updated_at).toLocaleString(),'Lease owner':task.lease_owner||'—','Lease expiry':task.lease_until?new Date(task.lease_until).toLocaleString():'—','Error code':task.error_code||'—'}).map(([k,v])=><div key={k}><small>{k}</small><b>{String(v)}</b></div>)}</div>
   {active&&<div className="footnote"><Clock3 size={13}/> This task is still active; details refresh every 3 seconds.</div>}
   {taskStateGroup(task.status)==='failed'&&<div className="boundary"><div><AlertTriangle size={16}/><span><b>Execution failed</b><small>{task.error_code||'No structured error code was returned.'} Inspect the event history before retrying.</small></span></div></div>}
   {taskStateGroup(task.status)==='blocked'&&<div className="boundary"><div><ShieldAlert size={16}/><span><b>Execution blocked</b><small>This task needs operator attention. The dashboard does not automatically unblock or retry it.</small></span></div></div>}
   {taskStateGroup(task.status)==='completed'&&<div className="footnote"><CheckCircle2 size={14}/> Task execution completed. This is not human content approval or permission to publish.</div>}
   {inputView&&<div className="result-inspector"><button className="btn" onClick={()=>setShowInput(v=>!v)}>{showInput?<ChevronUp size={14}/>:<ChevronDown size={14}/>} <FileInput size={14}/> {showInput?'Hide':'Inspect'} task input</button>{showInput&&<div className="result-details">{inputView.details.map(([key,value])=><code key={key}><strong>{key}:</strong> {value}</code>)}</div>}</div>}
   {resultView&&<div className="result-inspector"><button className="btn" onClick={()=>setShowResult(v=>!v)}>{showResult?<ChevronUp size={14}/>:<ChevronDown size={14}/>} <FileOutput size={14}/> {showResult?'Hide':'Inspect'} task output & evidence</button>{showResult&&<div className="result-details">{resultView.details.map(([key,value])=><code key={key}><strong>{key}:</strong> {value}</code>)}</div>}</div>}
  </Panel>
  <Panel>
   <div className="section-head"><div><div className="eyebrow">PERSISTED HISTORY</div><h3>Execution events</h3></div><Badge>{visibleEvents.length} / {events.length} events</Badge></div>
   <div className="task-event-toolbar"><label htmlFor="task-event-filter">Show</label><select id="task-event-filter" value={eventFilter} onChange={e=>setEventFilter(e.target.value)}><option value="all">All events</option><option value="errors">Failures & blocks</option><option value="worker">Worker & lease</option><option value="lifecycle">Lifecycle</option></select><small>Oldest first · persisted event IDs</small></div>
   {visibleEvents.length ? <div className="events task-event-list">{visibleEvents.map(e=>{const view=presentTaskEvent(String(e.event),e.detail_json??undefined);const kind=['failed','blocked','lease_expired'].includes(e.event.toLowerCase())?'error':/succeed|complete/.test(e.event.toLowerCase())?'success':'normal';return <div className="task-event-row" data-kind={kind} key={e.event_id}><i/><section><div className="task-event-title"><b>{view.title}</b><span>#{e.event_id}</span></div><small>{new Date(e.at).toLocaleString()}</small>{view.details.map(([key,value],index)=><code key={String(e.event_id)+'-'+index}><strong>{key}:</strong> {value}</code>)}</section></div>})}</div> : <Empty title={events.length?'No events in this filter':'No event history'} detail={events.length?'Choose another event category to inspect the persisted history.':'No lifecycle events were returned for this task.'}/>}
   <div className="footnote">Event details, inputs and outputs are sanitized and bounded for display. This is local lifecycle evidence, not a complete LLM/tool-call trace.</div>
  </Panel>
 </div>
 </>;
}
