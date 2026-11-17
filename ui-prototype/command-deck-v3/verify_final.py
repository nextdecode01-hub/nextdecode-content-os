from pathlib import Path
import re, collections, json
p=Path(__file__).with_name('index.html');s=p.read_text()
ids=re.findall(r'<section class="page(?: active)?" id="page-([^"]+)"',s)
c=collections.Counter(ids); nav=re.findall(r'data-page="([^"]+)"',s); links=re.findall(r'data-go="([^"]+)"',s)
m=re.search(r'const names=(\{.*?\});',s,re.S); names=json.loads(m.group(1)) if m else {}
print('PAGE_SECTIONS',len(ids),'UNIQUE',len(c),'DUPLICATES',{k:v for k,v in c.items() if v>1})
print('NAV_ITEMS',len(nav),'UNIQUE',len(set(nav)),'MISSING_PAGES',sorted(set(nav)-set(ids)))
print('ROUTE_NAMES',len(names),'MISSING_ROUTE_NAMES',sorted((set(nav)|set(links))-set(names)))
print('BROKEN_DATA_GO',sorted(set(links)-set(names)))
print('KEY_FORMATS',all(x in s for x in ['Short-form video','Long-form video','Social & carousels','X & threads','Blog & articles','Newsletter','Podcast & audio','Campaign packages']))
print('EDITORIAL_SERIES',all(x in s for x in ['AI You Can Use','Hype Check','What Changed','How It Works','Startup Breakdown']))
js=re.search(r'<script>(.*?)</script>',s,re.S).group(1);Path('/tmp/nd-final.js').write_text(js)
print('HTML_BYTES',len(s.encode()),'JS_BYTES',len(js.encode()))
