#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.parse
import urllib.request
from collections import defaultdict
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
    p.add_argument("--limit", type=int, default=6, help="Max activities to fetch")
    p.add_argument("--tone", choices=["dry", "playful", "savage", "coach"], default="playful")
    p.add_argument("--spice", type=int, choices=[0, 1, 2, 3], default=1, help="Roast intensity from 0 (gentle) to 3 (scorched)")
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
        "elapsed_min": minutes(a.get("elapsed_time")),
        "elev_m": round(a.get("total_elevation_gain") or 0),
        "kudos": a.get("kudos_count") or 0,
        "achievements": a.get("achievement_count") or 0,
        "avg_hr": round(a.get("average_heartrate") or 0) or None,
        "avg_watts": round(a.get("average_watts") or 0) or None,
        "suffer": a.get("suffer_score"),
        "date_local": a.get("start_date_local"),
        "timezone": a.get("timezone"),
        "trainer": bool(a.get("trainer")),
        "city": a.get("location_city"),
        "state": a.get("location_state"),
        "country": a.get("location_country"),
    }


def date_key(summary: dict[str, Any]) -> str:
    return (summary.get("date_local") or "")[:10]


def join_names(items: list[str]) -> str:
    items = [i for i in items if i]
    if not items:
        return "nothing in particular"
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def aggregate_day(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    names = [s['name'] for s in summaries]
    sports = [s['sport'] for s in summaries]
    total_km = round(sum(s['distance_km'] for s in summaries), 2)
    total_min = sum(s['moving_min'] for s in summaries)
    total_elev = sum(s['elev_m'] for s in summaries)
    total_kudos = sum(s['kudos'] for s in summaries)
    indoor_count = sum(1 for s in summaries if s['trainer'])
    tz = next((s['timezone'] for s in summaries if s.get('timezone')), None)
    place = next((", ".join([x for x in [s.get('city'), s.get('state'), s.get('country')] if x]) for s in summaries if any([s.get('city'), s.get('state'), s.get('country')])), None)
    return {
        "date": date_key(summaries[0]) if summaries else None,
        "count": len(summaries),
        "names": names,
        "sports": sports,
        "total_km": total_km,
        "total_min": total_min,
        "total_elev": total_elev,
        "total_kudos": total_kudos,
        "indoor_count": indoor_count,
        "timezone": tz,
        "place": place,
    }


def roast_day(day: dict[str, Any], tone: str, spice: int) -> str:
    names = join_names(day['names'])
    sports = join_names(day['sports'])
    intro = f"On {day['date']}, you somehow turned {names} into a full-day program of {sports.lower()}."
    if day['place']:
        intro = f"On {day['date']} in {day['place']}, you somehow turned {names} into a full-day program of {sports.lower()}."

    load = f" That came to {day['total_min']} moving minutes"
    if day['total_km'] > 0:
        load += f" and {day['total_km']} km"
    if day['total_elev'] > 0:
        load += f", plus {day['total_elev']} m of climbing"
    load += "."

    if tone == 'coach' or spice == 0:
        ending = f" Solid work overall. {day['total_kudos']} kudos suggests the public approves, even if your legs may still be reviewing the decision."
    elif spice == 1:
        ending = f" It was a nicely structured little block of voluntary fatigue, with {day['total_kudos']} kudos worth of outside encouragement."
    elif spice == 2:
        ending = f" In other words, a disciplined little carnival of exertion — organized enough to look healthy, deranged enough to stay interesting."
    else:
        ending = f" In other words, you built an impressively coherent schedule for self-inflicted wear and tear, then had the audacity to collect {day['total_kudos']} kudos for it."

    if day['indoor_count'] and day['count'] > 1:
        ending += " Bonus points for mixing outdoor ambition with indoor refusal to choose peace."

    return (intro + load + ending).strip()


def build_daily_payload(activities: list[dict[str, Any]]) -> dict[str, Any]:
    summaries = [summarize_activity(a) for a in activities]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for s in summaries:
        grouped[date_key(s)].append(s)
    days = []
    for key, items in sorted(grouped.items(), reverse=True):
        days.append({
            "date": key,
            "activities": items,
            "rollup": aggregate_day(items),
        })
    return {"activity_count": len(summaries), "days": days}


def main() -> int:
    args = build_parser().parse_args()
    token_file = Path(args.token_file).expanduser()
    tokens = load_tokens(token_file)
    tokens = refresh_tokens(tokens, token_file, args.client_id, args.client_secret)
    activities = fetch_activities(tokens, args.days, args.limit)
    daily = build_daily_payload(activities)

    if args.command == 'summary':
        payload: Any = daily
    else:
        latest_day = daily['days'][0]['rollup'] if daily['days'] else None
        roast = roast_day(latest_day, args.tone, args.spice) if latest_day else "No recent Strava activity found. Rest counts too."
        payload = {
            "activity_count": daily['activity_count'],
            "day_count": len(daily['days']),
            "tone": args.tone,
            "spice": args.spice,
            "roast": roast,
        }

    if args.json:
        print(json.dumps(payload, indent=2 if args.pretty else None))
    else:
        print(payload['roast'] if args.command == 'roast' else json.dumps(payload, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
