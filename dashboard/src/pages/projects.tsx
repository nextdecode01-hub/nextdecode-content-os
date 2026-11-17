import {useMemo} from 'react';
import {useQuery} from '@tanstack/react-query';
import {ArrowRight,Sparkles,Video,ShieldCheck,AlertTriangle,Workflow} from 'lucide-react';
import {Link} from '@tanstack/react-router';
import {api} from '../api';
import {Page,Panel,Badge,SectionHead,Loading,ErrorBox,Empty} from '../components';

type Series={name:string;promise:string;kws:string[]};
const series:Series[]=[
 {name:'AI You Can Use',promise:'One concrete tool or workflow, who it helps, and one real limitation.',kws:['tool','workflow','prompt','skill','tip','habit','how-to']},
 {name:'Hype Check',promise:'Take a specific claim and compare it with what the paper, product documentation, or credible report actually establishes.',kws:['hype','claim','myth','fact','true','false','debunk','wrong','misinformation']},
 {name:'What Changed',promise:'Explain a genuinely recent release, research result, or industry shift; say what changed and who should care.',kws:['change','changed','new','release','update','launch','announce','version','shift']},
 {name:'How It Works',promise:'Explain one hard concept with a simple analogy, then state where the analogy stops working.',kws:['how','mechanism','internals','explain','inside','science']},
 {name:'Startup Breakdown',promise:'Explain the user problem, product mechanism, business model, and one trade-off using sourced facts.',kws:['startup','business','model','funding','valuation','company','raised','market']},
];
const matchSeries=(topic:string)=>{const t=(topic||'').toLowerCase();for(const s of series){if(s.kws.some(k=>t.includes(k)))return s.name;}return null};
const ago=(s?:string|null)=>{if(!s)return '—';const d=Date.now()-new Date(s).getTime();if(!Number.isFinite(d))return '—';const n=Math.max(0,Math.floor(d/1000));return n<86400?Math.floor(n/3600)+'h ago':Math.floor(n/86400)+'d ago'};

export function Projects(){
 const runs=useQuery({queryKey:['production-runs'],queryFn:()=>api.productionRuns(),staleTime:60000});
 const data=runs.data;
 const list=data?.runs??[];
 const grouped=useMemo(()=>{
  const map=new Map<string,typeof list>();
  const unmatched:typeof list=[];
  for(const run of list){const key=matchSeries(run.topic||'');if(key){map.set(key,[...(map.get(key)??[]),run])}else{unmatched.push(run)}}
  const rows=series.map(s=>({series:s,runs:map.get(s.name)??[]}));
  const max=Math.max(1,...rows.map(r=>r.runs.length),unmatched.length);
  return {rows,unmatched,max};
 },[list]);
 const total=list.length;
 const completed=list.filter(r=>r.status==='ok'||r.status==='succeeded'||r.status==='completed').length;
 const gaps=grouped.rows.filter(r=>r.runs.length===0).map(r=>r.series.name);
 const strongest=grouped.rows.slice().sort((a,b)=>b.runs.length-a.runs.length)[0];
 return <><Page eyebrow="PLAN / EDITORIAL" title="Content planning" description="Series strategy paired with recorded production evidence. Counts come from saved Shorts runs matched by topic keywords; this is not a canonical content calendar or an approval workflow." actions={<Link className="btn btn-primary" to="/studio"><Sparkles size={14}/> Draft in Studio</Link>}/>
 {runs.isLoading?<Panel><Loading/></Panel>:runs.error?<Panel><ErrorBox error={runs.error}/></Panel>:!total?<Panel><SectionHead label="EDITORIAL SERIES" title="No recorded runs yet"/><Empty title="No Shorts have been recorded in outputs/runs" detail="Series run counts will appear once production runs exist. Draft your first Short in Studio."/><div className="empty-action"><Link className="btn btn-primary" to="/studio"><Sparkles size={14}/> Create first Short</Link></div></Panel>:<>
 <div className="planner-grid">
 <div className="operations-main">
 <Panel><SectionHead label="EDITORIAL SERIES" title="Repeatable series from NEXTDECODE strategy" action={<Badge tone="info">{series.length} series</Badge>}/>
 <div>{grouped.rows.map(({series:s,runs:matched})=>{const count=matched.length,zero=count===0,fill=Math.round(count/grouped.max*100);return <article className="series-card" key={s.name}>
 <div className="series-run-row"><div><h3>{s.name}</h3><p className="series-promise">{s.promise}</p></div><div style={{textAlign:'right'}}><div className={'series-count'+(zero?' zero':'')}>{count}</div><small style={{font:'8px DM Mono, monospace',color:'var(--muted)',letterSpacing:'.08em'}}>{zero?'NO RUNS YET':'RUNS RECORDED'}</small></div></div>
 <div className="series-bar"><i style={{'--fill':fill+'%'} as any}/></div>
 {matched.length?<div>{matched.slice(0,3).map(run=><div className="planner-topic" key={run.run_id}><b title={run.topic}>{run.topic}</b><time>{ago(run.started_at)}</time><Badge tone={run.status==='failed'?'bad':run.status==='ok'?'good':'warn'}>{run.status}</Badge></div>)}</div>:<p className="series-rule">No recorded Shorts match this lane yet. The evidence gap is real: nothing here has been run.</p>}
 </article>})}</div>
 <p className="footnote">Series names and promises quoted from docs/CONTENT_STRATEGY.md · runs matched to a series by topic keyword, not by a canonical Content ID mapping · sources matched greedily by priority, unmatched topics counted separately.</p>
 </Panel>
 </div>
 <div className="operations-side">
 <Panel><SectionHead label="RUN EVIDENCE" title="Recorded output"/><div className="ops-signal"><span><Video size={14}/> Total recorded runs</span><b>{total}</b></div><div className="ops-signal"><span><ShieldCheck size={14}/> Completed (ok)</span><b>{completed}</b></div><div className="ops-signal"><span><Workflow size={14}/> Strongest lane</span><b>{strongest?.series.name??'—'} · {strongest?.runs.length??0}</b></div>{gaps.length?<div className="ops-signal"><span><AlertTriangle size={14}/> Lanes with zero recorded runs</span><Badge tone="warn">{gaps.length}</Badge></div>:<div className="ops-signal"><span><ShieldCheck size={14}/> Every lane has a recorded run</span><Badge tone="good">Yes</Badge></div>}<p className="ops-footnote">Evidence from outputs/runs/*/manifest.json. Counts reflect persisted manifests only; they do not estimate reach, engagement or production quality.</p></Panel>
 <Panel><SectionHead label="PLANNING SUGGESTION" title="Empty lanes first" action={<Badge tone="warn">Heuristic</Badge>}/>{gaps.length?<><p className="planner-topic" style={{borderTop:0,paddingTop:4}}><b>Record for {gaps[0]}</b></p><p className="project-muted" style={{marginTop:8}}>{series.find(s=>s.name===gaps[0])?.promise}</p><p className="ops-footnote">Zero recorded runs in this lane. A suggestion derived from recorded counts only; editorial judgment stays human.</p><Link className="link" to="/studio">Draft one in Studio →</Link></>:<><p className="project-muted" style={{marginTop:4}}>All series lanes have at least one recorded run. Rotate lanes when the topic supports it — never force a weak topic to fill a slot (NEXTDECODE strategy).</p><Link className="link" to="/studio">Open Studio →</Link></>}</Panel>
 <Panel><SectionHead label="GUARDRAILS" title="Quality before volume"/><ul className="governance-rules"><li>Return to the evidence before picking the lane — never force a weak topic.</li><li>Rotate series across runs when the topic supports it.</li><li>Approval ≠ authorization ≠ publish — a recorded run is not publishable until human review clears it.</li><li>Topic choices are reasoned editorial estimates — no audience-winner claims without platform analytics.</li></ul></Panel>
 </div>
 </div>
 {grouped.unmatched.length?<Panel><SectionHead label="UNMATCHED TOPICS" title={grouped.unmatched.length+' recorded runs matched no series'} action={<Badge tone="warn">Keyword gap</Badge>}/><div className="home-compact-list">{grouped.unmatched.slice(0,5).map(run=><div key={run.run_id}><div><b>{run.topic}</b><small>{ago(run.started_at)}</small></div><Badge tone="neutral">Unmatched</Badge></div>)}</div><p className="footnote">No keyword matched. These topics likely belong to a series but need a human judgement call — this heuristic is not a canonical classifier.</p></Panel>:null}
 </>}</>}
