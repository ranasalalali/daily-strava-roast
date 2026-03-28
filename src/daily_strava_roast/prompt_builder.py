from __future__ import annotations

from typing import Any


PROMPT_INTRO = (
    "Write exactly one short paragraph roasting this day of Strava activity. "
    "Be funny, dry, slightly mean, but not cruel. "
    "Use natural prose, not bullets or stat-dumping. "
    "Do not invent facts."
)


def _fmt_list(values: list[str]) -> str:
    cleaned = [v for v in values if v]
    if not cleaned:
        return "none"
    return ", ".join(cleaned)


def build_roast_prompt(context: dict[str, Any]) -> str:
    totals = context.get("totals", {})
    effort = context.get("effort", {})
    hints = context.get("pattern_hints", {})
    style = context.get("style", {})

    lines = [
        PROMPT_INTRO,
        "",
        "Context:",
        f"- date: {context.get('date') or 'unknown'}",
        f"- activity_count: {context.get('activity_count', 0)}",
        f"- sports: {_fmt_list(context.get('sports', []))}",
        f"- dominant_sport: {context.get('dominant_sport') or 'none'}",
        f"- activity_names: {_fmt_list(context.get('activity_names', []))}",
        f"- total_distance_km: {totals.get('distance_km', 0)}",
        f"- total_moving_minutes: {totals.get('moving_minutes', 0)}",
        f"- total_elevation_m: {totals.get('elevation_m', 0)}",
        f"- total_kudos: {totals.get('kudos', 0)}",
        f"- avg_hr: {effort.get('avg_hr') if effort.get('avg_hr') is not None else 'unknown'}",
        f"- max_hr: {effort.get('max_hr') if effort.get('max_hr') is not None else 'unknown'}",
        f"- indoor_count: {hints.get('indoor_count', 0)}",
        f"- repeat_sport_recently: {bool(hints.get('repeat_sport_recently', False))}",
        f"- requested_tone: {style.get('tone', 'playful')}",
        f"- requested_spice: {style.get('spice', 3)}",
        "",
        "Constraints:",
        "- Output exactly one paragraph.",
        "- Do not use bullet points, labels, or quotation marks.",
        "- Do not list every stat mechanically.",
        "- Weave in only the most relevant details.",
        "- Avoid sounding like a dashboard, coach app, or generic AI assistant.",
        "- If there are repeated sports lately, hint at the pattern without sounding repetitive.",
        "- Keep it sharp and readable.",
    ]
    return "\n".join(lines)
