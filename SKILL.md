---
name: daily-strava-roast
description: Generate a playful or sharp daily roast of recent Strava activity. Use when asked to roast, recap, tease, or humorously summarize a Strava workout or a recent day of training. Useful for scheduled daily activity roasts, playful fitness summaries, or lightly sarcastic post-workout commentary. Prefer the deterministic package/script for data prep and fallback; when running inside OpenClaw, use the connected/default runtime model only for the final paragraph if available, then fall back to the deterministic roast path on failure.
---

# Daily Strava Roast

Use this skill to turn recent Strava activity into a short roast-style summary.

## Default workflow

1. Use the deterministic implementation first to fetch and summarize activity.
2. If you are inside OpenClaw and want the V2 path, use the structured context/prompt output as model input for the **final paragraph only**.
3. If connected-model generation is unavailable or weak, fall back to the deterministic roast output.
4. Do not pretend the standalone Python package has a built-in OpenClaw connected-model API if it does not.

## What this skill does

This skill provides:
- deterministic Strava fetch + summary tooling
- adjustable tones and spice levels
- V1 roast fallback that is stable and testable
- V2 context/prompt building for better final-paragraph generation in the OpenClaw runtime

## Preferred commands

Use the packaged CLI for deterministic preparation and fallback:

```bash
uv run --project {baseDir} daily-strava-roast summary --json --pretty
uv run --project {baseDir} daily-strava-roast context --pretty
uv run --project {baseDir} daily-strava-roast prompt
uv run --project {baseDir} daily-strava-roast roast
```

Legacy script usage is still valid when needed:

```bash
python {baseDir}/scripts/strava_roast.py roast
python {baseDir}/scripts/strava_roast.py summary --json --pretty
```

## Runtime guidance

When invoked inside OpenClaw for an actual roast reply:
- run deterministic preparation first
- use the connected/default runtime model only to write the final roast paragraph
- keep that paragraph to one short paragraph
- do not invent stats
- if generation fails, return the deterministic roast instead of erroring

### Runtime recipe

Use this sequence:

1. Build context JSON:

```bash
uv run --project {baseDir} daily-strava-roast context --pretty
```

2. Build the constrained prompt:

```bash
uv run --project {baseDir} daily-strava-roast prompt
```

3. Ask the connected/default OpenClaw runtime model to write the final paragraph from that prompt.
4. Before replying, sanity-check the generated paragraph:
   - exactly one paragraph
   - no bullet points
   - no invented stats
   - not generic AI filler
   - tone matches requested spice/tone closely enough
5. If the paragraph fails those checks or generation is unavailable, fall back to:

```bash
uv run --project {baseDir} daily-strava-roast roast
```

### Fallback triggers

Fall back immediately if any of these happen:
- no connected/default runtime model is available
- generated output is empty
- generated output invents numbers, activities, or claims not present in the prompt/context
- generated output is multiple paragraphs or list-like
- generated output is obviously generic, repetitive, or less readable than the deterministic roast

When falling back:
- do not apologize unless the user needs to know
- just return the deterministic roast text

When working purely from the repo/CLI:
- treat connected-model generation as a runtime concern, not a guaranteed packaged-CLI feature
- keep the deterministic path working without extra runtime dependencies

## Inputs

By default the Strava token file is:

```bash
~/.openclaw/workspace/agents/tars-fit/strava_tokens.json
```

Override with:

```bash
uv run --project {baseDir} daily-strava-roast roast --token-file /path/to/strava_tokens.json
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

Read as needed:
- `references/design.md` for roast heuristics and failure cases
- `docs/V2.md` for the V2 architecture and package/runtime boundary
