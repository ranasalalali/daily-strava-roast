# daily-strava-roast

A portable AgentSkill for turning recent Strava activity into a funny daily roast.

## What it does

- fetches recent Strava activity
- extracts a few useful metrics
- turns them into a short roast or recap
- supports multiple tones like `dry`, `playful`, `savage`, and `coach`

## Why it exists

There are already serious Strava integration and coaching skills.

This one is for the more important use case: lightly bullying your workout history into being entertaining.

## Structure

- `SKILL.md` — agent instructions
- `scripts/strava_roast.py` — roast generator
- `references/design.md` — design notes and heuristics
- `tests/smoke_test.py` — fixture-based smoke test

## Example commands

```bash
python scripts/strava_roast.py roast
python scripts/strava_roast.py roast --tone dry
python scripts/strava_roast.py roast --tone savage
python scripts/strava_roast.py summary --json --pretty
```

## Example output

```text
Lunch Run: 8.42 km of run in 46 min with 7 kudos. Public evidence that cardio and questionable judgment can coexist beautifully.
Evening Tennis: 5.23 km of tennis in 52 min with 3 kudos. Public evidence that cardio and questionable judgment can coexist beautifully.
Overall: 13.65 km across 2 activities and 98 moving minutes. A productive little festival of exertion.
```
