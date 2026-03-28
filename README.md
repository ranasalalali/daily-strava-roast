# daily-strava-roast

A portable AgentSkill and Python CLI for turning recent Strava activity into a funny daily roast.

## Overview

`daily-strava-roast` reads recent Strava activity and turns it into a short recap with adjustable sarcasm.

It is built for:
- playful workout summaries
- scheduled daily activity roasts
- post-workout recaps with personality
- configurable tone and spice level

## Why it exists

There are already serious Strava integration and coaching skills.

This project exists for a far nobler purpose: making your training log entertaining enough to deserve being read.

## One canonical repo, two interfaces

This repo serves both as:
- a **portable AgentSkill** via `SKILL.md`
- a **small Python CLI** via the packaged `daily-strava-roast` command

That keeps the implementation, local use, and eventual publication aligned in one place.

## Features

- fetch recent Strava activity from a token file
- summarize key metrics
- roast by activity type
- adjustable tone: `dry`, `playful`, `savage`, `coach`
- adjustable spice: `0..3`
- JSON summary output for scripting

## Repo structure

- `SKILL.md` — agent instructions
- `scripts/strava_roast.py` — bundled script used by the skill
- `src/daily_strava_roast/cli.py` — packaged CLI entrypoint
- `references/design.md` — design notes and roast heuristics
- `tests/smoke_test.py` — fixture-based smoke test

## CLI usage

```bash
uv run --project . daily-strava-roast roast
uv run --project . daily-strava-roast roast --tone playful --spice 2
uv run --project . daily-strava-roast roast --tone savage --spice 3
uv run --project . daily-strava-roast summary --json --pretty
```

## Script usage

```bash
python scripts/strava_roast.py roast  # defaults to tone=playful, spice=3
python scripts/strava_roast.py roast --tone dry --spice 1
python scripts/strava_roast.py roast --tone coach --spice 0
```

## Example output

```text
Evening Weight Training: 59 min of weight training. Same room, same iron, same refusal to choose peace.
Lunch Run: 5.04 km in 28 min. Efficient, uncomfortable, and exactly the kind of idea your legs will remember tomorrow.
Evening Tennis: 64 min of tennis. Just enough running to be annoying, not enough to count as honesty.
Overall: 7.23 km across 3 activities and 151 moving minutes. Productive, disciplined, and a little bit deranged.
```

## Testing

```bash
python tests/smoke_test.py
```

CI checks:
- CLI help
- smoke test execution
- package build
