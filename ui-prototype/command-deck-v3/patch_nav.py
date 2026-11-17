from pathlib import Path
p=Path(__file__).with_name('index.html');s=p.read_text()
needle='<button class="final-nav-item" data-page="creator" title="Creator Workspace"><span class="final-nav-icon">✧</span><span>Creator Workspace</span></button>'
assert needle in s
s=s.replace(needle,needle+'<button class="final-nav-item" data-page="contentgraph" title="Content Graph"><span class="final-nav-icon">⌘</span><span>Content Graph</span></button>',1)
p.write_text(s)
print('NAV LINK ADDED')
