# Daily Strava Roast design notes

## Goal

Generate short, funny, human-readable commentary from recent Strava activity.

## Primary input

Recent Strava activity JSON fetched from the athlete activities endpoint.

Useful fields include:
- `name`
- `sport_type` or `type`
- `distance`
- `moving_time`
- `elapsed_time`
- `total_elevation_gain`
- `average_speed`
- `average_heartrate`
- `max_heartrate`
- `average_watts`
- `suffer_score`
- `kudos_count`
- `start_date_local`
- `trainer`
- `commute`

## Output style

Keep roasts short.

Good output traits:
- 1–4 lines
- playful, readable, and specific
- based on actual metrics, not random invented insults
- able to switch between dry/playful/savage/coach modes

## Failure cases

If there is no recent activity:
- do not invent one
- produce a short joke about rest day / inactivity / stealth mode

If data is sparse:
- roast gently and mention only what is known

## Scheduling intent

This skill should be usable by a scheduler later, so the roast output should be:
- concise
- deterministic enough to test
- still varied by tone and activity type

## Package vs runtime boundary

Keep this distinction explicit:
- the package/CLI owns deterministic fetch, rollup, context, prompt prep, preview, and stable fallback roast generation
- the OpenClaw runtime can own connected/default-model generation for the final paragraph when available
- if the runtime generation path fails, use the deterministic roast rather than surfacing a brittle model error to the end user
