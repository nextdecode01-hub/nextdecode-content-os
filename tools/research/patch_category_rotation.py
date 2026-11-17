from pathlib import Path
p=Path('/home/demon/shorts_studio/app/research/selector.py')
s=p.read_text()
old='def select_best(candidates: list, *, limit: int = 1, weights: dict | None = None,\n                min_score: int = DEFAULT_MIN_SCORE, past_performance: dict | None = None) -> dict:\n    """Pick the best topic. Anything below `min_score` is rejected with a reason."""\n'
new='''CATEGORY_ROTATION_HISTORY = 3
CATEGORY_ROTATION_SCORE_TOLERANCE = 5.0


def _choose_with_category_rotation(ranked: list[dict], recent_topics: list[str], *,
                                   history_size: int = CATEGORY_ROTATION_HISTORY,
                                   score_tolerance: float = CATEGORY_ROTATION_SCORE_TOLERANCE) -> tuple[dict | None, dict]:
    """Rotate recent categories only when a fresh category is nearly as strong.

    This is a selection tie-break: scores and dimension weights are never changed.
    """
    if not ranked:
        return None, {"applied": False, "reason": "no_ranked_candidates"}
    top = ranked[0]
    recent = [classify_topic(str(topic)) for topic in (recent_topics or [])[-max(1, history_size):]]
    top_category = str((top.get("niche_relevance") or {}).get("topic_category") or "general_curiosity")
    if not recent or top_category not in recent:
        return top, {"applied": False, "reason": "top_category_not_recently_repeated",
                     "history_categories": recent, "selected_category": top_category}
    floor = float(top.get("total_score") or 0) - max(0.0, float(score_tolerance))
    for entry in ranked[1:]:
        category = str((entry.get("niche_relevance") or {}).get("topic_category") or "general_curiosity")
        score = float(entry.get("total_score") or 0)
        if category not in recent and category != "general_curiosity" and score >= floor:
            return entry, {"applied": True, "reason": "fresh_category_within_quality_tolerance",
                           "history_categories": recent, "previous_top_category": top_category,
                           "selected_category": category,
                           "score_delta": round(float(top.get("total_score") or 0) - score, 1),
                           "score_tolerance": score_tolerance}
    return top, {"applied": False, "reason": "no_fresh_category_within_quality_tolerance",
                 "history_categories": recent, "selected_category": top_category,
                 "score_tolerance": score_tolerance}


def select_best(candidates: list, *, limit: int = 1, weights: dict | None = None,
                min_score: int = DEFAULT_MIN_SCORE, past_performance: dict | None = None) -> dict:
    """Pick the best quality topic; rotate categories only among close-score options."""
'''
if old not in s: raise SystemExit('select_best anchor not found')
s=s.replace(old,new,1)
old2='    selected = accepted[0] if accepted else None\n    method = (\n'
new2='''    selected, rotation = _choose_with_category_rotation(accepted, load_used_topics())
    if selected is not None and rotation.get("applied"):
        selected = dict(selected)
        selected["category_rotation"] = rotation
    method = (
'''
if old2 not in s: raise SystemExit('selection anchor not found')
s=s.replace(old2,new2,1)
old3='        "feedback_note": performance.get("reason", ""),\n        "errors": errors,\n'
new3='        "feedback_note": performance.get("reason", ""),\n        "category_rotation": rotation,\n        "errors": errors,\n'
if old3 not in s: raise SystemExit('return anchor not found')
s=s.replace(old3,new3,1)
p.write_text(s)
