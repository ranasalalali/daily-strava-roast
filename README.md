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
- target the local calendar day for daily roasts so no-activity days behave correctly
- summarize the day instead of dumping raw activity lines
- generate compact narrative roasts
- adjustable tone: `dry`, `playful`, `savage`, `coach`
- adjustable spice: `0..3` (default leans spicy)
- smarter no-activity roasts based on inactivity gap
- lightweight roast memory to reduce repetition over time
- structured V2 context and prompt generation for runtime model use
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
uv run --project . daily-strava-roast generate --model-runner ollama --model llama3.2
uv run --project . daily-strava-roast roast
```

V2 staging note:
- `context` emits the structured roast context JSON
- `prompt` emits the constrained prompt text built from that context
- `preview` emits a local preview paragraph from the V2 context/prompt path for prompt-shape evaluation
- `generate` is an explicit local generation test path
- `roast` remains deterministic in the packaged CLI
- connected/default-model generation belongs to the OpenClaw runtime skill layer, not the standalone package CLI
- the intended runtime flow is: `context` -> `prompt` -> connected model paragraph -> fallback to deterministic `roast` when needed

## Script usage

```bash
python scripts/strava_roast.py roast
python scripts/strava_roast.py roast --tone playful --spice 3
python scripts/strava_roast.py roast --tone dry --spice 1
python scripts/strava_roast.py summary --json --pretty
```

## Example output

Deterministic roast example:

```text
Morning Ride: 56.95 km of ride in 150 min. A creative new way to be tired for no financial reward.
```

Runtime V2 target example:

```text
Morning Ride sounds like you were trying to file 56.95 km and 733 m of climbing under casual admin, which is an impressively committed way to pretend this hobby isn't just organised self-inflicted inconvenience.
```

## Testing

```bash
python tests/smoke_test.py
python tests/test_context_builder.py
python tests/test_prompt_builder.py
python tests/test_target_day.py
python tests/test_roast_memory.py
python tests/test_generator.py
```

CI checks:
- CLI help
- smoke test execution
- package build

## Publish hygiene

Do not publish local runtime leftovers such as:
- `.venv/`
- `dist/`
- `state/`
- token files or any local secrets

A small `.clawhubignore` is included to document the intended exclusions for ClawHub publishing.

## Design goals

- portable
- local-first
- funny without becoming unreadable
- small and pragmatic
- suitable for both real use and eventual publication
