import {ShieldCheck,AlertTriangle,Workflow} from 'lucide-react';
import {Link} from '@tanstack/react-router';
import {Page,Panel,Badge,SectionHead,Empty,CommandLine,PublishControl} from '../components';

export function Distribution(){
 return <><Page eyebrow="GOVERN & RELEASE / DISTRIBUTION" title="Distribution & publish" description="Where an approved Short can go, what the pipeline verifies before it uploads, and the exact local publish command for manual or scheduled release." actions={<Link className="btn" to="/reviews">Review desk →</Link>}/>
 <div className="governance-banner"><div className="governance-banner-icon"><ShieldCheck size={21}/></div><div><b>Owner-gated distribution</b><p>Every upload path — YouTube, Instagram, Facebook — requires your same-day approval bound to the exact reviewed artifacts. The controls below prepare the run; they never upload from the browser.</p></div><Badge tone="good">Owner gate on</Badge></div>
 <div className="governance-grid"><div className="operations-main">
 <Panel><SectionHead label="PUBLISH CONTROL" title="Manual or scheduled — pick one" action={<Badge tone="warn">Local execution</Badge>}/>
 <PublishControl blocked reason="The active package fails integrity (digest mismatch) and the review checklist is incomplete — the CLI will refuse to upload until a fresh package passes every gate."/>
 </Panel>
 <Panel><SectionHead label="PLATFORMS" title="Destination readiness" action={<Badge tone="warn">Owner dependencies</Badge>}/>
 <div className="boundary-list">
 <div><ShieldCheck size={16}/><span><b>YouTube — Shorts &amp; Long-form</b><small>Upload authorization already succeeded once (private upload). Public release needs a separate owner public-release authorization. Implementation exists in app.publish with the OAuth token already stored.</small></span><Badge tone="good">Private ready</Badge></div>
 <div><AlertTriangle size={16}/><span><b>Instagram Reels</b><small>Configured in .env and setup_check reports READY (2026-11-16) — the Instagram media host was verified too. But permissions have never been exercised by a real publish, so the first owner-approved cross-post remains the decisive test.</small></span><Badge tone="warn">Configured · unverified</Badge></div>
 <div><AlertTriangle size={16}/><span><b>Facebook Reels</b><small>Configured in .env and setup_check reports READY (2026-11-16). Same Meta dependency — permissions unverified until the first owner-approved coordinated cross-post.</small></span><Badge tone="warn">Configured · unverified</Badge></div>
 </div>
 <p className="footnote">Verified 2026-11-16: setup_check reports all required credentials present. Existence is not permission — no real publish has ever been executed.</p>
 </Panel>
 <Panel><SectionHead label="VERIFY SETUP" title="Read-only preflight — ran today, all READY" action={<Badge tone="good">setup_check READY</Badge>}/>
 <p className="project-muted"><strong>2026-11-16 result:</strong> all required credentials and local tools are present (AI provider, FFmpeg/ffprobe/edge-tts, YouTube OAuth + refresh token, Instagram + media host, Facebook, the full strong-pipeline module chain, Telegram alerts, stock B-roll). 23 optional integrations are not configured — none are required. The check validates existence, not token permissions.</p>
 <CommandLine command="wsl.exe -d Ubuntu --exec /home/demon/shorts_studio/venv/bin/python setup_check.py" label="Preflight"/>
 </Panel>
 <Panel><SectionHead label="PUBLISH PATH" title="Approval → authorization → execution" action={<Badge tone="warn">Owner gate</Badge>}/>
 <div className="identity-chain">{['Watch the exact file','Approve (local command)','Authorization verifies digest & same-day window','Publish run executes','Uploads to configured destinations'].map((n,i)=><div className="identity-node" key={n}><span>{String(i+1).padStart(2,'0')}</span><b>{n}</b></div>)}</div>
 <CommandLine command="wsl.exe -d Ubuntu --exec /home/demon/shorts_studio/venv/bin/python -m app.review.approve_review --interactive" label="Approve"/>
 <p className="footnote">Scheduled mode runs at 20:00 IST (Asia/Kolkata) only. Manual mode runs immediately after your approval. Either way: no approval = no upload, and the digest must match.</p>
 </Panel>
 </div><div className="governance-side">
 <Panel><SectionHead label="LAST PUBLISHED" title="Views & performance" action={<Link className="link" to="/analytics">Analytics →</Link>}/>
 <Empty title="No published videos yet" detail="feedback_ledger.csv has never been filled and the analytics collector has not been authorized. No views, reach or retention numbers exist. Any UI here claiming views would be fabricated."/>
 </Panel>
 <Panel><SectionHead label="ROADMAP" title="Where this is heading" action={<Badge tone="info">From docs/ROADMAP.md</Badge>}/>
 <div className="governance-gates"><div><Badge tone="warn">Phase 2</Badge><span><b>Distribution &amp; operating readiness</b><small>All destinations pass setup_check; owner-approved first cross-post; scheduler proven; 5 review-passed Shorts/week.</small></span></div><div><Badge tone="warn">Phase 3</Badge><span><b>Performance learning loop</b><small>24h/7d views per platform; cohort review of 20 videos; one weekly experiment; analytics collection authorized.</small></span></div><div><Badge tone="warn">Phase 4</Badge><span><b>Scale &amp; monetization</b><small>Scale only on repeatable audience evidence; monetization as eligibility gaps, never promised income.</small></span></div></div>
 </Panel>
 <Panel><SectionHead label="WHAT THIS PAGE IS NOT" title="Hard boundaries"/>
 <ul className="governance-rules"><li>It does not upload, approve or publish anything itself.</li><li>It cannot bypass the approval or authorization gates.</li><li>No metric shown here without a real platform source.</li><li>The 20:00 IST scheduler and the owner-run command are the only publish paths.</li></ul>
 </Panel>
 </div></div>
 <div className="governance-disclaimer"><Workflow size={16}/><span><b>Why the browser has no upload call</b><small>The backend exposes no publish endpoint, and publishing crosses the protected-action boundary. This page gives you a working mode switch, command copy and a downloadable script — the actual upload always happens in the locally gated CLI, never in a browser tab.</small></span><Badge tone="warn">Owner-gated</Badge></div>
 </>}