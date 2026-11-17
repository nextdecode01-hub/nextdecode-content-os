"""Reusable deterministic vector components for technology-explainer scenes.

All components return editable SVG source. No network, browser or new package
dependency is required; scene JSON remains the source of truth.
"""
from __future__ import annotations
import html, math, re
from typing import Any

def _s(value: Any, limit: int = 180) -> str:
    return html.escape(re.sub(r"\\s+", " ", str(value or ""))[:limit], quote=True)

def _num(value: Any, default: float = 0.0) -> float:
    try:
        number=float(value)
        return number if math.isfinite(number) else default
    except (TypeError,ValueError):
        return default

def _svg(body: str, width: int=1080, height: int=1920, background: str="#080E18") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<rect width="{width}" height="{height}" fill="{_s(background,24)}"/>{body}</svg>')

def render_metric_cards(spec: dict[str,Any]) -> str:
    cards=spec.get("cards",[])[:4]
    body=[f'<text x="72" y="170" fill="#F3F6FC" font-size="58" font-weight="700">{_s(spec.get("title","Key metrics"))}</text>']
    for i,item in enumerate(cards):
        x=72+(i%2)*486; y=280+(i//2)*360
        body += [f'<rect x="{x}" y="{y}" width="440" height="300" rx="28" fill="#142235" stroke="#2D4058" stroke-width="2"/>',
          f'<text x="{x+32}" y="{y+82}" fill="#9FB2C9" font-size="28">{_s(item.get("label","Metric"))}</text>',
          f'<text x="{x+32}" y="{y+190}" fill="#56D6C8" font-size="66" font-weight="700">{_s(item.get("value","—"),32)}</text>',
          f'<text x="{x+32}" y="{y+245}" fill="#C3CEDD" font-size="22">{_s(item.get("note",""),80)}</text>']
    return _svg("".join(body))

def render_bar_chart(spec: dict[str,Any]) -> str:
    data=spec.get("data",[])[:8]
    maxv=max([_num(x.get("value")) for x in data]+[1.0])
    body=[f'<text x="72" y="170" fill="#F3F6FC" font-size="54" font-weight="700">{_s(spec.get("title","Comparison"))}</text>']
    for i,item in enumerate(data):
        y=300+i*170; value=max(0,_num(item.get("value")))
        bar=max(4, min(700, 700*value/maxv))
        body += [f'<text x="80" y="{y}" fill="#D8E2F0" font-size="27">{_s(item.get("label",""),48)}</text>',
          f'<rect x="80" y="{y+28}" width="700" height="48" rx="12" fill="#1D2A3B"/>',
          f'<rect x="80" y="{y+28}" width="{bar:.1f}" height="48" rx="12" fill="#56D6C8"/>',
          f'<text x="820" y="{y+65}" fill="#FFFFFF" font-size="28">{_s(item.get("display",value),24)}</text>']
    return _svg("".join(body))

def render_flow_diagram(spec: dict[str,Any]) -> str:
    nodes=spec.get("nodes",[])[:6]
    body=[f'<text x="72" y="170" fill="#F3F6FC" font-size="54" font-weight="700">{_s(spec.get("title","How it works"))}</text>']
    for i,node in enumerate(nodes):
        y=270+i*235
        body += [f'<rect x="120" y="{y}" width="840" height="142" rx="24" fill="#142235" stroke="#56D6C8" stroke-width="3"/>',
          f'<text x="164" y="{y+58}" fill="#56D6C8" font-size="24" font-weight="700">{i+1:02d}</text>',
          f'<text x="230" y="{y+62}" fill="#FFFFFF" font-size="34" font-weight="600">{_s(node.get("title","Step"),64)}</text>',
          f'<text x="230" y="{y+106}" fill="#AAB9CC" font-size="22">{_s(node.get("detail",""),100)}</text>']
        if i<len(nodes)-1:
            body.append(f'<path d="M540 {y+144} v78" stroke="#56D6C8" stroke-width="5" stroke-linecap="round"/>')
            body.append(f'<path d="M526 {y+208} l14 16 14 -16" fill="none" stroke="#56D6C8" stroke-width="5"/>')
    return _svg("".join(body))

def render_icon_tile(spec: dict[str,Any]) -> str:
    """Simple icon tile from safe primitives; no remote icon font or SVG injection."""
    kind=str(spec.get("symbol","spark")).lower()
    paths={
      "spark":'<path d="M540 550 L585 670 L705 715 L585 760 L540 880 L495 760 L375 715 L495 670 Z"/>',
      "brain":'<path d="M430 500 C320 430 260 580 340 650 C260 750 370 850 450 790 C500 900 620 850 620 770 C740 800 800 660 700 600 C740 470 590 420 540 510 C500 450 450 450 430 500 Z"/>',
      "shield":'<path d="M540 450 L720 520 V670 C720 790 630 880 540 920 C450 880 360 790 360 670 V520 Z"/>',
      "chip":'<rect x="420" y="560" width="240" height="240" rx="24"/><rect x="470" y="610" width="140" height="140" rx="12" fill="#080E18"/>'
    }
    shape=paths.get(kind,paths["spark"])
    body=f'<text x="540" y="300" text-anchor="middle" fill="#F3F6FC" font-size="54" font-weight="700">{_s(spec.get("title","Concept"))}</text><g fill="none" stroke="#56D6C8" stroke-width="24" stroke-linejoin="round">{shape}</g><text x="540" y="1100" text-anchor="middle" fill="#AAB9CC" font-size="30">{_s(spec.get("caption",""),90)}</text>'
    return _svg(body)

def render_component(spec: dict[str,Any]) -> str:
    kind=str(spec.get("kind","")).lower()
    renderers={"metric_cards":render_metric_cards,"bar_chart":render_bar_chart,
               "flow_diagram":render_flow_diagram,"icon_tile":render_icon_tile}
    if kind not in renderers:
        raise ValueError(f"unsupported production component: {kind}")
    return renderers[kind](spec)
