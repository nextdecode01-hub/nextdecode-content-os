from pathlib import Path
import re, shutil
src=Path('/home/demon/shorts_studio/ui-prototype/command-deck-v2/index.html')
out=Path('/home/demon/shorts_studio/ui-prototype/command-deck-v3/index.html')
s=src.read_text()
# Replace the first application sidebar with a compact icon-and-label rail.
rail='''<aside id="sidebar" class="rail">
<div class="brand"><div class="orb">N</div><div class="brandword"><b>ND</b><small>CONTENT OS</small></div></div>
<div class="railnav">
<div class="railgroup"><small>COMMAND</small><nav class="nav">
<button class="active" data-page="home" title="Command Center"><span class="ico">⌂</span><em>Home</em></button>
<button data-page="portfolio" title="Portfolio & Projects"><span class="ico">▦</span><em>Projects</em></button>
<button data-page="work" title="Execution Queue"><span class="ico">☷</span><em>Work</em></button></nav></div>
<div class="railgroup"><small>CREATE</small><nav class="nav">
<button data-page="creator" title="Creator Workspace"><span class="ico">✧</span><em>Create</em></button>
<button data-page="studio" title="Production Studio"><span class="ico">▣</span><em>Studio</em></button>
<button data-page="library" title="Content & Asset Library"><span class="ico">▧</span><em>Library</em></button>
<button data-page="research" title="Research Desk"><span class="ico">⌕</span><em>Research</em></button></nav></div>
<div class="railgroup"><small>ORCHESTRATE</small><nav class="nav">
<button data-page="agents" title="Agent Command"><span class="ico">⌘</span><em>Agents</em><span class="count">05</span></button>
<button data-page="workflows" title="Workflow Canvas"><span class="ico">⤳</span><em>Flows</em></button>
<button data-page="runs" title="Run Observatory"><span class="ico">◷</span><em>Runs</em></button>
<button data-page="schedules" title="Schedules & Triggers"><span class="ico">◫</span><em>Schedule</em></button></nav></div>
<div class="railgroup"><small>GOVERN</small><nav class="nav">
<button data-page="review" title="Review & Decisions"><span class="ico">◇</span><em>Review</em><span class="count">03</span></button>
<button data-page="incidents" title="Incidents & Recovery"><span class="ico">⚑</span><em>Incidents</em></button>
<button data-page="evidence" title="Evidence & Lineage"><span class="ico">⌗</span><em>Evidence</em></button>
<button data-page="release" title="Release Guard"><span class="ico">↗</span><em>Release</em></button>
<button data-page="policy" title="Governance & Access"><span class="ico">⛨</span><em>Policy</em></button></nav></div>
<div class="railgroup"><small>LEARN</small><nav class="nav">
<button data-page="insights" title="Insights & Analytics"><span class="ico">⌁</span><em>Insights</em></button>
<button data-page="settings" title="Workspace Settings"><span class="ico">⚙</span><em>Settings</em></button></nav></div>
</div>
<div class="railbottom"><span class="dot"></span><small>LOCAL<br>PROTECTED</small></div>
</aside>'''
s,n=re.subn(r'<aside id="sidebar">.*?</aside>',rail,s,count=1,flags=re.S)
assert n==1, 'sidebar replacement failed'
home='''<section class="page active" id="page-home">
<div class="welcome">
<div class="welcomeGlow"></div><div class="welcomeTop"><div><div class="eyebrow">NEXTDECODE / CREATIVE OPERATIONS</div><h1>Good evening. <span>What are we decoding today?</span></h1><p>Research an idea, build a story, direct production—or move the operating system forward.</p></div><div class="welcomeMark">ND<span>●</span></div></div>
<div class="promptbar"><span class="spark">✧</span><input id="creativePrompt" aria-label="Creative brief" placeholder="Describe what you want to create… e.g. a 50-second short on AI-native startups"><button id="promptGo">Start brief ↗</button></div>
<div class="quickActions"><button data-go="research"><i>⌕</i> Research a topic</button><button data-go="creator"><i>✧</i> Generate a script</button><button data-go="studio"><i>▣</i> Create a video</button><button data-go="review"><i>◇</i> Review work</button><button data-go="release"><i>⛨</i> Release controls</button></div>
<div class="welcomeFoot"><span><i class="dot"></i> LOCAL-FIRST WORKSPACE</span><span>HUMAN APPROVAL REQUIRED</span><span>PUBLIC PUBLISHING DISABLED</span></div>
</div>
<div class="homeSectionHead"><div><div class="eyebrow">YOUR OPERATING PICTURE</div><h2>Active workspace</h2><p>Real project structure, creative pipeline and engineering priorities.</p></div><button class="link" data-go="portfolio">Explore portfolio ↗</button></div>
<div class="homeGrid">
<div class="homeMain">
<div class="pipelinePanel panel"><div class="panelTitle"><h3>Content production pipeline</h3><small>SHORTS / 45–60 SEC</small></div><div class="pipeline">
<div class="stage"><div class="stageIcon">⌕</div><b>Research</b><small>Evidence & claims</small></div><div class="stage"><div class="stageIcon">T</div><b>Script</b><small>Natural English</small></div><div class="stage active"><div class="stageIcon">✧</div><b>Visual direction</b><small>Hybrid shots</small></div><div class="stage"><div class="stageIcon">♫</div><b>Assembly</b><small>Voice & edit</small></div><div class="stage"><div class="stageIcon">◇</div><b>Human review</b><small>Approval gate</small></div><div class="stage"><div class="stageIcon">↗</div><b>Publishing</b><small>Locked</small></div></div></div>
<div class="panel projectPanel"><div class="panelTitle"><h3>Core initiatives</h3><button class="link" data-go="portfolio">All projects ↗</button></div><div class="projectRows">
<div class="projectRow" data-go="portfolio"><span class="projectGlyph violet">⌘</span><div><b>Engineering Command Center</b><small>WP2 execution · WP3 worker identity · WP5 authorization</small></div><span class="pill amber">BUILDING</span></div>
<div class="projectRow" data-go="studio"><span class="projectGlyph cyan">✧</span><div><b>NEXTDECODE Content OS</b><small>Research → script → visuals → review → release</small></div><span class="pill green">ACTIVE</span></div>
<div class="projectRow" data-go="studio"><span class="projectGlyph pink">▣</span><div><b>Shorts Studio</b><small>Hybrid visuals · quality-first · human approval</small></div><span class="pill purple">ITERATING</span></div>
</div></div>
</div>
<div class="homeSide">
<div class="panel agentPulse"><div class="panelTitle"><h3>Agent workforce</h3><button class="link" data-go="agents">Open command ↗</button></div><div class="agentMini"><span class="agentOrb">R</span><div><b>Research Analyst</b><small>Sources · claim ledger</small></div><i>READY</i></div><div class="agentMini"><span class="agentOrb">W</span><div><b>Workflow Engineer</b><small>WP2 · durable execution</small></div><i class="busy">BUSY</i></div><div class="agentMini"><span class="agentOrb">Q</span><div><b>Quality Reviewer</b><small>Regression · acceptance</small></div><i>READY</i></div><div class="agentMini"><span class="agentOrb">S</span><div><b>Security Reviewer</b><small>Rights · release boundary</small></div><i>READY</i></div><div class="agentNote">Demo workforce · not canonical WP3 registrations</div></div>
<div class="panel criticalPanel"><div class="panelTitle"><h3>Engineering critical path</h3><button class="link" data-go="work">View queue ↗</button></div><div class="criticalLine"><b>01</b><div><strong>Durable workflow execution</strong><small>WP2 · persistence & recovery</small></div><span class="pill amber">AT RISK</span></div><div class="criticalLine"><b>02</b><div><strong>Worker registry & identity</strong><small>WP3 · stable identity contract</small></div><span class="pill purple">REVIEW</span></div><div class="criticalLine"><b>03</b><div><strong>Protected-action authorization</strong><small>WP5 · separate approval & authority</small></div><span class="pill">QUEUED</span></div></div>
</div></div>
<div class="homeBottom"><div><span class="eyebrow">TRUST POSTURE</span><b><i class="dot"></i> Local · Isolated · Protected</b><small>external_actions_allowed = false</small></div><div><span class="eyebrow">CURRENT RELEASE MODE</span><b>Human approval required</b><small>Approval is not publishing authorization.</small></div><div><span class="eyebrow">SYSTEM PRINCIPLES</span><b>Local-first · Free-first · No n8n</b><small>Canonical WP2–WP5 contracts remain authoritative.</small></div></div>
</section>'''
s,n=re.subn(r'<section class="page active" id="page-home">.*?</section>',home,s,count=1,flags=re.S)
assert n==1, 'home replacement failed'
# New, isolated design system: no global aside styling leaks into drawer; fixed viewport shell and independent content scrolling.
css='''
/* V3 visual system + layout hardening */
:root{--bg:#090b16;--panel:#111426;--panel2:#171a32;--line:#292d49;--violet:#a68bff;--cyan:#68ddeb;--pink:#ed9bd0;--text:#f5f2ff;--muted:#a1a4c1;--side:94px}
html{min-height:100%;scroll-behavior:auto}body{min-height:100vh;overflow-x:hidden;background:radial-gradient(ellipse at 78% 5%,#4a2c7950,transparent 34%),radial-gradient(ellipse at 35% 75%,#153c5540,transparent 42%),linear-gradient(135deg,#090b16,#0d1020 52%,#111027);background-attachment:fixed}
.shell{min-height:100vh;grid-template-columns:var(--side) minmax(0,1fr);align-items:start}
#sidebar.rail{position:sticky;top:0;height:100vh;min-height:620px;width:var(--side);padding:13px 9px 12px;background:linear-gradient(180deg,#0b0e1bf2,#0c1020f5);border-right:1px solid #343052;display:flex;flex-direction:column;overflow:hidden;z-index:12}
.rail .brand{display:flex;flex-direction:column;gap:5px;align-items:center;padding:5px 0 17px;margin-bottom:8px;border-bottom:1px solid #292d49}
.rail .orb{width:38px;height:38px;display:grid;place-items:center;color:white;font:800 16px Manrope;background:radial-gradient(circle at 35% 25%,#e7a7df,#9669ef 53%,#385e9b);box-shadow:0 0 28px #9b74f855}
.brandword{text-align:center}.brandword b{font:800 11px Manrope;letter-spacing:.14em}.brandword small{display:block;font:7px 'DM Mono';color:#9a91c6;margin-top:2px;letter-spacing:.08em}
.railnav{overflow-y:auto;overflow-x:hidden;scrollbar-width:thin;scrollbar-color:#353153 transparent;flex:1}.railgroup{margin:7px 0 12px}.railgroup>small{display:block;text-align:center;font:7px 'DM Mono';letter-spacing:.13em;color:#6e7191;margin:0 0 5px}
.rail .nav{gap:3px}.rail .nav button{position:relative;min-height:48px;padding:5px 2px;gap:3px;display:flex;flex-direction:column;justify-content:center;align-items:center;border:1px solid transparent;border-radius:10px;color:#9da3c0;font-size:8px}
.rail .nav button em{font-style:normal;font-size:8px;line-height:1.1;white-space:nowrap}.rail .nav button .ico{width:auto;font-size:17px;line-height:19px}.rail .nav button .count{position:absolute;top:2px;right:2px;margin:0;padding:2px 4px;font-size:7px}.rail .nav button:hover{background:#1c203a;color:white}.rail .nav button.active{background:linear-gradient(145deg,#30244d,#202541);border-color:#4d4074;box-shadow:inset 0 0 0 1px #9b7cf322;color:#fff}
.railbottom{border-top:1px solid #292d49;padding:10px 0 2px;display:flex;align-items:center;justify-content:center;gap:6px;color:#8e94b2;font:7px 'DM Mono';letter-spacing:.08em}
main{min-width:0;min-height:100vh}.top{height:58px;padding:0 24px;background:#0c1020d9;border-color:#292d49}.content{max-width:1700px;padding:24px 27px 42px;min-height:calc(100vh - 58px)}
.page{display:none;min-height:calc(100vh - 105px);animation:fadeIn .22s ease}.page.active{display:block}@keyframes fadeIn{from{opacity:.55}to{opacity:1}}
.drawer{position:fixed!important;top:0!important;right:0!important;bottom:0!important;height:100vh!important;min-height:0!important;width:min(450px,94vw)!important;display:block!important;overflow-y:auto!important;z-index:30!important}
.drawerShade{z-index:29!important}.head h1{font-size:30px}.panel{background:linear-gradient(145deg,#15182d,#101426);border-color:#2b2d4b}
.welcome{position:relative;overflow:hidden;padding:30px 31px 20px;border:1px solid #4a3e70;border-radius:22px;background:radial-gradient(ellipse at 80% 15%,#9a69d94d,transparent 32%),radial-gradient(ellipse at 70% 110%,#2c9bad2c,transparent 40%),linear-gradient(115deg,#17152d,#11182a 60%,#17152c);box-shadow:0 18px 65px #06071180,inset 0 1px #ffffff0b;margin-bottom:24px}
.welcome:before{content:'';position:absolute;width:420px;height:420px;border:1px solid #b79cff24;border-radius:50%;right:6%;top:-255px;box-shadow:0 0 0 32px #b79cff08,0 0 0 75px #b79cff06,0 0 90px #9a6cff25;pointer-events:none}
.welcomeGlow{position:absolute;width:180px;height:180px;border-radius:50%;right:19%;bottom:-145px;background:#7d5bff33;filter:blur(45px)}
.welcomeTop{position:relative;display:flex;justify-content:space-between;align-items:center;gap:20px}.welcome h1{font:800 clamp(25px,3vw,38px) Manrope;letter-spacing:-.055em;margin:5px 0 8px}.welcome h1 span{color:#c9b4ff}.welcomeTop p{font-size:12px;color:#b4b5d0;margin:0;line-height:1.6}.welcomeMark{font:800 54px Manrope;letter-spacing:-.12em;color:#e3d7ff20;padding:0 14px}.welcomeMark span{font-size:15px;color:#b79aff}
.promptbar{position:relative;display:flex;align-items:center;gap:12px;margin:25px 0 12px;padding:8px 9px 8px 16px;border:1px solid #64518b;border-radius:14px;background:#0b1020bb;box-shadow:0 8px 30px #07081580;max-width:920px}
.promptbar .spark{font-size:20px;color:#c6a8ff}.promptbar input{flex:1;min-width:0;background:transparent;border:0;outline:0;color:#f3efff;font:12px 'DM Sans';padding:8px 0}.promptbar input::placeholder{color:#8585a8}.promptbar button{border:0;border-radius:10px;background:linear-gradient(110deg,#9871e8,#5e91d9);color:white;padding:11px 17px;font-size:10px;font-weight:700}
.quickActions{display:flex;gap:8px;flex-wrap:wrap}.quickActions button{border:1px solid #454063;background:#ffffff08;color:#d2c9ee;border-radius:20px;padding:8px 13px;font-size:9px}.quickActions button:hover{background:#31274d;border-color:#9175d4}.quickActions i{font-style:normal;color:#c3a8ff;margin-right:6px}
.welcomeFoot{display:flex;gap:20px;flex-wrap:wrap;margin-top:22px;padding-top:13px;border-top:1px solid #ffffff14;color:#9899b8;font:8px 'DM Mono';letter-spacing:.1em}.welcomeFoot span{display:flex;align-items:center;gap:7px}.welcomeFoot .dot,.homeBottom .dot{width:6px;height:6px}
.homeSectionHead{display:flex;align-items:end;justify-content:space-between;margin:0 0 12px}.homeSectionHead h2{font:700 18px Manrope;margin:0}.homeSectionHead p{color:var(--muted);font-size:10px;margin:4px 0 0}
.homeGrid{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(300px,.8fr);gap:12px}.homeMain,.homeSide{display:grid;align-content:start;gap:12px}.pipelinePanel{padding:16px 18px}.pipelinePanel .pipeline{padding:13px 2px 6px}.pipelinePanel .stageIcon{width:40px;height:40px;border-radius:13px}.pipelinePanel .stage b{font-size:9px}.projectRows{display:grid}.projectRow{display:flex;align-items:center;gap:11px;padding:12px 0;border-top:1px solid #292d49;cursor:pointer}.projectRow:first-child{border-top:0;padding-top:0}.projectGlyph{width:34px;height:34px;flex:none;border-radius:11px;display:grid;place-items:center;font-size:16px;background:#25213d}.projectGlyph.violet{color:#c0a8ff}.projectGlyph.cyan{color:#73dce5;background:#17303a}.projectGlyph.pink{color:#efa7d6;background:#39233d}.projectRow div{min-width:0;flex:1}.projectRow b{font-size:10px}.projectRow small{display:block;color:var(--muted);font-size:9px;margin-top:4px;white-space:normal}.agentMini{display:flex;align-items:center;gap:9px;padding:8px 0;border-top:1px solid #292d49}.agentMini:first-of-type{border-top:0}.agentOrb{width:29px;height:29px;display:grid;place-items:center;border-radius:9px;background:#2c2548;color:#cbb6ff;font:700 10px Manrope}.agentMini div{flex:1}.agentMini b{font-size:9px}.agentMini small{display:block;color:var(--muted);font-size:8px;margin-top:3px}.agentMini i{font:8px 'DM Mono';font-style:normal;color:var(--green)}.agentMini i.busy{color:var(--amber)}.agentNote{border-top:1px solid #292d49;padding-top:9px;color:#777e9e;font-size:8px}
.criticalLine{display:flex;align-items:center;gap:8px;padding:10px 0;border-top:1px solid #292d49}.criticalLine:first-of-type{border-top:0}.criticalLine>b{font:10px 'DM Mono';color:#8b80b8}.criticalLine div{flex:1;min-width:0}.criticalLine strong{display:block;font-size:9px}.criticalLine small{display:block;color:var(--muted);font-size:8px;margin-top:3px}
.homeBottom{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:12px}.homeBottom>div{border:1px solid #292d49;border-radius:12px;padding:12px 14px;background:#12162a}.homeBottom .eyebrow{font-size:7px;margin-bottom:7px}.homeBottom b{display:flex;align-items:center;gap:7px;font-size:9px}.homeBottom small{display:block;color:var(--muted);font-size:8px;margin-top:5px}
.projectRow:hover{background:#ffffff05}
@media(max-width:1100px){.homeGrid{grid-template-columns:1fr}.homeSide{grid-template-columns:1fr 1fr}.metrics{grid-template-columns:repeat(3,1fr)}}
@media(max-width:700px){:root{--side:68px}.rail .brandword,.railgroup>small{display:none}.rail .brand{padding-bottom:10px}.rail .nav button{min-height:43px}.rail .nav button em{font-size:7px}.rail .nav button .ico{font-size:16px}.railgroup{margin:5px 0 9px}.top{padding:0 12px}.content{padding:15px 12px 30px}.welcome{padding:21px 16px 16px}.welcomeMark{display:none}.welcome h1{font-size:25px}.welcomeFoot{gap:9px;font-size:7px}.promptbar{margin-top:19px}.promptbar button{padding:10px}.homeSide{grid-template-columns:1fr}.homeBottom{grid-template-columns:1fr}.homeSectionHead{align-items:start}.pipeline{grid-template-columns:repeat(3,1fr);row-gap:15px}.pipeline .stage:nth-child(3):after{display:none}}
@media(max-height:760px){#sidebar.rail{overflow-y:auto}.railnav{overflow:visible}.railgroup{margin:4px 0 7px}.rail .nav button{min-height:41px}.railbottom{position:sticky;bottom:0;background:#0c1020}}
'''
s=s.replace('</style>',css+'\n</style>',1)
# JS: reliable routing, correct active nav state, close drawer and reset both document and main scroll immediately.
s=s.replace("function go(id){if(!names[id])return;pages.forEach(p=>p.classList.toggle('active',p.id==='page-'+id));document.querySelectorAll('[data-page]').forEach(b=>b.classList.toggle('active',b.dataset.page===id));document.getElementById('crumb').textContent=names[id];sidebar.classList.remove('open');history.replaceState(null,'','#/'+id);window.scrollTo({top:0,behavior:'smooth'})}",
"""function go(id){if(!names[id])return;pages.forEach(p=>p.classList.toggle('active',p.id==='page-'+id));document.querySelectorAll('#sidebar [data-page]').forEach(b=>b.classList.toggle('active',b.dataset.page===id));document.getElementById('crumb').textContent=names[id];sidebar.classList.remove('open');drawer.classList.remove('open');shade.classList.remove('open');history.replaceState(null,'','#/'+id);window.scrollTo(0,0);document.querySelector('main').scrollTop=0;document.querySelector('.content').scrollTop=0;}""")
# Clicks for project rows; brief submit takes the user's prompt into the research desk as a demo navigation, not an AI action.
s=s.replace("document.getElementById('search').onclick=()=>note('Search overlay is a planned next integration; no live index is connected.');",
"""document.getElementById('search').onclick=()=>note('Global search UI is planned; no live index is connected.');
document.querySelectorAll('.projectRow').forEach(el=>el.addEventListener('click',()=>go(el.dataset.go)));
document.getElementById('promptGo').onclick=()=>{const v=document.getElementById('creativePrompt').value.trim();if(!v){note('Add a short brief to get started.');return}note('Brief captured in this prototype — research workflow is not connected.');go('research')};
document.getElementById('creativePrompt').addEventListener('keydown',e=>{if(e.key==='Enter')document.getElementById('promptGo').click()});""")
out.write_text(s)
print('WROTE',out,'bytes',out.stat().st_size,'page_sections',len(re.findall(r'<section class="page',s)))
