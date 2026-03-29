# Changelog

All notable changes to `daily-strava-roast` will be documented in this file.

## 0.2.1

- document publish hygiene and clean ClawHub bundle expectations
- update README and V2 docs to reflect the shipped 0.2.x state
- clarify security/publish guidance for excluding local state, virtualenvs, build artifacts, and secrets

## 0.2.0

- merge the V2 branch into main
- add deterministic daily target-date selection so no-activity days roast correctly
- add structured V2 roast context and constrained prompt generation
- add lightweight roast memory hints for recent joke families, openings, and targets
- sharpen runtime prompt guidance for drier, meaner, less repetitive output
- clarify package-vs-runtime boundaries in the skill and V2 docs
- add focused regression coverage for prompt building, target-day behavior, generator behavior, and roast-memory hints

## 0.1.2

- improve inactivity roast logic with better gap-based judgment
- add lightweight roast memory to reduce repetition and notice short-term patterns
- add occasional heart-rate flavor to enrich some roasts
- improve roast phrasing, defaults, and no-activity narrative flow

## 0.1.1

- improve roast phrasing
- improve inactivity handling
- add lightweight roast memory foundations

## 0.1.0

- initial public release
- portable AgentSkill + CLI structure
- daily roll-up roast behavior
- tone and spice controls
- fixture-based smoke test and CI
