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


def roast_line(summary: dict[str, Any], tone: str) -> str:
    sport = summary['sport']
    name = summary['name']
    dist = summary['distance_km']
    mins = summary['moving_min']
    elev = summary['elev_m']
    kudos = summary['kudos']
    suffer = summary['suffer']
    avg_hr = summary['avg_hr']
    trainer = summary['trainer']

    if tone == 'dry':
        return f"{name}: {dist} km of {sport.lower()} in {mins} min. A very measured attempt at pretending this was all deliberate."
    if tone == 'savage':
        extra = f" {elev} m climbing just to make the poor decisions vertical." if elev else ""
        return f"{name}: {dist} km in {mins} min.{extra} {kudos} kudos for effort, none for restraint."
    if tone == 'coach':
        hr = f" Avg HR {avg_hr}." if avg_hr else ""
        suf = f" Suffer score {suffer}." if suffer else ""
        return f"{name}: {dist} km in {mins} min.{hr}{suf} Solid work — now try being as disciplined with recovery as you are with self-inflicted fatigue."
    if trainer:
        return f"{name}: indoor {sport.lower()} for {mins} min. Same room, same legs, same audacity."
    return f"{name}: {dist} km of {sport.lower()} in {mins} min with {kudos} kudos. Public evidence that cardio and questionable judgment can coexist beautifully."


def roast_block(activities: list[dict[str, Any]], tone: str) -> str:
    if not activities:
        if tone == 'savage':
            return "No recent Strava activity. Incredible commitment to stealth mode."
        if tone == 'coach':
            return "No recent Strava activity found. Recovery is valid; disappearing entirely is less convincing."
        return "No recent Strava activity found. Either you rested, or you committed your workout in witness protection."
    summaries = [summarize_activity(a) for a in activities]
    lines = [roast_line(s, tone) for s in summaries]
    if len(summaries) > 1:
        total_km = round(sum(s['distance_km'] for s in summaries), 2)
        total_min = sum(s['moving_min'] for s in summaries)
        lines.append(f"Overall: {total_km} km across {len(summaries)} activities and {total_min} moving minutes. A productive little festival of exertion.")
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
        payload = {"activity_count": len(summaries), "tone": args.tone, "roast": roast_block(activities, args.tone)}

    if args.json:
        print(json.dumps(payload, indent=2 if args.pretty else None))
    else:
        print(payload["roast"] if args.command == 'roast' else json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
