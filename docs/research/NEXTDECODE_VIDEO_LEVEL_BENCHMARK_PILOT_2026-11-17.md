# NEXTDECODE Video-Level Competitor Benchmark — First Observed Sample

**Capture date:** 2026-11-17  
**Rows:** 40 public upload observations  
**Channels:** 5 (Primal Space, Real Engineering, Found And Explained, Wendover Productions, Mustard)  
**Source:** vidIQ public channel upload tables, which attribute their statistics to public YouTube data.

## Important interpretation limits

- Views are lifetime public view totals at the capture date, not views in the first 24/48 hours.
- Newer uploads have had less time to accumulate views.
- The tables are channel-specific samples; raw views must not be pooled as if each channel had the same audience size.
- Duration categories are taken from source tables. A 1:15 item is labelled Short in the source; Shorts can exceed 60 seconds under current YouTube rules.
- The title-pattern labels are editorial coding by NEXTDECODE, not causal findings. They describe the promise/framing suggested by the title only.
- This is a 40-row sample, not the 1,000-video target. It is biased toward channels for which recent upload tables were available and easy to retrieve.
- Public data does not reveal CTR, swipe-away rate, audience retention, subscriber conversion or revenue. Do not infer these.

## Initial qualitative signals (hypotheses to test)

1. **A concrete object + a surprising constraint** recurs: “38% Nose”, a submarine battleship, a gyroscope, a cable, a monster telescope.
2. **Why did it disappear / what happened to it?** is a repeatable curiosity frame in the machine-history lane.
3. **Systems behind familiar things** (hotel brands, IKEA, channel tunnel) can make everyday subjects feel newly consequential.
4. **Specificity beats generic category labels** in the observed title set: named machine, place, material, event, or measurable attribute.
5. **Shorts are not always under 60 seconds** in this sample; benchmark format by the source's Shorts/long-form classification, not duration alone.
6. The same story may support multiple runtimes: a short can isolate one surprising mechanism, while long-form can explain context, trade-offs and consequences.

These are editorial hypotheses, not evidence that a particular wording caused higher views. The next expansion should compare each video's views with its own channel's recent median and account for upload age.

## Source pages

- [Primal Space upload table](https://vidiq.com/youtube-stats/channel/@primalspace/videos/)
- [Real Engineering upload table](https://vidiq.com/youtube-stats/channel/@realengineering/videos/)
- [Found And Explained upload table](https://vidiq.com/youtube-stats/channel/@foundandexplained/videos/)
- [Wendover Productions upload table](https://vidiq.com/youtube-stats/channel/@wendoverproductions/videos/)
- [Mustard upload table](https://vidiq.com/youtube-stats/channel/@mustardchannel/videos/)

See the companion CSV for all 40 row-level observations and their source/capture metadata.
## Benchmark expansion — 4 additional channels

**Added on:** 2026-11-17  
**New observations:** 32  
**Additional channels:** PolyMatter, Economics Explained, Astrum, Company Man

All values are public lifetime views from the cited vidIQ upload tables, captured on 2026-11-17 (source page updates may differ slightly by retrieval time). These rows extend the first 40-row sample to **72 observations across 9 channels**. Each title-pattern tag is qualitative coding, not a causal claim.

### Channel baseline context (recent 48-upload medians reported by vidIQ)

| Channel | Recent sample median views | Recent upload cadence note |
|---|---:|---|
| Primal Space | 96,121 | 48-upload sample includes 11 long-form and 37 Shorts |
| Real Engineering | 869,145 | 48-upload sample includes 24 long-form and 24 Shorts |
| Found And Explained | 327,204 | 48-upload sample includes 47 long-form and 1 Short |
| Wendover Productions | 1,257,704 | 48-upload sample all long-form |
| Mustard | 6,312,013 | 48-upload sample includes 42 long-form and 6 Shorts |
| PolyMatter | 375,143 | 48-upload sample all long-form |
| Economics Explained | 531,142 | 48-upload sample includes 46 long-form and 2 Shorts |
| Astrum | 929,617 | 48-upload sample includes 44 long-form and 4 Shorts |
| Company Man | 133,269 | 48-upload sample all long-form |

Do not interpret these medians as fair performance rankings. Channel age, audience size, upload history and topic mix differ. Use per-channel normalized ratios and upload-age cohorts in the next analysis.

### Additional source pages

- [PolyMatter uploads](https://vidiq.com/youtube-stats/channel/@polymatter/videos/)
- [Economics Explained uploads](https://vidiq.com/youtube-stats/channel/@economicsexplained/videos/)
- [Astrum uploads](https://vidiq.com/youtube-stats/channel/@astrumspace/videos/)
- [Company Man uploads](https://vidiq.com/youtube-stats/channel/@companyman114/videos/)


## Reproducible analysis and data-quality correction — 2026-11-17

The 72-row CSV is now validated by the standard-library analyzer at
tools/research/analyze_faceless_benchmark.py. It checks required columns, duplicate
(channel, title, publication date) keys, parseable view counts, publication/capture
dates, non-negative upload age, and source URLs. The first validation pass exposed
three titles containing unquoted commas; those CSV fields were corrected and the
final validation now reports **72 valid rows, 0 invalid rows, across 9 channels**.

Generated outputs:
- reports/research/NEXTDECODE_FACELESS_BENCHMARK_ANALYSIS_2026-11-17.md
- reports/research/NEXTDECODE_FACELESS_BENCHMARK_ANALYSIS_2026-11-17.json

The analyzer reports per-channel medians, format mix, median upload age, title-pattern
descriptives, and broad upload-age cohorts. It only computes median-to-baseline
ratios where the published 48-upload reference sample is all long-form; mixed-format
baselines are excluded to avoid comparing long-form-heavy samples with a Shorts-heavy
reference mix. Even the retained ratios are contextual rather than age-matched.
No title-pattern or channel result is a causal claim.

Focused test: tests/test_faceless_benchmark_analysis.py — 1 passed.
