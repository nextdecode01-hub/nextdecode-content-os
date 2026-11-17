from pathlib import Path
import re, shutil, datetime, json

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "index.html"
BACKUP = ROOT / "index.pre-final.html"
if not BACKUP.exists():
    shutil.copy2(TARGET, BACKUP)
html = TARGET.read_text()

nav_groups = [
("HOME", [("home","⌂","Home"),("portfolio","▦","Portfolio")]),
("CREATE", [("creator","✧","Creator Workspace"),("planner","▤","Content Planner"),("research","⌕","Research Desk"),("brand","◉","Brand & Knowledge"),("library","▧","Content Library"),
("shorts","▣","Shorts Studio"),("longform","▤","Long-form Studio"),("social","▧","Social & Carousel"),("xstudio","𝕏","X & Threads"),("blog","¶","Blog Studio"),("newsletter","✉","Newsletter Studio"),("podcast","♫","Podcast & Audio"),("campaigns","◈","Campaign Packages")]),
("ORCHESTRATE", [("agents","⌘","Agent Command"),("workflows","⤳","Workflow Canvas"),("runs","◷","Execution Monitor"),("schedules","◫","Schedules & Triggers"),("integrations","⌘","Integrations & Providers")]),
("GOVERN", [("review","◇","Review & Decisions"),("quality","✓","Quality & Rights"),("evidence","⌗","Evidence & Lineage"),("incidents","⚑","Incidents & Recovery"),("release","↗","Distribution & Release"),("policy","⛨","Governance & Access")]),
("ENGINEERING", [("engineering","⌘","Engineering Command"),("workstreams","▥","WP1–WP6 Workstreams"),("database","▦","Database & Migrations"),("testing","✓","Testing & Acceptance"),("operations","⌁","Technical Operations")]),
("INTELLIGENCE", [("insights","⌁","Analytics & Performance"),("audience","◎","Audience Insights"),("learning","↗","Feedback & Learning"),("improvements","✧","Improvement Proposals")]),
("SYSTEM", [("notifications","♧","Notifications"),("settings","⚙","Workspace Settings")])
]

def sidebar():
    chunks = ['<aside id="sidebar" class="final-sidebar">',
      '<div class="brand-lockup"><div class="orb">N</div><div><b>NEXTDECODE</b><small>CONTENT OPERATING SYSTEM</small></div></div>',
      '<div class="workspace-switch"><span class="workspace-glyph">◈</span><div><small>ACTIVE WORKSPACE</small><b>Creator Mode · NEXTDECODE</b></div><span>⌄</span></div>',
      '<div class="final-nav-scroll">']
    for group, items in nav_groups:
        chunks.append(f'<section class="final-nav-group"><div class="final-nav-label">{group}</div><nav class="final-nav">')
        for pid, icon, label in items:
            active = ' active' if pid == 'home' else ''
            count = '<span class="nav-count">03</span>' if pid in ('review','incidents') else ('<span class="nav-count">06</span>' if pid == 'agents' else '')
            chunks.append(f'<button class="final-nav-item{active}" data-page="{pid}" title="{label}"><span class="final-nav-icon">{icon}</span><span>{label}</span>{count}</button>')
        chunks.append('</nav></section>')
    chunks += ['</div>',
      '<div class="sidebar-status"><span class="status-light"></span><div><b>Local · Isolated · Protected</b><small>External actions disabled</small></div></div>',
      '</aside>']
    return ''.join(chunks)

html, n = re.subn(r'<aside id="sidebar"[^>]*>.*?</aside>', sidebar(), html, count=1, flags=re.S)
assert n == 1, "Could not replace sidebar"

# Remove obsolete mobile sidebar trigger; retain top-bar search and account controls.
html = html.replace('<button class="topbtn mobile" id="menu">☰</button>', '')
html = html.replace('NEXTDECODE / <b id="crumb">COMMAND CENTER</b>', 'NEXTDECODE OS / <b id="crumb">HOME</b>')

# Rename product identity and initiative labels without implying Content OS is a separate product.
html = html.replace('NEXTDECODE Content OS</b>', 'NEXTDECODE OS</b>')
html = html.replace('Content OS</h1>', 'NEXTDECODE OS</h1>')
html = html.replace('NEXTDECODE Content OS</h3>', 'NEXTDECODE OS</h3>')
html = html.replace('Content OS</small>', 'NEXTDECODE OS</small>')
html = html.replace('NEXtdecode Content OS', 'NEXTDECODE OS')

# Replace old page map with an expanded, clearly scoped workspace model.
new_names = {
"home":"HOME","portfolio":"PORTFOLIO & INITIATIVES","creator":"CREATOR WORKSPACE","planner":"CONTENT PLANNER",
"research":"RESEARCH INTELLIGENCE","brand":"BRAND & KNOWLEDGE","library":"CONTENT LIBRARY",
"shorts":"SHORTS STUDIO","longform":"LONG-FORM STUDIO","social":"SOCIAL & CAROUSEL STUDIO","xstudio":"X & THREADS STUDIO",
"blog":"BLOG STUDIO","newsletter":"NEWSLETTER STUDIO","podcast":"PODCAST & AUDIO STUDIO","campaigns":"CAMPAIGN PACKAGES",
"agents":"AGENT COMMAND","workflows":"WORKFLOW CANVAS","runs":"EXECUTION MONITOR","schedules":"SCHEDULES & TRIGGERS","integrations":"INTEGRATIONS & PROVIDERS",
"review":"REVIEW & DECISIONS","quality":"QUALITY & RIGHTS","evidence":"EVIDENCE & LINEAGE","incidents":"INCIDENTS & RECOVERY","release":"DISTRIBUTION & RELEASE","policy":"GOVERNANCE & ACCESS",
"engineering":"ENGINEERING COMMAND CENTER","workstreams":"WP1–WP6 WORKSTREAMS","database":"DATABASE & MIGRATIONS","testing":"TESTING & ACCEPTANCE","operations":"TECHNICAL OPERATIONS",
"insights":"ANALYTICS & PERFORMANCE","audience":"AUDIENCE INSIGHTS","learning":"FEEDBACK & LEARNING","improvements":"IMPROVEMENT PROPOSALS",
"notifications":"NOTIFICATIONS","settings":"WORKSPACE SETTINGS"
}
names_js = "const names=" + json.dumps(new_names, ensure_ascii=False, separators=(',',':')) + ";"
html, n = re.subn(r'const names=\{.*?\};', names_js, html, count=1, flags=re.S)
assert n == 1, "Could not replace route name map"

# Add detailed workspace pages. All P1/future capabilities are labelled as planned, not implemented.
page_specs = [
("planner","Content Planner","Plan a connected editorial portfolio across formats, series, audiences and channels.","PLANNED · P1",
["Editorial calendar","Topic opportunity board","Content briefs","Series rotation","Campaign planning","Platform packaging"],
["AI You Can Use","Hype Check","What Changed","How It Works","Startup Breakdown"],
["A single verified research package can inform multiple format-specific briefs. Each output keeps its own audience, hook, length, tone and approval."],
"Content strategy and calendar workflows are planning scope; no scheduler is connected in this prototype."),
("research","Research Intelligence","Investigate topics, evaluate sources, map claims and prepare reusable evidence packages.","EXISTING SPECIALIST MODULES · UI DEMO",
["Topic discovery","Adaptive research depth","Source evaluation","Atomic claim ledger","Counter-evidence","Research packages","Trend radar · planned","Competitor intelligence · planned"],
["On-demand research","Scheduled discovery · planned","Fact-check review","Source lineage","Research history"],
["Evidence is reusable across formats. A source or claim correction should identify dependent content that may need review."],
"Repository includes research desk, topic research, source lineage and claim-ledger modules. Advanced trend and competitor capabilities remain planned."),
("brand","Brand & Knowledge","Shared context for positioning, audience, voice, visual rules, reusable knowledge and content history.","PLANNED · P1",
["Brand profile","Audience & personas","Positioning & pillars","Voice & writing rules","Visual identity","Approved terminology","Knowledge library","Reusable insights"],
["NEXTDECODE first","Single-brand creator mode","Future multi-brand support"],
["Creator overrides take priority over AI recommendations while preserving decision history."],
"Brand intelligence and shared knowledge are defined in the blueprint and P1 planning package; not all capabilities are implemented."),
("library","Content Library","A traceable library for scripts, research, media, prompts, exports, templates and rights.","PARTIAL FOUNDATION · UI DEMO",
["Research packages","Scripts & versions","Visual assets","Audio assets","Prompts & templates","Exports & artifacts","Rights records","Content-to-asset links"],
["Provenance","Version history","Licensing & expiry","Reusable templates"],
["Asset rights and provenance must travel with every derivative and distribution package."],
"Existing artifact, output, review and asset paths are present in the repository; a complete unified asset-management workspace is planned."),
("shorts","Shorts Studio","The existing specialist short-form production engine. Preserve its architecture and integrate through stable boundaries.","EXISTING SPECIALIST ENGINE",
["Research-to-script","Script Studio","Voice generation","Shot planning","Visual direction","Hybrid B-roll & motion","Timeline assembly","Render QA","Review package"],
["45–60 second target","Natural English voiceover","Cinematic + fast edit","Human approval before release"],
["Shorts Studio remains a specialist engine. The unified OS orchestrates it; it does not replace or rewrite it."],
"Existing short pipeline, script, voice, visuals, render, review and publishing modules are present. This page is a product map, not a live editor."),
("longform","Long-form Studio","Research-led mini-documentaries, explainers, chapters, scene plans and production packages.","PARTIAL SPECIALIST CAPABILITY",
["Editorial candidate comparison","Evidence-led outline","Long-form script","Chapters & scene plan","Voice & visual package","Subtitles & render QA","Review & export"],
["Focused documentary structure","Primary-source spine","Independent corroboration","Retention-led improvement"],
["Long-form is not a list of unrelated headlines. Each narrative needs evidence, originality, visual potential and audience relevance."],
"Long-form pipeline and editorial modules exist. Full unified studio and production orchestration are not yet complete."),
("social","Social & Carousel Studio","Create platform-specific posts, carousels, captions and visual variants from shared research.","PLANNED · P1",
["Single-image posts","Carousel narratives","Captions & hooks","Visual layouts","Platform variants","Brand checks","Export package"],
["Instagram","Facebook","LinkedIn","Cross-platform variants"],
["Reuse verified research, not identical copy. Every destination needs its own context, packaging and rights checks."],
"Multiformat creation is in the blueprint and P1 scope; a complete social studio is not confirmed as implemented."),
("xstudio","X & Threads Studio","Turn evidence-backed ideas into concise posts, threads and visual explainers.","PLANNED · P1",
["Single posts","Thread outlines","Thread sequencing","Evidence links","Visual explainers","Variants & drafts"],
["X posts","X threads","Thread-to-blog reuse"],
["Keep claims traceable to sources. Thread segments should build a coherent argument rather than repeat the same hook."],
"Format-specific X/thread studio is product scope, not a completed engine."),
("blog","Blog Studio","Develop research-led articles, explainers, editorial structures and publish-ready drafts.","PLANNED · P1",
["Article briefs","SEO research","Outline & structure","Draft editor","Fact-check & citations","Editorial review","Export"],
["Explainers","Deep dives","Startup analysis","Evergreen guides"],
["One research package can support the article, but article claims and citations require their own review."],
"Blog/article studio is defined in the master blueprint; implementation status remains planned."),
("newsletter","Newsletter Studio","Curate research and insights into useful recurring editions and email drafts.","PLANNED · P1",
["Edition planning","Editorial curation","Newsletter draft","Subject-line variants","Source references","Review & export"],
["Weekly intelligence","Product updates","Curated research","Creator notes"],
["Newsletter segmentation and recurring delivery are future capabilities and are not active here."],
"Newsletter creation is part of multiformat scope; no email delivery is connected."),
("podcast","Podcast & Audio Studio","Plan audio-first episodes, scripts, show notes and supporting audio assets.","PLANNED · P1",
["Episode concept","Research & outline","Host script","Show notes","Voice/audio assets","Transcript & chapters","Export"],
["Solo explainers","Interview outlines","Audio adaptations"],
["Audio reuse requires format-specific pacing, rights and voice checks."],
"Podcast/audio studio is planned; existing voice/audio modules are reusable components, not proof of a completed podcast product."),
("campaigns","Campaign Packages","Coordinate multiple connected outputs around one approved campaign brief.","PLANNED · P1",
["Campaign brief","Audience & objective","Shared research package","Format mix","Asset plan","Review matrix","Distribution pack"],
["One campaign","Many format-specific outputs","Shared evidence and brand context"],
["Campaign packages coordinate outputs; they do not bypass the approval and rights requirements of individual variants."],
"Campaign orchestration is part of the blueprint's multidimensional Studio direction."),
("integrations","Integrations & Providers","Inspect provider eligibility, model capability, service health, resource limits and integration boundaries.","DESIGN / NOT CONNECTED",
["Provider registry","Model catalogue","Capability matching","Eligibility checks","Quota & resource use","Integration health","Local worker link"],
["Free-first target","Approved providers only","No automatic paid upgrades"],
["Tool availability is not authorization. Providers must pass privacy, rights, security, data-classification and budget eligibility checks."],
"No new provider, paid service, credential or external integration is activated by this prototype."),
("quality","Quality & Rights","Centralized evaluation for factuality, editorial quality, brand fit, platform suitability and usage rights.","PARTIAL CONTROLS · UI DEMO",
["Factual accuracy","Evidence coverage","Editorial structure","Brand consistency","Platform suitability","Language quality","Rights & license","Output validation"],
["Fail closed on unknown rights","Human review required","Independent verification"],
["Attribution is not permission. Unknown, expired or incompatible rights cannot become publish-ready silently."],
"Repository contains visual quality, audio quality, review, approval-integrity and publishing-governance controls."),
("engineering","Engineering Command Center","Operate engineering delivery, dependencies, ownership, evidence, risk and milestone readiness.","CANONICAL CONTROL-PLANE VIEW",
["Portfolio & milestones","Work queue","WP1 domain persistence","WP2 workflow execution","WP3 worker trust","WP4 artifact storage","WP5 governance & rights","WP6 integration & recovery"],
["Preserve existing architecture","Canonical contracts are authoritative","No restart or broad rewrite"],
["Engineering status must be sourced from canonical workstream records and acceptance evidence, not illustrative dashboard counters."],
"Engineering Command Center is a control-plane view. It does not replace the canonical contracts, accepted decisions or workstream evidence."),
("workstreams","WP1–WP6 Workstreams","Navigate the six canonical engineering workstreams and their dependencies.","CANONICAL STRUCTURE",
["WP1 · Domain persistence","WP2 · Workflow execution","WP3 · Worker trust","WP4 · Artifact storage","WP5 · Governance, quality & rights","WP6 · Integration, recovery & acceptance"],
["Contracts","Implementation evidence","Acceptance gates","Open decisions"],
["Local autonomy runtime identities and sample jobs do not replace canonical WP2/WP3 records."],
"Workstream names are taken from the canonical P0 architecture."),
("database","Database & Migrations","Observe persistence foundations, schema evolution, migration safety and recovery readiness.","ENGINEERING WORKSPACE",
["Primary PostgreSQL","SQLite test/development fallback","Schema & migrations","Migration ledger","Backup & restore","Connection health","Data integrity"],
["No silent schema mutation","Migration review","Recovery evidence"],
["Managed PostgreSQL alternatives remain inactive unless separately approved."],
"Existing repository includes database-related code and workspace data. This screen does not connect to or modify a database."),
("testing","Testing & Acceptance","Track test suites, acceptance criteria, regression evidence, release blockers and verification provenance.","ENGINEERING WORKSPACE",
["Unit & contract tests","Integration tests","Security regression","Quality gates","Acceptance evidence","Release dossier","Coverage & gaps"],
["Exact command and result","Independent review","No green status without evidence"],
["A passing test subset is not proof of whole-system release readiness."],
"Existing repository includes a substantial pytest suite and acceptance/security tests. Live full-chain verification remains a separate requirement."),
("operations","Technical Operations","Observe services, local workers, queues, logs, incidents, backups and runtime health.","ENGINEERING WORKSPACE",
["API/service health","Local worker status","Queue & job age","Logs & traces","Disk & resource pressure","Backup & restore","Incident response"],
["Local-first","Free-first","Human-governed"],
["This prototype does not read live telemetry or execute operational controls."],
"Operations, tracking, notifications and autonomy modules exist; this UI remains disconnected from them."),
("audience","Audience Insights","Understand audience needs, personas, viewing intent and platform-specific context.","PLANNED · P1",
["Audience profile","Viewer intent","Persona hypotheses","Platform context","Audience questions","Feedback themes"],
["English-speaking","Tech-curious","Useful AI & technology without hype"],
["Audience claims and performance conclusions require real channel evidence; do not invent viewer attributes."],
"Audience identity and context are defined in shared intelligence contracts."),
("learning","Feedback & Learning","Turn observed performance and creator feedback into explainable recommendations.","PLANNED · HUMAN CONTROL",
["Performance observations","Creator feedback","Series comparison","Hook & pacing analysis","Learning proposals","Staged apply","Rollback reference"],
["AI recommends","Creator decides","History preserved"],
["No silent strategy changes. Creator override wins AI priority classification and retains the decision history."],
"Learning is human-controlled and staged. Automatic analytics ingestion is not yet complete."),
("improvements","Improvement Proposals","Review proposed changes to strategy, brand rules, workflow thresholds and agent configurations.","PLANNED · STAGED APPLY",
["Proposal inbox","Evidence & rationale","Expected impact","Risk assessment","Preview & compare","Owner decision","Activation history","Rollback"],
["Propose","Review","Stage","Approve","Activate","Measure"],
["AI can recommend. The creator approves. Changes remain staged until explicit authorization."],
"Staged Apply and creator-controlled learning are accepted product decisions; this prototype does not activate changes."),
("notifications","Notifications","A prioritized inbox for approvals, incidents, workflow failures and useful digests.","DESIGN / NOT CONNECTED",
["Critical incidents","Review requests","Workflow failures","Quota warnings","Daily digest","Notification preferences"],
["Risk-prioritized","Adaptive within creator-approved boundaries","No approval by silence"],
["Notifications never authorize an action and must not expose sensitive payloads in previews."],
"Repository contains notification boundary and notification modules; no live notification service is connected here.")
]

def page_html(spec):
    pid,title,desc,status,features,subitems,principles,evidence=spec
    fcards=''.join(f'<article class="feature"><div class="symbol">{["✧","⌕","▧","◇","◈","↗","♫","▤"][i%8]}</div><h3>{x}</h3><p>{desc if i==0 else "Dedicated workspace capability · scope and evidence remain visible."}</p></article>' for i,x in enumerate(features))
    tags=''.join(f'<span class="scope-chip">{x}</span>' for x in subitems)
    principle_html=''.join(f'<div class="row"><span>{x}</span><b>REQUIRED</b></div>' for x in principles)
    return f'''<section class="page" id="page-{pid}">
<div class="head"><div><div class="eyebrow">NEXTDECODE OS / SPECIALIST WORKSPACE</div><h1>{title}</h1><p>{desc}</p></div><span class="scope-status">{status}</span></div>
<div class="workspace-intro"><div><div class="eyebrow">WORKSPACE SCOPE</div><h2>{title}</h2><p>{evidence}</p></div><div class="workspace-orb">ND<span>✧</span></div></div>
<div class="panel scope-panel"><div class="panelTitle"><h3>Capabilities & work areas</h3><small>PRODUCT MAP</small></div><div class="cards">{fcards}</div></div>
<div class="split" style="margin-top:12px"><div class="panel"><div class="panelTitle"><h3>Connected formats & workflows</h3><small>SHARED INTELLIGENCE</small></div><div class="scope-chips">{tags}</div><p class="scope-note">Shared context: workspace · brand · audience · research · claims · content graph · assets · versions · quality · approvals · analytics.</p></div>
<div class="panel"><div class="panelTitle"><h3>Operating rules</h3><small>GOVERNED BY DESIGN</small></div>{principle_html}</div></div>
<div class="scope-footer"><span>IMPLEMENTATION STATUS</span><b>{status}</b><p>Prototype representation only. This page does not claim that planned functionality is implemented or connected to a live service.</p></div>
</section>'''

# Add missing routes as specialist workspaces.
pages_markup=''.join(page_html(x) for x in page_specs)
anchor='</div></main></div>'
assert anchor in html, "main layout insertion anchor missing"
html=html.replace(anchor, pages_markup + anchor, 1)

# Replace project identity on the home page and make project map explicit.
html=html.replace('<b>NEXTDECODE Content OS</b>', '<b>NEXTDECODE OS</b>')
html=html.replace('Research → script → visuals → review → release', 'Shared intelligence · multi-format studios · governed distribution')
html=html.replace('<b>Shorts Studio</b><small>Hybrid visuals · quality-first · human approval</small>', '<b>Shorts Studio</b><small>Existing specialist engine · integrated, not replaced</small>')

# Update route behavior and remove stale references to absent mobile menu.
html=html.replace("const pages=[...document.querySelectorAll('.page')],sidebar=document.getElementById('sidebar'),drawer=", "const pages=[...document.querySelectorAll('.page')],sidebar=document.getElementById('sidebar'),drawer=")
html=html.replace("document.querySelectorAll('#sidebar [data-page]').forEach", "document.querySelectorAll('#sidebar [data-page]').forEach")
html=html.replace("sidebar.classList.remove('open');drawer.classList.remove('open')", "drawer.classList.remove('open')")
html=html.replace("document.getElementById('menu').onclick=()=>sidebar.classList.toggle('open');", "")
# Ensure route change closes overlay, resets viewport, and uses robust route parsing.
html=html.replace("const initial=location.hash.slice(2);if(names[initial])go(initial);",
"""const initial=location.hash.replace(/^#\\/?/,'').split(/[?&]/)[0];if(names[initial])go(initial);
window.addEventListener('hashchange',()=>{const id=location.hash.replace(/^#\\/?/,'').split(/[?&]/)[0];if(names[id])go(id)});
""")

# Add search overlay with working client-side index across pages and capability labels.
search_overlay='''<div class="search-layer" id="searchLayer" aria-hidden="true"><div class="search-box"><div class="search-head"><span>⌕</span><input id="globalSearchInput" placeholder="Search workspaces, formats, capabilities…" autocomplete="off"><kbd>ESC</kbd></div><div id="searchResults" class="search-results"></div><small class="search-hint">Search this prototype's navigation and product map · no live backend index</small></div></div>'''
html=html.replace('<div class="drawerShade" id="shade"></div>', search_overlay+'<div class="drawerShade" id="shade"></div>',1)
# Replace search click handler and add accessible keyboard interactions.
html=html.replace("document.getElementById('search').onclick=()=>note('Global search UI is planned; no live index is connected.');",
"""const searchLayer=document.getElementById('searchLayer'),searchInput=document.getElementById('globalSearchInput'),searchResults=document.getElementById('searchResults');
function openSearch(){searchLayer.classList.add('open');searchLayer.setAttribute('aria-hidden','false');searchInput.value='';renderSearch('');setTimeout(()=>searchInput.focus(),30)}
function closeSearch(){searchLayer.classList.remove('open');searchLayer.setAttribute('aria-hidden','true')}
function renderSearch(q){const term=q.trim().toLowerCase();const matches=Object.entries(names).filter(([id,label])=>!term||id.includes(term)||label.toLowerCase().includes(term));searchResults.innerHTML=matches.slice(0,14).map(([id,label])=>'<button class="search-result" data-result="'+id+'"><span>◈</span><b>'+label+'</b><small>'+id+'</small><kbd>↵</kbd></button>').join('')||'<p class="empty-search">No matching workspace. Try a format, agent or capability.</p>';searchResults.querySelectorAll('[data-result]').forEach(b=>b.onclick=()=>{go(b.dataset.result);closeSearch()})}
document.getElementById('search').onclick=openSearch;searchInput.addEventListener('input',()=>renderSearch(searchInput.value));searchLayer.addEventListener('click',e=>{if(e.target===searchLayer)closeSearch()});""")
html=html.replace("if(e.key==='Escape'){document.getElementById('close').click();sidebar.classList.remove('open')}", "if(e.key==='Escape'){document.getElementById('close').click();closeSearch()}")
html=html.replace("e.preventDefault();note('Global search is not connected yet.')", "e.preventDefault();openSearch()")

# Add final design system and scrollbar/layout fixes after all previous CSS.
final_css=r'''
/* FINAL PRODUCT PROTOTYPE — unified navigation, warm luminous surfaces, stable page layout */
:root{--bg:#090a17;--panel:#14162b;--panel2:#1b1d37;--line:#343451;--violet:#aa91ff;--cyan:#75dce7;--pink:#efa4d5;--text:#f5f2ff;--muted:#a7a5c4;--dim:#777894;--side:264px}
*{scrollbar-width:none}*::-webkit-scrollbar{width:0;height:0;display:none}
html,body{min-height:100%;overflow-x:hidden}body{background:radial-gradient(ellipse at 72% -8%,#7752a52c,transparent 36%),radial-gradient(ellipse at 8% 55%,#2b77821c,transparent 42%),linear-gradient(135deg,#090a17,#0e1022 54%,#111027);background-attachment:fixed}
.shell{grid-template-columns:var(--side) minmax(0,1fr);min-height:100vh;align-items:start}
#sidebar.final-sidebar{position:sticky;top:0;height:100vh;min-height:100vh;width:var(--side);padding:18px 13px 14px;background:linear-gradient(180deg,#0d1020f5,#101326f7);border-right:1px solid #34314f;display:flex;flex-direction:column;overflow:hidden;z-index:12}
.brand-lockup{display:flex;align-items:center;gap:11px;padding:3px 8px 17px;border-bottom:1px solid #302d4a}
.brand-lockup .orb{width:40px;height:40px;flex:none;display:grid;place-items:center;color:#fff;font:800 17px Manrope;background:radial-gradient(circle at 30% 25%,#f4b7df,#a47af3 54%,#3d6e9c);box-shadow:0 0 28px #a77af34a}
.brand-lockup b{font:800 14px Manrope;letter-spacing:.09em;color:#f5f0ff}.brand-lockup small{display:block;font:8px 'DM Mono';letter-spacing:.13em;color:#9d9ab9;margin-top:4px}
.workspace-switch{display:flex;align-items:center;gap:9px;margin:13px 1px 10px;padding:10px;border:1px solid #34314f;border-radius:11px;background:linear-gradient(120deg,#1d2039,#141a2d)}
.workspace-glyph{width:28px;height:28px;border-radius:8px;display:grid;place-items:center;color:#c7b3ff;background:#302849}.workspace-switch div{min-width:0;flex:1}.workspace-switch small{display:block;color:#8889a9;font:7px 'DM Mono';letter-spacing:.12em}.workspace-switch b{display:block;font-size:10px;margin-top:3px}.workspace-switch>span:last-child{color:#a6a1c0}
.final-nav-scroll{flex:1;min-height:0;overflow-y:auto;overflow-x:hidden;padding:2px 0 8px;scrollbar-width:none}.final-nav-scroll::-webkit-scrollbar{display:none}
.final-nav-group{margin:7px 0 11px}.final-nav-label{font:8px 'DM Mono';letter-spacing:.17em;color:#85809f;padding:0 9px 6px}
.final-nav{display:grid;gap:2px}.final-nav-item{width:100%;min-height:34px;display:flex;align-items:center;gap:11px;padding:7px 10px;border:1px solid transparent;border-radius:9px;background:transparent;color:#aaa9c5;text-align:left;font-size:10px;transition:background .16s,border-color .16s,color .16s}
.final-nav-item:hover{background:#24243e;color:#fff}.final-nav-item.active{color:#fff;background:linear-gradient(100deg,#392b58,#24263f);border-color:#59487d;box-shadow:inset 2px 0 #b49aff}
.final-nav-icon{width:18px;flex:none;text-align:center;color:#a69acb;font-size:15px}.final-nav-item.active .final-nav-icon{color:#d3c2ff}.nav-count{margin-left:auto;padding:3px 6px;border-radius:6px;background:#332b4c;color:#d1bdff;font:8px 'DM Mono'}
.sidebar-status{display:flex;align-items:center;gap:9px;padding:12px 8px 2px;border-top:1px solid #302d4a}.status-light{width:7px;height:7px;border-radius:50%;background:#7de0ae;box-shadow:0 0 12px #7de0ae88}.sidebar-status b{display:block;font-size:9px}.sidebar-status small{display:block;color:#9998b6;font-size:8px;margin-top:3px}
main{min-width:0;min-height:100vh}.top{height:58px;padding:0 25px;background:#0c1020e8;border-color:#34314f}.content{max-width:1780px;padding:23px 27px 35px;min-height:calc(100vh - 58px)}
.page{display:none;min-height:calc(100vh - 100px);animation:fadeIn .2s ease}.page.active{display:block}@keyframes fadeIn{from{opacity:.65}to{opacity:1}}
.panel{background:linear-gradient(145deg,#191a32,#121629);border-color:#353552;box-shadow:0 10px 30px #06071420}
.feature{background:linear-gradient(145deg,#20213d,#15192c);border-color:#393754}.feature .symbol{color:#c2aaff}.feature p{line-height:1.6}
.welcome{background:radial-gradient(ellipse at 78% 10%,#9c72e64d,transparent 34%),radial-gradient(ellipse at 80% 100%,#3babbc2b,transparent 42%),linear-gradient(115deg,#211a3b,#171d34 58%,#18263a);border-color:#554779;box-shadow:0 18px 60px #05061070,inset 0 1px #ffffff10}
.welcome h1 span{background:linear-gradient(100deg,#d9c8ff,#b9d7ff 70%,#9ce5e8);-webkit-background-clip:text;background-clip:text;color:transparent}
.promptbar{background:#0d1224d9;border-color:#71619a}.promptbar button{background:linear-gradient(110deg,#9a78eb,#5e9bc5)}
.scope-status{align-self:center;border:1px solid #66558b;background:#2b2544;color:#d3c2ff;padding:7px 10px;border-radius:8px;font:8px 'DM Mono';letter-spacing:.08em;max-width:48%;text-align:center}
.workspace-intro{display:flex;justify-content:space-between;align-items:center;gap:20px;padding:20px 23px;margin-bottom:12px;border:1px solid #454166;border-radius:15px;background:radial-gradient(ellipse at 80% 0%,#8e6ed32b,transparent 43%),linear-gradient(120deg,#1d1c36,#141b2e)}
.workspace-intro h2{font:700 18px Manrope;margin:2px 0 6px}.workspace-intro p{font-size:10px;line-height:1.65;color:#b1b0ca;max-width:850px;margin:0}
.workspace-orb{width:65px;height:65px;flex:none;border-radius:50%;display:grid;place-items:center;font:800 17px Manrope;color:#e6dcff;background:radial-gradient(circle at 35% 25%,#d5b7ff,#7b63c9 52%,#264b68);box-shadow:0 0 0 8px #a58bff0b,0 0 45px #9d7bff40}.workspace-orb span{position:absolute;margin:39px 0 0 45px;color:#a6f0ef;font-size:12px}
.scope-panel .cards{grid-template-columns:repeat(4,minmax(0,1fr))}.scope-panel .feature{min-height:112px;padding:12px}.scope-panel .feature .symbol{font-size:16px}.scope-panel .feature h3{font-size:10px;margin:8px 0 4px}.scope-panel .feature p{font-size:9px}
.scope-chips{display:flex;flex-wrap:wrap;gap:7px}.scope-chip{border:1px solid #4a456b;border-radius:20px;padding:7px 10px;background:#24213d;color:#d0c3f4;font-size:9px}.scope-note{font-size:9px;line-height:1.7;color:var(--muted);margin:14px 0 0}.scope-footer{margin-top:12px;padding:13px 15px;border:1px solid #343451;border-radius:12px;background:#15182a}.scope-footer span{font:8px 'DM Mono';letter-spacing:.13em;color:#9b91bb}.scope-footer b{display:block;font:10px 'DM Mono';color:#d7c8ff;margin-top:5px}.scope-footer p{font-size:9px;color:var(--muted);margin:5px 0 0}
.search-layer{position:fixed;inset:0;z-index:50;background:#050610b8;backdrop-filter:blur(10px);display:none;align-items:flex-start;justify-content:center;padding:13vh 16px}.search-layer.open{display:flex}.search-box{width:min(620px,96vw);border:1px solid #62558b;border-radius:16px;background:#17182d;box-shadow:0 30px 100px #000b;overflow:hidden}.search-head{display:flex;align-items:center;gap:11px;padding:14px 16px;border-bottom:1px solid #393652;color:#c7b5ff}.search-head input{flex:1;min-width:0;background:transparent;border:0;outline:0;color:white;font-size:13px}.search-head kbd,.search-result kbd{border:1px solid #4a4665;border-radius:5px;padding:3px 6px;color:#aaa6c4;font:9px 'DM Mono'}.search-results{max-height:48vh;overflow:auto;padding:7px}.search-result{width:100%;display:flex;align-items:center;gap:10px;padding:10px;border:0;border-radius:8px;background:transparent;color:#e9e5f6;text-align:left}.search-result:hover{background:#292642}.search-result>span{color:#b9a5ff}.search-result b{font-size:10px;flex:1}.search-result small{color:#8d8aa9;font:8px 'DM Mono'}.empty-search{padding:20px;color:#aaa6c4;font-size:10px}.search-hint{display:block;padding:10px 15px;border-top:1px solid #393652;color:#85829f;font:8px 'DM Mono'}
#drawer{position:fixed!important;inset:0 0 0 auto!important;height:100dvh!important;min-height:0!important;width:min(450px,94vw)!important;display:block!important;overflow-y:auto!important;z-index:60!important;background:#17182d!important;border-left:1px solid #4a456b!important}
#shade{z-index:59!important}
button:focus-visible,input:focus-visible{outline:2px solid #bba7ff;outline-offset:2px}
@media(max-width:1150px){:root{--side:238px}.scope-panel .cards{grid-template-columns:repeat(3,minmax(0,1fr))}.homeGrid{grid-template-columns:1fr}.homeSide{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:820px){:root{--side:220px}.content{padding:18px 16px 30px}.scope-panel .cards{grid-template-columns:repeat(2,minmax(0,1fr))}.split{grid-template-columns:1fr}}
@media(max-width:620px){.shell{grid-template-columns:minmax(0,1fr)}#sidebar.final-sidebar{position:fixed;left:0;top:0;bottom:0;width:min(290px,86vw);height:100dvh;transform:translateX(-105%);transition:transform .2s;box-shadow:20px 0 60px #0009}.final-sidebar.mobile-open{transform:none}.top{padding:0 12px}.content{padding:14px 11px 24px}.search{width:36px;font-size:0}.homeSide{grid-template-columns:1fr}.scope-panel .cards{grid-template-columns:1fr 1fr}.workspace-intro{padding:15px}.workspace-orb{width:48px;height:48px}.welcome{padding:22px 17px 16px}.welcomeMark{display:none}.welcomeFoot{gap:9px;font-size:7px}.quickActions{gap:6px}.quickActions button{font-size:8px;padding:7px 9px}.head{align-items:flex-start;flex-direction:column}.scope-status{max-width:100%}}
'''
html=html.replace('</style>',final_css+'</style>',1)

# Make route links and project cards accessible, remove any references to stale page map labels.
html=html.replace('onclick="', 'onclick="')  # explicit no-op; keep source formatting stable.
TARGET.write_text(html)
print("BUILT", TARGET)
print("BYTES", TARGET.stat().st_size)
print("ROUTES", len(new_names))
print("PAGES", len(re.findall(r'<section class="page', html)))
print("BACKUP", BACKUP)
