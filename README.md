# daily-strava-roast

A portable AgentSkill for turning recent Strava activity into a funny daily roast.

## What it does

- fetches recent Strava activity
- extracts useful workout metrics
- turns them into a short roast or recap
- supports multiple tones like `dry`, `playful`, `savage`, and `coach`
- supports a configurable `spice` level for how hard it hits

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
python scripts/strava_roast.py roast --tone dry --spice 1
python scripts/strava_roast.py roast --tone playful --spice 2
python scripts/strava_roast.py roast --tone savage --spice 3
python scripts/strava_roast.py summary --json --pretty
```

## Example output

```text
Lunch Run: 8.42 km in 46 min. Efficient, uncomfortable, and exactly the kind of idea your legs will remember tomorrow.
Evening Tennis: 52 min of tennis. Just enough running to be annoying, not enough to count as honesty.
Overall: 13.65 km across 2 activities and 98 moving minutes. Productive, disciplined, and a little bit deranged.
```
