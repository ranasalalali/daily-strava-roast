from __future__ import annotations

from collections import Counter
from typing import Any


def summarize_sport_label(sport: str) -> str:
    s = sport.lower()
    if "run" in s:
        return "run"
    if "ride" in s or "cycle" in s:
        return "ride"
    if "tennis" in s:
        return "tennis"
    if "weight" in s:
        return "weight training"
    return s


def _recent_state_hints(recent_state: dict[str, Any] | None) -> tuple[list[str], list[str], list[str], list[str]]:
    recent = (recent_state or {}).get("recent", [])
    recent_sports: list[str] = []
    recent_families: list[str] = []
    recent_openings: list[str] = []
    recent_targets: list[str] = []

    for item in recent:
        if not isinstance(item, dict):
            continue
        sports = item.get("sports", [])
        if isinstance(sports, list):
            recent_sports.extend([v for v in sports if isinstance(v, str)])
        family = item.get("joke_family") or item.get("family")
        if isinstance(family, str) and family:
            recent_families.append(family)
        opening = item.get("opening_style")
        if isinstance(opening, str) and opening:
            recent_openings.append(opening)
        targets = item.get("joke_targets", [])
        if isinstance(targets, list):
            recent_targets.extend([v for v in targets if isinstance(v, str)])

    return recent_sports, recent_families[-3:], recent_openings[-3:], recent_targets[-5:]


def build_roast_context(day: dict[str, Any], tone: str, spice: int, recent_state: dict[str, Any] | None = None) -> dict[str, Any]:
    summaries = day.get("summaries", [])
    sport_labels = [summarize_sport_label(s.get("sport", "activity")) for s in summaries]
    counts = Counter(sport_labels)
    dominant_sport = counts.most_common(1)[0][0] if counts else None
    recent_sports, recent_families, recent_openings, recent_targets = _recent_state_hints(recent_state)

    return {
        "date": day.get("date"),
        "activity_count": day.get("count", 0),
        "sports": sport_labels,
        "dominant_sport": dominant_sport,
        "activity_names": [s.get("name") for s in summaries if s.get("name")],
        "totals": {
            "distance_km": day.get("total_km", 0),
            "moving_minutes": day.get("total_min", 0),
            "elevation_m": day.get("total_elev", 0),
            "kudos": day.get("total_kudos", 0),
        },
        "effort": {
            "avg_hr": next((s.get("avg_hr") for s in summaries if s.get("avg_hr") is not None), None),
            "max_hr": next((s.get("max_hr") for s in summaries if s.get("max_hr") is not None), None),
        },
        "pattern_hints": {
            "indoor_count": day.get("indoor_count", 0),
            "repeat_sport_recently": any(s in recent_sports for s in day.get("sports", [])),
        },
        "roast_memory": {
            "recent_families": recent_families,
            "recent_openings": recent_openings,
            "recent_targets": recent_targets,
        },
        "style": {
            "tone": tone,
            "spice": spice,
            "target": "one short paragraph",
            "voice": "funny, dry, slightly mean but not cruel",
        },
    }
