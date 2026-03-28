# daily-strava-roast

[![CI](https://github.com/ranasalalali/daily-strava-roast/actions/workflows/ci.yml/badge.svg)](https://github.com/ranasalalali/daily-strava-roast/actions/workflows/ci.yml)

A portable AgentSkill and Python CLI for turning recent Strava activity into a funny daily roast.

## Overview

`daily-strava-roast` reads recent Strava activity and turns it into a short recap with adjustable sarcasm.

It is built for:
- playful workout summaries
- scheduled daily activity roasts
- post-workout recaps with personality
- configurable tone and spice level
- slightly unnecessary but highly respectable levels of sass

## Quick start

```bash
uv run --project . daily-strava-roast roast
uv run --project . daily-strava-roast roast --tone playful --spice 3
uv run --project . daily-strava-roast summary --json --pretty
```

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
- summarize the day instead of dumping raw activity lines
- generate compact narrative roasts
- adjustable tone: `dry`, `playful`, `savage`, `coach`
- adjustable spice: `0..3` (default leans spicy)
- smarter no-activity roasts based on inactivity gap
- lightweight roast memory to reduce repetition over time
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
uv run --project . daily-strava-roast roast --tone playful --spice 3
uv run --project . daily-strava-roast roast --tone coach --spice 0
uv run --project . daily-strava-roast summary --json --pretty
uv run --project . daily-strava-roast context --pretty
uv run --project . daily-strava-roast prompt
uv run --project . daily-strava-roast preview
uv run --project . daily-strava-roast generate --generation-mode local --model-runner ollama --model llama3.2
uv run --project . daily-strava-roast roast
```

V2 staging note:
- `context` emits the structured roast context JSON
- `prompt` emits the constrained prompt text built from that context
- `preview` emits a local preview paragraph from the V2 context/prompt path
- `generate` is an explicit generation test path
- `roast` now prefers connected-model generation by default and falls back to the deterministic V1 roast if generation is unavailable or fails
- local model generation remains available via `--generation-mode local`

## Script usage

```bash
python scripts/strava_roast.py roast
python scripts/strava_roast.py roast --tone playful --spice 3
python scripts/strava_roast.py roast --tone dry --spice 1
python scripts/strava_roast.py summary --json --pretty
```

## Example output

```text
You opened the day with a ride, which is a very committed way to spend your free will. It wasn't an all-day epic, but 150 moving minutes, 56.95 km, and 733 m of climbing still adds up to a very respectable little commitment to tiredness. 10 kudos suggests people are willing to encourage this sort of behaviour, which feels generous if not entirely responsible.
```

## Testing

```bash
python tests/smoke_test.py
```

CI checks:
- CLI help
- smoke test execution
- package build

## Design goals

- portable
- local-first
- funny without becoming unreadable
- small and pragmatic
- suitable for both real use and eventual publication
