from pathlib import Path
import re,json
p=Path(__file__).with_name('index.html');s=p.read_text()
needle='<button class="final-nav-item" data-page="engineering" title="Engineering Command"><span class="final-nav-icon">⌘</span><span>Engineering Command</span></button>'
assert needle in s
s=s.replace(needle,needle+'<button class="final-nav-item" data-page="work" title="Execution Queue"><span class="final-nav-icon">☷</span><span>Execution Queue</span></button>',1)
m=re.search(r'const names=(\{.*?\});',s,re.S); d=json.loads(m.group(1)); d['work']='EXECUTION QUEUE'
s=s[:m.start()]+'const names='+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';'+s[m.end():]
p.write_text(s)
print('EXECUTION QUEUE NAV ADDED')
