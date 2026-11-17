from pathlib import Path
import re
s=Path(__file__).with_name('index.html').read_text()
j=re.search(r'<script>(.*?)</script>',s,re.S).group(1)
Path('/tmp/nd-v3.js').write_text(j)
print('PAGES',len(re.findall(r'<section class="page',s)))
print('RAIL_NAV',len(re.findall(r'data-page="',s)))
print('HOME_PROMPT', 'creativePrompt' in s)
print('FIXED_DRAWER', '.drawer{position:fixed!important' in s)
