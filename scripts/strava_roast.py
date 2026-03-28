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
        "best_kudos": max((s['kudos'] for s in summaries), default=0),
        "top_named": max(summaries, key=lambda s: s['kudos'])['name'] if summaries else None,
        "summaries": summaries,
    }


def sport_phrase(sport: str) -> str:
    s = sport.lower()
    if 'run' in s:
        return 'a run'
    if 'tennis' in s:
        return 'tennis'
    if 'weight' in s:
        return 'a round of weight training'
    if 'ride' in s or 'cycle' in s:
        return 'a ride'
    return sport.lower()


def opening_phrase(day: dict[str, Any]) -> str:
    if day['count'] == 1:
        first = day['summaries'][0]
        sport = sport_phrase(first['sport'])
        name = first['name']
        if 'run' in first['sport'].lower() and first['distance_km'] > 0:
            return f"You somehow managed to turn {name.lower()} into a {first['distance_km']:.2f}K {sport[2:]},"
        return f"You somehow managed to turn {name.lower()} into {sport},"
    phrases = [sport_phrase(s['sport']) for s in day['summaries']]
    return f"You somehow managed to stack {join_names(phrases[:-1]) if len(phrases)>1 else phrases[0]}{' and ' + phrases[-1] if len(phrases)>1 else ''},"


def chaos_line(day: dict[str, Any], spice: int) -> str:
    if day['indoor_count'] and day['count'] > 1:
        return "Between the outdoor ambition and indoor iron diplomacy, it was a full day of disciplined chaos."
    if day['count'] >= 3:
        return "It was a full day of disciplined chaos, which is a very elegant way of telling your legs they don't get voting rights."
    if day['count'] == 2:
        return "A tidy little two-part program of exertion, because apparently one bout of fatigue wasn't enough to make the point."
    if spice >= 2:
        return "A compact but committed burst of self-inflicted difficulty."
    return "A respectable little dose of voluntary suffering."


def social_line(day: dict[str, Any], spice: int) -> str:
    kudos = day['best_kudos']
    top = day['top_named']
    if not kudos:
        return "The public has wisely chosen not to encourage this further."
    if spice >= 2:
        return f"{kudos} kudos on {top.lower()} suggests people support the behaviour; whether they should is another matter."
    return f"{kudos} kudos on {top.lower()} suggests the behaviour has, somehow, public backing."


def roast_day(day: dict[str, Any], tone: str, spice: int) -> str:
    if not day:
        return "No recent Strava activity found. A bold commitment to mystery."
    opener = opening_phrase(day)
    if tone == 'coach' or spice == 0:
        middle = "you put together a solid day of training without completely losing the plot."
        end = social_line(day, 0)
        return f"{opener} {middle} {end}"
    if tone == 'dry':
        middle = f"you logged {day['count']} activity{'ies' if day['count'] != 1 else ''} and {day['total_min']} moving minutes, which is a very efficient way to remain tired."
        end = social_line(day, spice)
        return f"{opener} {middle} {end}"
    middle = chaos_line(day, spice)
    end = social_line(day, spice)
    return f"{opener} {middle} {end}"


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
