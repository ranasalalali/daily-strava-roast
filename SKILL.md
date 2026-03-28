---
name: daily-strava-roast
description: Generate a playful or sharp daily roast of recent Strava activity. Use when asked to roast, recap, tease, or humorously summarize a Strava workout or a recent day of training. Useful for scheduled daily activity roasts, playful fitness summaries, or lightly sarcastic post-workout commentary.
---

# Daily Strava Roast

Use this skill to turn recent Strava activity into a short roast-style summary.

## What it does

This skill:
- reads recent Strava activity data
- summarizes key workout metrics
- produces a short roast or playful recap
- supports different tones and spice levels for scheduled or on-demand use

## Script usage

Run the bundled script:

```bash
python {baseDir}/scripts/strava_roast.py roast
python {baseDir}/scripts/strava_roast.py roast --tone dry --spice 1
python {baseDir}/scripts/strava_roast.py roast --tone playful --spice 2
python {baseDir}/scripts/strava_roast.py roast --tone savage --spice 3
python {baseDir}/scripts/strava_roast.py summary --json --pretty
```

## Inputs

By default the script looks for Strava tokens in:

```bash
~/.openclaw/workspace/agents/tars-fit/strava_tokens.json
```

Override with:

```bash
python {baseDir}/scripts/strava_roast.py roast --token-file /path/to/strava_tokens.json
```

## Tones

Supported tones:
- `dry`
- `playful`
- `savage`
- `coach`

## Spice

Spice controls roast intensity:
- `0` — gentle
- `1` — light tease
- `2` — proper roast
- `3` — scorched earth

## References

For field assumptions and roast heuristics, read:
- `references/design.md`
