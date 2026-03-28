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


def _activity_guidance(activity_count: int) -> list[str]:
    if activity_count <= 0:
        return [
            "- There were no logged activities for this day.",
            "- Roast the absence with restraint; do not pretend a workout happened.",
            "- Keep the joke about rest, silence, stealth, or suspicious inactivity grounded in the missing activity.",
        ]
    if activity_count == 1:
        return [
            "- Focus on the single session instead of pretending there was an epic training block.",
            "- Use one or two concrete details, not a full stat recital.",
        ]
    return [
        "- Treat the day as one combined story, not separate mini-recaps.",
        "- Mention the mix of activities only if it helps the joke.",
    ]


def build_roast_prompt(context: dict[str, Any]) -> str:
    activity_count = int(context.get("activity_count", 0) or 0)
    totals = context.get("totals", {})
    effort = context.get("effort", {})
    hints = context.get("pattern_hints", {})
    style = context.get("style", {})

    lines = [
        PROMPT_INTRO,
        "",
        "Context:",
        f"- date: {context.get('date') or 'unknown'}",
        f"- activity_count: {activity_count}",
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
        "- Do not use bullet points, labels, or quotation marks in the final output.",
        "- Do not list every stat mechanically.",
        "- Weave in only the most relevant details.",
        "- Avoid sounding like a dashboard, coach app, or generic AI assistant.",
        "- Keep it sharp, readable, and specific.",
    ]

    lines.extend(_activity_guidance(activity_count))

    if bool(hints.get("repeat_sport_recently", False)):
        lines.append("- Hint at the repeated-sport pattern without repeating old phrasing.")
    if int(hints.get("indoor_count", 0) or 0) > 0:
        lines.append("- If useful, lightly acknowledge the indoor/trainer angle without overexplaining it.")
    if style.get("tone") == "coach" or style.get("spice") == 0:
        lines.append("- Keep the edge light; this should feel more encouraging than cruel.")
    else:
        lines.append("- Let the joke land, but keep it human and readable.")

    return "\n".join(lines)
