import {useQuery} from '@tanstack/react-query';
import {AlertCircle,ArrowRight,BarChart3,Clock3,RefreshCw,Workflow} from 'lucide-react';
import {Link} from '@tanstack/react-router';
import {api} from '../api';
import {Page,Panel,Badge,Loading,ErrorBox,Empty} from '../components';
import {taskStateGroup} from '../taskStatus';

function ago(value?:string|null){
 if(!value)return '—';
 const time=new Date(value).getTime();
 if(!Number.isFinite(time))return '—';
 const seconds=Math.max(0,Math.floor((Date.now()-time)/1000));
 return seconds<60?seconds+'s ago':seconds<3600?Math.floor(seconds/60)+'m ago':seconds<86400?Math.floor(seconds/3600)+'h ago':Math.floor(seconds/86400)+'d ago';
}
const label=(value:string)=>value.replace(/[._-]+/g,' ').replace(/\b\w/g,c=>c.toUpperCase());

export function Home(){
 const health=useQuery({queryKey:['health'],queryFn:api.health,refetchInterval:15000});
 const tasksQuery=useQuery({queryKey:['tasks'],queryFn:api.tasks,refetchInterval:10000});
 const runsQuery=useQuery({queryKey:['production-runs'],queryFn:api.productionRuns,refetchInterval:15000});
 const tasksLoaded=!!tasksQuery.data;
 const runsLoaded=!!runsQuery.data;
 const tasksUnavailable=!tasksLoaded&&tasksQuery.isError;
 const runsUnavailable=!runsLoaded&&runsQuery.isError;
 const healthUnavailable=!health.data&&health.isError;
 const refresh=()=>{void health.refetch();void tasksQuery.refetch();void runsQuery.refetch()};
 const head=<Page eyebrow="WORKSPACE" title="Home" description="Your content production, operational attention and published-content activity in one place." actions={<button className="btn" onClick={refresh}><RefreshCw size={14}/> Refresh</button>}/>;
 if(healthUnavailable&&tasksUnavailable&&runsUnavailable)return <>{head}<Panel><ErrorBox error={health.error??tasksQuery.error??runsQuery.error} onRetry={refresh}/></Panel></>;
 if(!health.data&&!tasksLoaded&&!runsLoaded)return <>{head}<Panel><Loading/></Panel></>;

 const tasks=tasksQuery.data?.tasks??[];
 const active=tasks.filter(task=>taskStateGroup(task.status)==='running').sort((a,b)=>b.updated_at.localeCompare(a.updated_at));
 const queued=tasks.filter(task=>taskStateGroup(task.status)==='pending').sort((a,b)=>b.updated_at.localeCompare(a.updated_at));
 const productionRuns=runsQuery.data?.runs??[];
 const liveRuns=productionRuns.filter(run=>run.status==='in_progress');
 const STALE_RUN_MS=60*60*1000;
 const stalledRuns=liveRuns.filter(run=>{const started=Date.parse(run.started_at??'');return Number.isFinite(started)&&Date.now()-started>STALE_RUN_MS;});
 const stalledIds=new Set(stalledRuns.map(run=>run.run_id));
 const runIsStalled=(run:{run_id:string})=>stalledIds.has(run.run_id);
 const activeRuns=liveRuns.filter(run=>!stalledIds.has(run.run_id));
 const failedRuns=productionRuns.filter(run=>run.status==='failed');
 const completedRuns=productionRuns.filter(run=>['ok','completed','succeeded','success'].includes(run.status));
 const artifactTotal=productionRuns.reduce((sum,run)=>sum+run.artifact_count,0);
 const stageTotal=productionRuns.reduce((sum,run)=>sum+run.stage_count,0);
 const runningKnown=tasksLoaded&&runsLoaded?active.length+activeRuns.length:null;
 const runningTasksKnown=tasksLoaded?active.length:null;
 const runningTasksNote=!tasksLoaded?(tasksUnavailable?'Task data unavailable':'Task data loading…'):'';
 const queueKnown=tasksLoaded?queued.length:null;
 const attentionKnown=tasksLoaded&&runsLoaded?tasks.filter(task=>['failed','blocked'].includes(taskStateGroup(task.status))).length+failedRuns.length:null;
 const runningNote=!tasksLoaded&&!runsLoaded?(tasksUnavailable&&runsUnavailable?'Task and run data unavailable':tasksUnavailable?'Task data unavailable':runsUnavailable?'Run data unavailable':'Checking task and run data…'):!tasksLoaded?(tasksUnavailable?'Task data unavailable':'Task data loading…'):!runsLoaded?(runsUnavailable?'Run data unavailable':'Run data loading…'):'';
 const attentionNote=!tasksLoaded&&!runsLoaded?(tasksUnavailable&&runsUnavailable?'Task and run data unavailable':tasksUnavailable?'Task data unavailable':runsUnavailable?'Failed-run data unavailable':'Checking task and run data…'):!tasksLoaded?(tasksUnavailable?'Task data unavailable':'Task data loading…'):!runsLoaded?(runsUnavailable?'Failed-run data unavailable':'Failed-run data loading…'):'';
 const queueCounts=health.data?.queue_counts??{};
 const awaitingWork=Object.entries(queueCounts).reduce((total,[status,count])=>taskStateGroup(status)==='pending'||taskStateGroup(status)==='running'?total+count:total,0);
 const workerCount=health.data?.active_workers??0;
 const expiredLeases=health.data?.expired_running_leases??0;
 const statusReasons=[stalledRuns.length?stalledRuns.length+' stalled run'+(stalledRuns.length===1?'':'s'):'',expiredLeases?expiredLeases+' expired lease'+(expiredLeases===1?'':'s'):'',awaitingWork>0&&workerCount===0?awaitingWork+' queued with no live worker':''].filter(Boolean);
 const degraded=statusReasons.length>0;
 const failedNote=failedRuns.length?failedRuns.length+' failed run'+(failedRuns.length===1?'':'s')+' on record':'';
 const healthLabel=healthUnavailable?'Runtime status unavailable':!health.data?'Checking runtime status…':!health.data.database_accessible?'Workspace needs attention':degraded?'Workspace degraded':'Workspace operational';
 const healthDetail=healthUnavailable?'Health endpoint unreachable · saved records are shown where available':!health.data?'Local runtime · auto-updates every 10–15 seconds':!health.data.database_accessible?'Task database is not reachable':degraded?'Local runtime · '+statusReasons.join(' · ')+(failedNote?' · '+failedNote:''):'Local runtime · '+workerCount+' worker'+(workerCount===1?'':'s')+' alive'+(failedNote?' · '+failedNote:'')+' · auto-updates every 10–15 seconds';
 const statusOffline=!health.data||!health.data.database_accessible||degraded;
 const workItems=(runsLoaded?liveRuns.slice(0,5).map(run=><div className="home-work-item" key={run.run_id}>
   <span className="home-work-icon"><Workflow size={17}/></span>
   <div className="home-work-copy"><b>{run.topic||'Production run'}</b><small>Shorts Studio production run · Started {ago(run.started_at)}</small><small>{run.active_stage ? 'Currently: '+label(run.active_stage) : 'Between recorded stages'} · {run.stage_count} stages · {run.artifact_count} artifacts</small></div>
   <Badge tone={runIsStalled(run)?'warn':'info'}>{runIsStalled(run)?'Stalled':'In progress'}</Badge>
   <Link className="link" to="/runs">Inspect <ArrowRight size={13}/></Link>
  </div>):[]).concat(tasksLoaded?active.slice(0,5).map(task=><div className="home-work-item" key={task.task_id}>
   <span className="home-work-icon"><Clock3 size={17}/></span>
   <div className="home-work-copy"><b>{label(task.task_type)}</b><small>Task {task.task_id.slice(0,12)}… · Updated {ago(task.updated_at)}</small><small>Attempt {task.attempts} of {task.max_attempts}</small></div>
   <Badge tone="info">Running</Badge>
   <Link className="link" to="/tasks/$taskId" params={{taskId:task.task_id}}>Inspect <ArrowRight size={13}/></Link>
  </div>):[]);

 return <>
  {head}
  <div className="home-statusline">{health.data?<span className={statusOffline?'home-status-dot offline':'home-status-dot'}/>:null}<b>{healthLabel}</b><span>{healthDetail}</span></div>

  <div className="home-summary">
   <div><small>Running tasks</small><strong>{runningTasksKnown??'—'}</strong>{runningTasksKnown===null&&runningTasksNote&&<small>{runningTasksNote}</small>}</div>
   <div><small>Waiting in queue</small><strong>{queueKnown??'—'}</strong>{queueKnown===null&&<small>{tasksUnavailable?'Task data unavailable':'Task data loading…'}</small>}</div>
   <div className={attentionKnown!==null&&attentionKnown>0?'attention':''}><small>Needs attention</small><strong>{attentionKnown??'—'}</strong>{attentionKnown===null&&attentionNote&&<small>{attentionNote}</small>}</div>
  </div>

  <Panel className="home-work-panel">
   <div className="home-section-title"><div><span className="eyebrow">RIGHT NOW</span><h2>What’s happening</h2></div><Badge tone={runningKnown!==null?(runningKnown>0?'info':stalledRuns.length>0?'warn':'neutral'):tasksUnavailable||runsUnavailable?'warn':'neutral'}>{runningKnown!==null?(runningKnown>0?runningKnown+' active':stalledRuns.length>0?stalledRuns.length+' stalled':'0 active'):tasksUnavailable||runsUnavailable?'Unavailable':'—'}</Badge></div>
   {tasksUnavailable&&runsUnavailable?<ErrorBox error={tasksQuery.error}/>:tasksUnavailable||runsUnavailable?<>{tasksUnavailable&&<ErrorBox error={tasksQuery.error}/>}{runsUnavailable&&<ErrorBox error={runsQuery.error}/>}{workItems.length>0&&<div className="home-work-list">{workItems}</div>}</>:workItems.length>0?<div className="home-work-list">{workItems}</div>:tasksLoaded||runsLoaded?<Empty title="Nothing is running right now" detail="When a task or production run starts, it will appear here."/>:<Loading/>}
  </Panel>

  <div className="home-secondary-grid">
   <Panel>
    <div className="home-section-title"><div><span className="eyebrow">CONTENT PRODUCTION</span><h2>Production pipeline activity</h2></div><Link className="link" to="/runs">All runs <ArrowRight size={13}/></Link></div>
    {runsUnavailable?<ErrorBox error={runsQuery.error}/>:runsLoaded?<><div className="home-production-stats">
     <div><strong>{productionRuns.length}</strong><small>Runs</small></div>
     <div><strong>{completedRuns.length}</strong><small>Completed</small></div>
     <div><strong>{stageTotal}</strong><small>Stages</small></div>
     <div><strong>{artifactTotal}</strong><small>Artifacts</small></div>
    </div>
    {productionRuns.length?<div className="home-compact-list">{productionRuns.slice(0,4).map(run=><div key={run.run_id}><div><b>{run.topic||'Production run'}</b><small>{run.stage_count} stages · {run.artifact_count} artifacts · {ago(run.started_at)}</small></div><Badge tone={run.status==='failed'?'bad':run.status==='in_progress'?(runIsStalled(run)?'warn':'info'):run.status==='ok'||run.status==='completed'||run.status==='succeeded'||run.status==='success'?'good':'neutral'}>{run.status==='in_progress'&&runIsStalled(run)?'Stalled':label(run.status)}</Badge></div>)}</div>:<Empty title="No production runs recorded" detail="Persisted Shorts Studio runs will appear here when available."/>}
    <p className="home-data-note">Counts reflect saved run manifests only. They do not imply that unrecorded pipeline stages ran.</p></>:<Loading/>}
   </Panel>

   <Panel>
    <div className="home-section-title"><div><span className="eyebrow">AFTER PUBLISHING</span><h2>Published content activity</h2></div><Badge tone="warn">Not connected</Badge></div>
    <div className="home-performance-empty">
     <span><BarChart3 size={20}/></span>
     <div><b>Platform analytics aren’t connected yet</b><p>Views, likes, comments, shares, subscribers and watch-time activity will appear here once authorized YouTube or Instagram analytics are available.</p></div>
    </div>
    <div className="home-performance-footer"><span>No audience metrics are being estimated or fabricated.</span><Link className="link" to="/analytics">Analytics details <ArrowRight size={13}/></Link></div>
   </Panel>
  </div>

  <div className="home-operator-grid">
   <Panel>
    <div className="home-section-title"><div><span className="eyebrow">UP NEXT</span><h2>Waiting in queue</h2></div><Badge>{queueKnown??'—'}</Badge></div>
    {tasksUnavailable?<ErrorBox error={tasksQuery.error}/>:tasksLoaded?(queued.length?<div className="home-compact-list">{queued.slice(0,5).map(task=><div key={task.task_id}><div><b>{label(task.task_type)}</b><small>{task.task_id.slice(0,12)}… · {ago(task.updated_at)}</small></div><Link className="link" to="/tasks/$taskId" params={{taskId:task.task_id}}>Inspect <ArrowRight size={13}/></Link></div>)}</div>:<Empty title="Queue is clear" detail="No tasks are waiting for a worker."/>) :<Loading/>}
 {tasksLoaded&&queued.length>5&&<Link className="home-more" to="/runs">View all tasks <ArrowRight size={13}/></Link>}
   </Panel>

  </div>

  <div className="home-footer-note"><AlertCircle size={14}/><span>Production counts come from saved local manifests. Published-content metrics require a connected platform analytics source. Task completion does not mean content approval or publishing.</span></div>
 </>;
}
