# Monetization readiness and progress

## Targets

YouTube currently describes two relevant paths for eligible creators:

- **Expanded YPP / fan-funding features:** 500 subscribers, 3 valid public uploads
  in the last 90 days, and either 3,000 qualified long-form watch hours in the last
  365 days or 3 million qualified public Shorts views in the last 90 days.
- **Ads and Premium revenue:** 1,000 subscribers and either 4,000 qualified
  long-form watch hours in the last 365 days or 10 million qualified public Shorts
  views in the last 90 days.

See the official [YPP overview](https://support.google.com/youtube/answer/72851)
and [monetization feature thresholds](https://support.google.com/youtube/answer/94522)
for the account's current availability. YouTube still reviews the channel for
policy compliance after thresholds are reached. Shorts-feed watch time does not
count toward the 4,000 long-form watch-hour requirement.

## 30-day operating targets

- Publish or prepare 20 original, review-passed packages at five per week.
- Reach the expanded-YPP milestone if the channel's starting audience and distribution
  make it realistic; the tracker must show the gap every week.
- Treat the full ads milestone as a stretch target. Do not claim it is achievable
  from output volume alone.
- Keep a policy-safe evidence trail: sources, original visuals, limitations, and
  per-platform publication records.
- Set up two-step verification, advanced features, AdSense readiness, and the Earn
  page notification before claiming eligibility.

## What to record

Update `monetization_progress.json` from YouTube Studio at least weekly:

- subscribers
- valid public uploads in the last 90 days
- qualified Shorts views in the last 90 days
- qualified long-form watch hours in the last 365 days
- policy/feature readiness notes
- date checked and source dashboard

Use `monetization_tracker.py` to update the snapshot without storing credentials.
The tracker calculates percentages and gaps; it never claims that approval or
revenue is guaranteed.

