#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_TOKEN_FILE = Path.home() / ".openclaw" / "workspace" / "agents" / "tars-fit" / "strava_tokens.json"
DEFAULT_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "216808")
DEFAULT_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate a daily Strava roast from recent activity.")
    p.add_argument("command", choices=["summary", "roast"], nargs="?", default="roast")
    p.add_argument("--token-file", default=str(DEFAULT_TOKEN_FILE), help="Path to strava token JSON")
    p.add_argument("--client-id", default=DEFAULT_CLIENT_ID)
    p.add_argument("--client-secret", default=DEFAULT_CLIENT_SECRET)
    p.add_argument("--days", type=int, default=2, help="Look back N days for recent activity")
    p.add_argument("--limit", type=int, default=3, help="Max activities to fetch")
    p.add_argument("--tone", choices=["dry", "playful", "savage", "coach"], default="playful")
    p.add_argument("--spice", type=int, choices=[0, 1, 2, 3], default=3, help="Roast intensity from 0 (gentle) to 3 (scorched)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--pretty", action="store_true")
    return p


def load_tokens(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def save_tokens(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def refresh_tokens(tokens: dict[str, Any], path: Path, client_id: str, client_secret: str | None) -> dict[str, Any]:
    if not client_secret:
        return tokens
    if tokens.get("expires_at", 0) > int(time.time()) + 300:
        return tokens
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"],
    }).encode()
    req = urllib.request.Request("https://www.strava.com/oauth/token", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        fresh = json.load(r)
    save_tokens(path, fresh)
    return fresh


def fetch_activities(tokens: dict[str, Any], days: int, limit: int) -> list[dict[str, Any]]:
    after = int(time.time()) - days * 86400
    query = urllib.parse.urlencode({"after": after, "per_page": limit, "page": 1})
    req = urllib.request.Request(
        f"https://www.strava.com/api/v3/athlete/activities?{query}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def km(distance_m: float | None) -> float:
    return round((distance_m or 0.0) / 1000.0, 2)


def minutes(seconds: int | None) -> int:
    return round((seconds or 0) / 60)


def summarize_activity(a: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": a.get("name") or "Unnamed suffering",
        "sport": a.get("sport_type") or a.get("type") or "Activity",
        "distance_km": km(a.get("distance")),
        "moving_min": minutes(a.get("moving_time")),
        "elev_m": round(a.get("total_elevation_gain") or 0),
        "kudos": a.get("kudos_count") or 0,
        "avg_hr": round(a.get("average_heartrate") or 0) or None,
        "avg_watts": round(a.get("average_watts") or 0) or None,
        "suffer": a.get("suffer_score"),
        "date_local": a.get("start_date_local"),
        "trainer": bool(a.get("trainer")),
    }


def line_for_run(s: dict[str, Any], tone: str, spice: int) -> str:
    base = f"{s['name']}: {s['distance_km']} km in {s['moving_min']} min"
    if tone == 'coach':
        return base + f". Useful work. Now try to recover like someone who plans to run again this century."
    if tone == 'dry':
        return base + ". A concise little appointment with gravity and self-imposed inconvenience."
    if spice >= 3:
        return base + f" with {s['elev_m']} m climbing. Remarkable commitment to making your own life harder on purpose."
    if spice == 2:
        return base + ". Efficient, uncomfortable, and exactly the kind of idea your legs will remember tomorrow."
    if spice == 1:
        return base + f" with {s['kudos']} kudos. Cardio, but make it publicly auditable."
    return base + ". Nice work. Mildly heroic, acceptably unhinged."


def line_for_tennis(s: dict[str, Any], tone: str, spice: int) -> str:
    base = f"{s['name']}: {s['moving_min']} min of tennis"
    if spice >= 3:
        return base + ". Competitive cardio disguised as leisure. A classic scam."
    if spice == 2:
        return base + ". Just enough running to be annoying, not enough to count as honesty."
    if spice == 1:
        return base + f" with {s['kudos']} kudos. Elegant little sprint intervals in polite clothing."
    return base + ". Solid session. Civilized suffering with a racket."


def line_for_weights(s: dict[str, Any], tone: str, spice: int) -> str:
    base = f"{s['name']}: {s['moving_min']} min of weight training"
    if tone == 'coach':
        return base + ". Good. Lift the weight, keep the ego on a shorter leash."
    if spice >= 3:
        return base + ". Zero kilometres, maximum theatrical tension."
    if spice == 2:
        return base + ". Same room, same iron, same refusal to choose peace."
    if spice == 1:
        return base + ". Honest work. No scenery, just reps and consequences."
    return base + ". Strong, sensible, and only moderately feral."


def generic_line(s: dict[str, Any], tone: str, spice: int) -> str:
    sport = s['sport'].lower()
    base = f"{s['name']}: {s['distance_km']} km of {sport} in {s['moving_min']} min"
    if spice >= 3:
        return base + ". A creative new way to be tired for no financial reward."
    if spice == 2:
        return base + ". Public evidence that questionable judgment and endurance remain close friends."
    if spice == 1:
        return base + ". Respectable effort, lightly seasoned with chaos."
    return base + ". Nice little outing."


def roast_line(summary: dict[str, Any], tone: str, spice: int) -> str:
    sport = summary['sport'].lower()
    if 'run' in sport:
        return line_for_run(summary, tone, spice)
    if 'tennis' in sport:
        return line_for_tennis(summary, tone, spice)
    if 'weight' in sport or summary['trainer']:
        return line_for_weights(summary, tone, spice)
    return generic_line(summary, tone, spice)


def overall_line(summaries: list[dict[str, Any]], spice: int) -> str:
    total_km = round(sum(s['distance_km'] for s in summaries), 2)
    total_min = sum(s['moving_min'] for s in summaries)
    if spice >= 3:
        return f"Overall: {total_km} km across {len(summaries)} activities and {total_min} moving minutes. An impressive amount of voluntary wear and tear."
    if spice == 2:
        return f"Overall: {total_km} km across {len(summaries)} activities and {total_min} moving minutes. Productive, disciplined, and a little bit deranged."
    if spice == 1:
        return f"Overall: {total_km} km across {len(summaries)} activities and {total_min} moving minutes. A productive little festival of exertion."
    return f"Overall: {total_km} km across {len(summaries)} activities and {total_min} moving minutes. Nicely done."


def roast_block(activities: list[dict[str, Any]], tone: str, spice: int) -> str:
    if not activities:
        if spice >= 3:
            return "No recent Strava activity. Elite dedication to stealth mode."
        if spice == 2:
            return "No recent Strava activity found. Either rest day, or you buried the evidence well."
        if spice == 1:
            return "No recent Strava activity found. Recovery day or suspiciously quiet behaviour."
        return "No recent Strava activity found. Rest counts too."
    summaries = [summarize_activity(a) for a in activities]
    lines = [roast_line(s, tone, spice) for s in summaries]
    if len(summaries) > 1:
        lines.append(overall_line(summaries, spice))
    return "\n".join(lines)


def main() -> int:
    args = build_parser().parse_args()
    token_file = Path(args.token_file).expanduser()
    tokens = load_tokens(token_file)
    tokens = refresh_tokens(tokens, token_file, args.client_id, args.client_secret)
    activities = fetch_activities(tokens, args.days, args.limit)
    summaries = [summarize_activity(a) for a in activities]

    if args.command == 'summary':
        payload: Any = {"activity_count": len(summaries), "activities": summaries}
    else:
        payload = {
            "activity_count": len(summaries),
            "tone": args.tone,
            "spice": args.spice,
            "roast": roast_block(activities, args.tone, args.spice),
        }

    if args.json:
        print(json.dumps(payload, indent=2 if args.pretty else None))
    else:
        print(payload["roast"] if args.command == 'roast' else json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
