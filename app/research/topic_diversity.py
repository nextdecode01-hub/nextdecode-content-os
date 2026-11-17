"""Broad editorial taxonomy and repeat-avoidance for NEXTDECODE topics."""
from __future__ import annotations
import re
from difflib import SequenceMatcher
from typing import Iterable

TOPIC_CATEGORIES = {
 "science_discovery": ("science","scientist","discovery","experiment","physics","chemistry","biology","research","laboratory","study","medical","medicine","genetics"),
 "world_geopolitics": ("country","government","president","minister","war","conflict","election","diplomacy","border","sanction","parliament","policy","geography","canal","strait","shipping route","territory","river","island","panama canal"),
 "business_economy": ("company","business","market","economy","bank","stock","revenue","profit","startup","founder","industry","trade","billion"),
 "history_mystery": ("history","historical","ancient","century","archaeology","mystery","forgotten","empire","artifact"),
 "nature_environment": ("wildlife","animal","species","forest","rainforest","rainfall","ocean","climate","environment","earthquake","volcano","pollution","ecosystem"),
 "space_astronomy": ("nasa","space","planet","moon","mars","asteroid","telescope","galaxy","astronomy","rocket","satellite"),
 "human_stories": ("person","people","survivor","rescue","human","community","athlete","inventor","explorer","achievement"),
 "consumer_society": ("consumer","product","brand","shopping","food","fashion","social media","internet culture","habit","advertising"),
 "culture_entertainment": ("film","movie","music","artist","art","actor","celebrity","gaming","game","book","culture"),
 "technology_ai": ("ai","artificial intelligence","machine learning","robot","robotics","chip","semiconductor","quantum","computer","software","open source","cyber","data center","model","llm","neural","battery","electric vehicle","autonomous"),
 "investigations": ("investigation","lawsuit","court","fraud","scam","exposed","whistleblower","allegation","audit","corruption"),
 "sports_competition": ("sport","football","cricket","basketball","tennis","olympic","championship","record","league","tournament"),
}
STOPWORDS = {"the","and","for","with","from","that","this","into","about","after","before","when","what","why","how","who","has","have","had","was","were","are","its","their","they","will","could","would","should","over","under","new","says","said"}

def normalize_topic(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()

def topic_terms(value: str) -> set[str]:
    return {x for x in normalize_topic(value).split() if len(x)>2 and x not in STOPWORDS}

def classify_topic(title: str, summary: str = "") -> str:
    """Classify with token boundaries so short markers (notably 'ai') do not
    match inside unrelated words such as 'rainforest' or 'mountain'."""
    text = normalize_topic(f"{title} {summary}")
    scored = []
    for category, markers in TOPIC_CATEGORIES.items():
        score = 0
        for marker in markers:
            normalized_marker = normalize_topic(marker)
            if not normalized_marker:
                continue
            pattern = r"(?<![a-z0-9])" + re.escape(normalized_marker).replace(r"\ ", r"\s+") + r"(?![a-z0-9])"
            if re.search(pattern, text):
                score += 2 if " " in normalized_marker else 1
        if score:
            scored.append((score, category))
    return max(scored)[1] if scored else "general_curiosity"

def similarity(left: str, right: str) -> float:
    a,b=normalize_topic(left),normalize_topic(right)
    if not a or not b: return 0.0
    ta,tb=topic_terms(a),topic_terms(b)
    jaccard=len(ta & tb)/max(1,len(ta | tb))
    return max(SequenceMatcher(None,a,b).ratio(),jaccard)

def annotate_and_diversify(candidates: Iterable[dict], recent_topics: Iterable[str]=(), *,
                           limit: int=12, similarity_threshold: float=.68) -> list[dict]:
    recent=[str(x) for x in recent_topics if str(x).strip()]
    recent_categories=[classify_topic(x) for x in recent[-1:]]
    prepared=[]
    for raw in candidates:
        if not isinstance(raw,dict): continue
        item=dict(raw); title=str(item.get("title") or "").strip()
        if not title: continue
        category=classify_topic(title,str(item.get("summary") or ""))
        max_sim=max((similarity(title,old) for old in recent),default=0.0)
        if max_sim >= similarity_threshold: continue
        item["topic_category"]=category
        item["topic_similarity"]={"recent_max":round(max_sim,3),"category_repeat":category in recent_categories}
        prepared.append(item)
    prepared.sort(key=lambda x:(bool(x["topic_similarity"]["category_repeat"]),-float(x.get("rank") or 0),str(x.get("published") or "")))
    selected=[]; seen=set()
    for item in prepared:
        if item["topic_category"] in seen: continue
        selected.append(item); seen.add(item["topic_category"])
        if len(selected)>=limit: return selected
    for item in prepared:
        if item not in selected: selected.append(item)
        if len(selected)>=limit: break
    return selected
