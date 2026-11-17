from pathlib import Path
import re
p=Path(__file__).with_name('index.html')
s=p.read_text()
js=re.search(r'<script>(.*?)</script>', s, re.S).group(1)
Path('/tmp/nd-v2.js').write_text(js)
print('HTML_BYTES', len(s.encode()))
print('PAGE_SECTIONS', len(re.findall(r'<section class="page', s)))
print('NAV_ITEMS', len(re.findall(r'data-page="', s)))
print('AGENT_COMMAND', 'Agent Command' in s)
print('ALL_WORKSPACES', all(x in s for x in ['Creator Workspace','Production Studio','Content & Asset Library','Research Desk','Workflow Canvas','Run Observatory','Schedules & Triggers','Review & Decisions','Incidents & Recovery','Evidence & Lineage','Release Guard','Governance & Access','Insights & Analytics']))
