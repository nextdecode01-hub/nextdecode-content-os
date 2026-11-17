#!/usr/bin/env python3
"""Standard-library analysis for NEXTDECODE's public video benchmark."""
import argparse, csv, json, statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINES = {
"Wendover Productions":1257704,"PolyMatter":375143,
"Company Man":133269}
REQUIRED = {"channel","video_title","published_utc","format","views_lifetime","source_url","capture_date","title_pattern"}

def med(xs):
    return round(statistics.median(xs), 3) if xs else None

def analyze(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        errors = []
        missing = sorted(REQUIRED - set(reader.fieldnames or []))
        if missing: errors.append("Missing headers: " + ", ".join(missing))
        rows = list(reader)
    valid, seen = [], set()
    for n, r in enumerate(rows, 2):
        key = tuple(r.get(k, "").strip() for k in ("channel","video_title","published_utc"))
        if key in seen: errors.append(f"Duplicate row {n}: {key}")
        seen.add(key)
        try: views = int(r["views_lifetime"].replace(",","").strip())
        except (ValueError, KeyError, AttributeError): views = None
        try: age = (date.fromisoformat(r["capture_date"]) - date.fromisoformat(r["published_utc"])).days
        except (ValueError, KeyError, TypeError): age = None
        if not all(key): errors.append(f"Missing identity at row {n}")
        if views is None: errors.append(f"Invalid views at row {n}")
        if age is None or age < 0: errors.append(f"Invalid date/negative age at row {n}")
        if not r.get("source_url","").strip(): errors.append(f"Missing source URL at row {n}")
        if all(key) and views is not None and age is not None and age >= 0:
            base = BASELINES.get(key[0])
            r["_views"], r["_age"], r["_ratio"] = views, age, views/base if base else None
            valid.append(r)
    channels, patterns, cohorts = defaultdict(list), defaultdict(list), defaultdict(list)
    formats = Counter()
    for r in valid:
        channels[r["channel"]].append(r); patterns[r.get("title_pattern") or "unclassified"].append(r)
        formats[r.get("format") or "unknown"] += 1
        a = r["_age"]; cohort = "0-30d" if a<=30 else "31-90d" if a<=90 else "91-180d" if a<=180 else "181d+"
        cohorts[cohort].append(r)
    ch = {}
    for name, rs in sorted(channels.items()):
        ratios = [r["_ratio"] for r in rs if r["_ratio"] is not None]
        ch[name] = {"videos":len(rs),"median_lifetime_views":med([r["_views"] for r in rs]),
          "baseline_48_upload_median":BASELINES.get(name),"median_vs_channel_baseline":med(ratios),
          "median_age_days":med([r["_age"] for r in rs]),
          "format_mix":dict(Counter(r.get("format","unknown") for r in rs))}
    pat = {}
    for name, rs in sorted(patterns.items(), key=lambda x:(-len(x[1]),x[0])):
        ratios=[r["_ratio"] for r in rs if r["_ratio"] is not None]
        pat[name]={"videos":len(rs),"channels":len({r["channel"] for r in rs}),
          "median_lifetime_views":med([r["_views"] for r in rs]),"median_channel_baseline_ratio":med(ratios)}
    ageout={k:{"videos":len(rs),"median_lifetime_views":med([r["_views"] for r in rs]),
      "median_channel_baseline_ratio":med([r["_ratio"] for r in rs if r["_ratio"] is not None])} for k,rs in cohorts.items()}
    return {"rows_read":len(rows),"valid_rows":len(valid),"invalid_rows":len(rows)-len(valid),
      "channel_count":len(channels),"format_mix":dict(formats),"validation_errors":errors,
      "channels":ch,"title_patterns":pat,"upload_age_cohorts":ageout,
      "limitations":["Views are lifetime totals, not first-day or first-week views.",
      "Only all-long-form baseline channels are normalized; mixed-format channel medians are excluded because the format mix differs.",
      "Pattern comparisons are descriptive and non-causal; topic, channel, format and age confound results.",
      "Public data does not provide CTR, retention, swipe-away rate, subscriber conversion or revenue."]}

def markdown(d):
    L=["# NEXTDECODE Benchmark Analysis","",f"- Rows: {d['rows_read']} | valid: {d['valid_rows']} | invalid: {d['invalid_rows']}",
      f"- Channels: {d['channel_count']} | format mix: {d['format_mix']}","","## Channel-normalized summary","",
      "| Channel | Videos | Median views | 48-upload baseline | Median / baseline | Median age days |","|---|---:|---:|---:|---:|---:|"]
    for n,x in d["channels"].items(): L.append(f"| {n} | {x['videos']} | {x['median_lifetime_views']} | {x['baseline_48_upload_median']} | {x['median_vs_channel_baseline']} | {x['median_age_days']} |")
    L += ["","## Title-pattern observations","","| Pattern | Videos | Channels | Median views | Median / baseline |","|---|---:|---:|---:|---:|"]
    for n,x in d["title_patterns"].items(): L.append(f"| {n} | {x['videos']} | {x['channels']} | {x['median_lifetime_views']} | {x['median_channel_baseline_ratio']} |")
    L += ["","## Upload-age cohorts (descriptive only)","","| Cohort | Videos | Median views | Median / baseline |","|---|---:|---:|---:|"]
    for n,x in d["upload_age_cohorts"].items(): L.append(f"| {n} | {x['videos']} | {x['median_lifetime_views']} | {x['median_channel_baseline_ratio']} |")
    L += ["","## Validation"] + [f"- {e}" for e in d["validation_errors"]] if d["validation_errors"] else ["","## Validation","- No structural/data validation errors detected."]
    L += ["","## Interpretation limits"] + [f"- {x}" for x in d["limitations"]]
    L += ["","Generated by tools/research/analyze_faceless_benchmark.py. Descriptive correlations are not causal findings."]
    return "\n".join(L)+"\n"

def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",type=Path,default=ROOT/"data/research/faceless_video_observations_pilot_2026-11-17.csv")
    p.add_argument("--output-dir",type=Path,default=ROOT/"reports/research"); a=p.parse_args()
    d=analyze(a.input); a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/"NEXTDECODE_FACELESS_BENCHMARK_ANALYSIS_2026-11-17.json").write_text(json.dumps(d,indent=2)+"\n")
    (a.output_dir/"NEXTDECODE_FACELESS_BENCHMARK_ANALYSIS_2026-11-17.md").write_text(markdown(d))
    print(json.dumps({k:d[k] for k in ("rows_read","valid_rows","invalid_rows","channel_count","validation_errors")},indent=2))
    return 1 if d["validation_errors"] else 0
if __name__=="__main__": raise SystemExit(main())
