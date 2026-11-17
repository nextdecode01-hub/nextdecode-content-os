"""Structured, editable screen/window graphics for NEXTDECODE scenes.

JSON-friendly scene specs produce editable SVG, rendered by the existing FFmpeg
image pipeline. Components do not require external screenshot or video APIs.
"""
from __future__ import annotations
import html, json, re
from pathlib import Path
from typing import Any

def _esc(value: Any, limit: int=240) -> str:
    return html.escape(re.sub(r"\\s+"," ",str(value or ""))[:limit],quote=True)

def _lines(values: Any, limit: int=8) -> list[str]:
    return [str(x)[:120] for x in values[:limit]] if isinstance(values,list) else []

def render_screen_component(spec: dict[str,Any], output_path: str|Path|None=None) -> str:
    """Render browser, terminal, code editor, dashboard or generic app-window SVG."""
    kind=str(spec.get("kind","browser")).lower()
    if kind not in {"browser","terminal","code","dashboard","app"}: raise ValueError(f"unsupported screen component kind: {kind}")
    title=_esc(spec.get("title","NEXTDECODE")); subtitle=_esc(spec.get("subtitle",""))
    accent=_esc(spec.get("accent","#56D6C8"),20); lines=_lines(spec.get("lines"))
    body=[]
    if kind=="browser":
        url=_esc(spec.get("url","https://nextdecode.ai"))
        body += [f'<rect x="52" y="150" width="796" height="1250" rx="28" fill="#101827"/>',
                 f'<text x="90" y="205" fill="#AAB7C8" font-size="24">{url}</text>',
                 f'<text x="90" y="330" fill="#FFFFFF" font-size="46" font-weight="700">{title}</text>',
                 f'<text x="90" y="385" fill="#AAB7C8" font-size="24">{subtitle}</text>']
        for i,line in enumerate(lines):
            y=500+i*92; body += [f'<rect x="90" y="{y-38}" width="720" height="66" rx="12" fill="#1B293B"/>',
                f'<text x="118" y="{y+5}" fill="#E6EDF7" font-size="25">{_esc(line)}</text>']
    elif kind=="terminal":
        body += ['<rect x="52" y="150" width="796" height="1250" rx="24" fill="#07110F" stroke="#31564C" stroke-width="3"/>',
                 f'<text x="90" y="220" fill="{accent}" font-size="28">{title}</text>']
        for i,line in enumerate(lines): body.append(f'<text x="90" y="{310+i*76}" fill="#B9F6D3" font-family="monospace" font-size="23">$ {_esc(line)}</text>')
    elif kind=="code":
        body += ['<rect x="52" y="150" width="796" height="1250" rx="24" fill="#111827" stroke="#34445B" stroke-width="3"/>',
                 f'<text x="90" y="220" fill="#D7E2F2" font-size="27">{title}</text>']
        for i,line in enumerate(lines):
            y=310+i*72; body += [f'<text x="95" y="{y}" fill="#64748B" font-family="monospace" font-size="20">{i+1:02d}</text>',
                f'<text x="155" y="{y}" fill="#A5E6D7" font-family="monospace" font-size="21">{_esc(line)}</text>']
    else:
        body += ['<rect x="52" y="150" width="796" height="1250" rx="24" fill="#101827" stroke="#34445B" stroke-width="3"/>',
                 f'<text x="90" y="225" fill="#FFFFFF" font-size="36" font-weight="700">{title}</text>',
                 f'<text x="90" y="275" fill="#AAB7C8" font-size="22">{subtitle}</text>']
        cards=lines[:4] or ["Signal","Analysis","Output"]
        for i,line in enumerate(cards):
            x=90+(i%2)*360; y=360+(i//2)*260
            body += [f'<rect x="{x}" y="{y}" width="320" height="210" rx="18" fill="#1B293B"/>',
                f'<text x="{x+24}" y="{y+70}" fill="{accent}" font-size="25">{_esc(line)}</text>',
                f'<path d="M{x+24} {y+150} h240" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>']
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="1500" viewBox="0 0 900 1500">'
         '<rect width="900" height="1500" fill="#070B12"/><rect x="30" y="30" width="840" height="1440" rx="38" fill="#0C1420" stroke="#26364B" stroke-width="3"/>'
         '<circle cx="72" cy="88" r="10" fill="#F87171"/><circle cx="108" cy="88" r="10" fill="#FBBF24"/><circle cx="144" cy="88" r="10" fill="#34D399"/>'
         + "".join(body) + '</svg>')
    if output_path:
        p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(svg,encoding="utf-8")
    return svg

def render_screen_spec_file(spec_path: str|Path, output_path: str|Path) -> str:
    return render_screen_component(json.loads(Path(spec_path).read_text(encoding="utf-8")),output_path)
