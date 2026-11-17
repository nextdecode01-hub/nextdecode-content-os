from pathlib import Path
import re, shutil
root=Path(__file__).resolve().parent
p=root/'index.html'
s=p.read_text()
# Remove the legacy research/library sections so each route has exactly one workspace.
for pid in ('research','library'):
    pat=rf'<section class="page" id="page-{pid}">.*?</section>'
    s,n=re.subn(pat,'',s,count=1,flags=re.S)
    assert n==1,(pid,n)
# Repair the hash parser regex (the JS regex needs one escaped slash).
s=s.replace(r"location.hash.replace(/^#\\/?/,'')", r"location.hash.replace(/^#\/?/,'')")
# Mobile navigation trigger, preserving desktop horizontal sidebar.
s=s.replace('<div style="display:flex;align-items:center;gap:10px"><div class="crumb">', '<div style="display:flex;align-items:center;gap:10px"><button class="topbtn mobile" id="menu" aria-label="Open navigation">☰</button><div class="crumb">',1)
s=s.replace("sidebar.classList.remove('open');drawer.classList.remove('open')", "sidebar.classList.remove('open','mobile-open');drawer.classList.remove('open')",1)
s=s.replace("document.querySelectorAll('[data-page],[data-go]').forEach", "document.querySelectorAll('[data-page],[data-go]').forEach",1)
needle="document.querySelectorAll('[data-page],[data-go]').forEach(b=>b.addEventListener('click',()=>go(b.dataset.page||b.dataset.go)));"
s=s.replace(needle,needle+"\ndocument.getElementById('menu').onclick=()=>sidebar.classList.toggle('mobile-open');",1)
s=s.replace("if(e.key==='Escape'){document.getElementById('close').click();closeSearch()}", "if(e.key==='Escape'){document.getElementById('close').click();closeSearch();sidebar.classList.remove('mobile-open')}",1)
# Add mobile button display and avoid nested scrolling.
s=s.replace("button:focus-visible,input:focus-visible{outline:2px solid #bba7ff;outline-offset:2px}", ".mobile{display:none}.button:focus-visible,input:focus-visible{outline:2px solid #bba7ff;outline-offset:2px}",1)
s=s.replace("@media(max-width:620px){.shell{grid-template-columns:minmax(0,1fr)}", "@media(max-width:620px){.mobile{display:inline-flex}.shell{grid-template-columns:minmax(0,1fr)}",1)
p.write_text(s)
# Fix the build script too so rebuilding this existing prototype retains the same route parser.
bp=root/'build_final.py'
b=bp.read_text().replace(r"location.hash.replace(/^#\\\\/?/,'')", r"location.hash.replace(/^#\\/?/,'')")
bp.write_text(b)
print('PATCHED',p,'BYTES',p.stat().st_size)
