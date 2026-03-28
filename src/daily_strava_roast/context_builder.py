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


def build_roast_context(day: dict[str, Any], tone: str, spice: int, recent_state: dict[str, Any] | None = None) -> dict[str, Any]:
    summaries = day.get("summaries", [])
    sport_labels = [summarize_sport_label(s.get("sport", "activity")) for s in summaries]
    counts = Counter(sport_labels)
    dominant_sport = counts.most_common(1)[0][0] if counts else None
    recent = (recent_state or {}).get("recent", [])
    recent_sports = []
    for item in recent:
        if isinstance(item, dict):
            value = item.get("sports", [])
            if isinstance(value, list):
                recent_sports.extend([v for v in value if isinstance(v, str)])

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
        "style": {
            "tone": tone,
            "spice": spice,
            "target": "one short paragraph",
            "voice": "funny, dry, slightly mean but not cruel",
        },
    }
