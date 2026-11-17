"""Deterministic creator-grade creative direction for Shorts."""
from __future__ import annotations
import re

STORY_FORMATS = {
 "explainer":{"arc":["hook","context","mechanism","example","implication","payoff"],"pace":"brisk"},
 "mini_documentary":{"arc":["cold_open","context","evidence","turning_point","consequence","reflection"],"pace":"measured"},
 "mystery_reveal":{"arc":["question","clue","clue","misdirection_check","reveal","payoff"],"pace":"build"},
 "myth_bust":{"arc":["common_belief","challenge","evidence","explanation","correction"],"pace":"brisk"},
 "case_study":{"arc":["outcome","starting_point","decision","execution","result","lesson"],"pace":"measured"},
 "problem_solution":{"arc":["pain","stakes","failed_approach","solution","proof","payoff"],"pace":"brisk"},
 "timeline":{"arc":["setup","milestone","milestone","turning_point","today","future"],"pace":"driving"},
 "listicle":{"arc":["promise","item","item","item","ranking","payoff"],"pace":"driving"},
 "cinematic_essay":{"arc":["provocation","observation","tension","insight","reflection"],"pace":"measured"}}
VISUAL_STYLES = {
 "cinematic":{"lighting":"motivated contrast, practical highlights","composition":"layered depth, intentional negative space"},
 "documentary":{"lighting":"naturalistic available light","composition":"observational, candid, grounded"},
 "newsroom":{"lighting":"clean neutral key light","composition":"direct, information-first, restrained"},
 "tech_editorial":{"lighting":"cool controlled highlights","composition":"precise geometry, clean negative space"},
 "minimal_motion":{"lighting":"graphic contrast","composition":"simple hierarchy, one focal point"}}
CAMERA=[("wide","eye_level","locked_off"),("medium","low_angle","slow_push_in"),("close_up","eye_level","subtle_handheld"),("extreme_close_up","top_down","rack_focus_simulated"),("over_the_shoulder","eye_level","slow_drift"),("insert","top_down","locked_off"),("medium_wide","low_angle","lateral_dolly"),("close_up","high_angle","slow_pull_back")]
TRANSITIONS=["cut","cut","match_cut","cut","dissolve","cut","whip_pan","cut"]
EDITING={"brisk":"motivated_fast_cuts","measured":"breathing_room","build":"accelerate_toward_reveal","driving":"rhythmic_progression"}
def select_story_format(topic: str, beats: list) -> str:
 text = (str(topic) + " " + " ".join(str((b or {}).get("text") or (b or {}).get("claim") or "") if isinstance(b,dict) else str(b) for b in beats)).lower()
 if any(x in text for x in ("myth","misconception","actually true","common belief","debunk")): return "myth_bust"
 if any(x in text for x in ("case study","how company","startup","founder","company built","product launch")): return "case_study"
 if any(x in text for x in ("timeline","history of","in 20","in 19","founded","launched in","evolution of")): return "timeline"
 if any(x in text for x in ("versus","vs.","compared","top 5","top five","three ways","five ways","reasons why")): return "listicle"
 if any(x in text for x in ("experiment","researchers","scientists","study finds","investigation","inside the")): return "mini_documentary"
 if any(x in text for x in ("problem","challenge","failure","failed","solution","fixes")): return "problem_solution"
 if "?" in text or text.startswith(("why ","how ","what happens")): return "mystery_reveal"
 return "explainer"

def select_visual_style(topic: str, story_format: str) -> str:
 text = str(topic).lower()
 if any(x in text for x in ("breaking","election","policy","regulation","government","news")): return "newsroom"
 if any(x in text for x in ("research","scientist","experiment","history","founder","people")): return "documentary"
 if any(x in text for x in ("ai","artificial intelligence","technology","software","chip","robot","startup")): return "tech_editorial"
 return "cinematic"

def _semantic_query(text: str, topic: str) -> str:
    value = str(text or "").lower()
    if any(x in value for x in ("unpublished paper", "research paper", "authors", "peer review")):
        return "scientists reviewing AI research paper manuscript"
    if any(x in value for x in ("agent", "open-ended research", "research question")):
        return "AI research agents scientist laboratory"
    if any(x in value for x in ("hypothesis", "experiment", "scientist")):
        return "scientist laboratory research experiment"
    if any(x in value for x in ("engineering", "software", "code", "system")):
        return "software engineer developing AI system"
    if any(x in value for x in ("data", "analysis", "evidence", "results")):
        return "research data analysis computer screens"
    if any(x in value for x in ("8085", "microprocessor", "computer architecture")):
        return "8085 microprocessor circuit board computer"
    generic = {
        "the","and","that","this","with","from","when","what","which","their","they",
        "about","into","then","because","just","only","each","part","parts","does",
        "can","how","why","not","for","are","was","were","has","have","its","use",
        "used","more","than","very","clear","useful","role","order","matters",
        "gotten","cheap","easy","almost","anything","short","video","explained",
        "conduct","open","ended","worth","closer","look","specific","detail",
    }
    words = [w for w in re.findall(r"[a-z0-9]+", value) if w not in generic]
    topic_words = [w for w in re.findall(r"[a-z0-9]+", str(topic).lower()) if w not in generic]
    combined = list(dict.fromkeys((topic_words + words)))
    return " ".join(combined[:5]) or "technology research laboratory"

def _semantic_variants(text: str, topic: str, label: str, primary: str) -> list[str]:
    value = str(text or "").lower()
    topic_terms = " ".join(re.findall(r"[a-z0-9]+", str(topic).lower())[:3])
    if any(x in value for x in ("protomaps", "pmtiles", "map tiles", "vector tiles", "map server")) or any(x in str(topic).lower() for x in ("protomaps", "pmtiles", "map tiles", "vector tiles")):
        options = [primary, "Protomaps PMTiles vector map tiles",
                   "map tile server CDN infrastructure", "open source vector map tiles"]
    elif any(x in value for x in ("unpublished paper", "research paper", "authors", "peer review", "manuscript")):
        options = [primary, "scientists reviewing AI research paper manuscript",
                   "researchers annotating scientific manuscript", "unpublished AI paper peer review"]
    elif any(x in value for x in ("agent", "open-ended research", "research question")):
        options = [primary, "AI agent evaluation workstation",
                   "scientific research team AI lab", "AI agents hypothesis generation"]
    elif any(x in value for x in ("experiment", "evaluation", "test", "benchmark")):
        options = [primary, "AI research experiment workstation",
                   "scientists evaluating model results", "research benchmark data analysis"]
    elif any(x in value for x in ("evidence", "source", "claim", "result")):
        options = [primary, "research evidence source documents",
                   "scientific paper results close up", "researcher highlighting study findings"]
    else:
        options = [primary, f"{topic_terms} scientist research".strip(),
                   f"{topic_terms} technology workflow".strip()]
    return list(dict.fromkeys(item for item in options if item and len(item.split()) <= 7))

def _visual_family(text: str, label: str) -> str:
    value = str(text or "").lower()
    if any(x in value for x in ("protomaps", "pmtiles", "map tiles", "vector tiles", "map server", "cdn")):
        if label in {"mechanism", "solution", "execution", "how_it_works"}:
            return "diagram"
        if label in {"evidence", "proof"} and re.search(r"\d|\$", value):
            return "chart"
        if label in {"implication", "payoff", "takeaway"}:
            return "typography"
        return "real_footage"
    if any(x in value for x in ("workflow", "steps", "process", "how it works", "system connects", "agent pipeline")):
        return "diagram"
    if any(x in value for x in ("evidence", "source", "claim", "quote", "paper says", "authors report")):
        return "typography"
    if any(x in value for x in ("score", "percentage", "compared", "ranking", "benchmark result", "results show")):
        return "chart"
    if label in {"mechanism", "solution", "execution"}:
        return "diagram"
    if label in {"evidence", "proof", "correction"}:
        return "typography"
    return "real_footage"

def _visual_direction(text: str, topic: str, label: str) -> tuple[str, str]:
    value = str(text or "").lower()
    topic_value = str(topic or "").lower()
    if any(x in value + " " + topic_value for x in ("protomaps", "pmtiles", "map tiles", "vector tiles", "map server")):
        return "vector map tiles and CDN infrastructure", "map tile layers loading from a self-hosted CDN server"
    if any(x in value for x in ("unpublished paper", "research paper", "authors", "peer review")):
        return "AI research paper manuscript", "scientists reviewing and annotating a research manuscript"
    if any(x in value for x in ("agent", "open-ended research", "research question")):
        return "AI research agents", "research agents analyzing an open-ended scientific question"
    if any(x in value for x in ("experiment", "evaluation", "test", "benchmark")):
        return "AI research experiment", "researchers evaluating model results on a workstation"
    if any(x in value for x in ("evidence", "source", "claim", "result")):
        return "research evidence", "researcher highlighting source notes and comparing findings"
    if any(x in value for x in ("8085", "microprocessor", "computer architecture")) or "8085" in topic.lower():
        return "8085 microprocessor", "close-up of a microprocessor board and circuit traces"
    defaults = {
        "hook": ("research laboratory", "scientist studying a complex research question"),
        "context": ("research team", "researchers collaborating around a paper"),
        "mechanism": ("AI system workflow", "animated system diagram showing connected stages"),
        "evidence": ("research evidence", "close-up of source documents and highlighted findings"),
        "payoff": ("research scientist", "scientist reflecting on evaluated results"),
    }
    return defaults.get(label, ("technology research", "researcher examining a technical workflow"))

def direct_shots(beats:list,*,topic:str,story_format:str="auto",visual_style:str="auto")->list[dict]:
 story_format = select_story_format(topic, beats) if story_format in {"", "auto"} else story_format
 visual_style = select_visual_style(topic, story_format) if visual_style in {"", "auto"} else visual_style
 story_format=story_format if story_format in STORY_FORMATS else "explainer"
 visual_style=visual_style if visual_style in VISUAL_STYLES else "cinematic"
 spec,direction=STORY_FORMATS[story_format],VISUAL_STYLES[visual_style]
 out=[]
 for i,item in enumerate(beats):
  beat=dict(item) if isinstance(item,dict) else {"text":str(item)}
  label=str(beat.get("label") or beat.get("beat_label") or "").lower().replace("-","_")
  label={"intro":"hook","opening":"hook","close":"payoff","conclusion":"payoff","body":"mechanism"}.get(label,label) or spec["arc"][min(i,len(spec["arc"])-1)]
  size,angle,move=CAMERA[i%len(CAMERA)]
  if label in {"hook","cold_open","question","provocation","pain","outcome"}: size,angle,move="close_up","low_angle","slow_push_in"
  elif label in {"evidence","example","proof","item","milestone"}: size,angle,move="insert","top_down","locked_off"
  elif label in {"payoff","reflection","lesson","future"}: size,angle,move="wide","eye_level","slow_pull_back"
  text=str(beat.get("text") or beat.get("caption") or beat.get("claim") or "")
  subject=str(beat.get("visual_subject") or beat.get("visual") or text)
  action=str(beat.get("visual_action") or beat.get("action") or "")
  semantic_subject=_semantic_query(subject + " " + text, topic)
  visual_subject, visual_action = _visual_direction(subject + " " + text, topic, label)
  camera_phrase=f"{size.replace('_',' ')} {angle.replace('_',' ')} camera"
  variants = _semantic_variants(subject + " " + text, topic, label, semantic_subject)
  base=semantic_subject
  beat.update({"label":label,"story_format":story_format,"visual_style":visual_style,"visual_family":beat.get("visual_family") or _visual_family(subject + " " + text, label),"visual_subject":beat.get("visual_subject") or visual_subject,"visual_action":beat.get("visual_action") or visual_action,"shot_size":size,"camera_angle":angle,"camera_movement":move,"camera_instruction":camera_phrase,"lighting_direction":direction["lighting"],"composition_direction":direction["composition"],"editing_rhythm":EDITING[spec["pace"]],"transition_intent":TRANSITIONS[i%len(TRANSITIONS)],"asset_query":base or subject,"asset_query_variants":variants,"continuity_group":str(beat.get("continuity_group") or f"{story_format}:{label}"),"editorial_reason":str(beat.get("editorial_reason") or f"{label}: {story_format} story progression")})
  out.append(beat)
 return out
