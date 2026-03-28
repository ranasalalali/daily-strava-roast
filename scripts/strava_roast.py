#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.parse
import urllib.request
import zlib
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


def title_roast(day: dict[str, Any], spice: int, idx: int) -> str | None:
    if not day['names']:
        return None
    name = day['names'][0]
    lowered = name.lower()
    generic_titles = ['morning ride', 'lunch run', 'evening tennis', 'evening weight training', 'morning run', 'evening run']
    if lowered in generic_titles:
        variants = [
            f"Calling it *{name}* has the gloriously plain energy of naming a folder 'new folder'.",
            f"The title *{name}* is admirably direct, if not exactly drunk on imagination.",
            f"*{name}* is such an honest title it feels less written than filed.",
            f"There is something almost moving about how little decorative effort went into the title *{name}*.",
        ]
        return variants[idx % len(variants)] if spice >= 1 else variants[1]
    if len(name.split()) <= 2 and spice >= 3:
        return f"*{name}* is such a blunt title it feels less like creativity and more like a witness statement."
    return None


def pattern_index(day: dict[str, Any], tone: str, spice: int) -> int:
    seed = f"{day.get('date')}|{','.join(day.get('names', []))}|{tone}|{spice}|{day.get('count')}"
    return zlib.crc32(seed.encode())


def single_activity_opener(day: dict[str, Any], spice: int, idx: int) -> str:
    first = day['summaries'][0]
    sport = first['sport'].lower()
    name = first['name']
    if 'ride' in sport or 'cycle' in sport:
        variants = [
            f"You opened the day with *{name}*, which is a very committed way to spend your free will.",
            f"Apparently the day's opening argument was *{name}*, because moderation once again failed to make the guest list.",
            f"You decided *{name}* was how this day should begin, which says a lot about your relationship with optional suffering.",
            f"*{name}* was your idea of a normal start to the day, which is already a fairly revealing character note.",
            f"There are easier ways to begin a day than *{name}*, but apparently ease was never central to the plan.",
        ]
        return variants[idx % len(variants)]
    if 'run' in sport:
        variants = [
            f"You turned *{name}* into a very public little argument with your own legs.",
            f"You called it *{name}*, then went out for the sort of effort that makes that title sound suspiciously understated.",
            f"Somewhere along the line, *{name}* became your chosen form of cardio diplomacy.",
            f"*{name}* sounds harmless on paper, which is a charming lie to tell yourself before a run.",
        ]
        return variants[idx % len(variants)]
    if 'tennis' in sport:
        variants = [
            f"You dedicated part of the day to *{name}*, which is just cardio dressed up as a civilized hobby.",
            f"*{name}* was apparently the plan, because simple rest would clearly have been too tasteful.",
            f"You went with *{name}*, proving once again that tennis is just respectable-looking chaos.",
            f"*{name}* sounds elegant, which is one of tennis' better disguises for all the sprinting.",
        ]
        return variants[idx % len(variants)]
    if 'weight' in sport or first['trainer']:
        variants = [
            f"You made time for *{name}*, which means even indoors you still found a way to negotiate with suffering.",
            f"*{name}* was the chosen activity, because peace and quiet were evidently never serious candidates.",
            f"You spent part of the day on *{name}*, which is a polite way of saying you went inside to manufacture consequences.",
            f"*{name}* is what happened when you looked at a perfectly normal day and decided it needed iron in the story.",
        ]
        return variants[idx % len(variants)]
    return f"You made a whole event out of *{name}*, which feels on brand."


def multi_activity_opener(day: dict[str, Any], idx: int) -> str:
    phrases = [sport_phrase(s['sport']) for s in day['summaries']]
    variants = [
        f"You somehow turned the day into {join_names(phrases)},",
        f"At some point this became a day featuring {join_names(phrases)},",
        f"You managed to stack {join_names(phrases)},",
        f"What started as a normal day somehow collected {join_names(phrases)},",
    ]
    return variants[idx % len(variants)]


def chaos_line(day: dict[str, Any], spice: int, idx: int) -> str:
    if day['indoor_count'] and day['count'] > 1:
        variants = [
            "Between the outdoor ambition and indoor iron diplomacy, it was a full day of disciplined chaos.",
            "Between the fresh air and the indoor consequences, you built a strangely balanced day of exertion.",
            "It had everything: outdoor optimism, indoor stubbornness, and a complete disregard for sitting still.",
        ]
        return variants[idx % len(variants)]
    if day['count'] >= 3:
        variants = [
            "It was a full day of disciplined chaos, which is a very elegant way of telling your legs they don't get voting rights.",
            "By the end of it, the whole day had the energy of a well-organized mutiny against comfort.",
            "Taken together, it looked less like a schedule and more like a carefully managed argument with fatigue.",
        ]
        return variants[idx % len(variants)]
    if day['count'] == 2:
        variants = [
            "A tidy little two-part program of exertion, because apparently one bout of fatigue wasn't enough to make the point.",
            "A neat double feature of movement, effort, and highly questionable respect for recovery.",
            "Just enough variety to feel balanced, and just enough volume to feel mildly vindictive.",
        ]
        return variants[idx % len(variants)]
    if spice >= 2:
        variants = [
            "A compact but committed burst of self-inflicted difficulty, because moderation clearly wasn't getting a vote.",
            "Not a huge day on paper, but more than enough to remind the body who's making the bad decisions here.",
            "A small but pointed contribution to the ongoing project of making fatigue feel deserved.",
        ]
        return variants[idx % len(variants)]
    variants = [
        "A respectable little dose of voluntary suffering.",
        "A tidy bit of effort, lightly seasoned with unnecessary ambition.",
        "Nothing outrageous — just a calm, competent flirtation with discomfort.",
    ]
    return variants[idx % len(variants)]


def social_line(day: dict[str, Any], spice: int, idx: int = 0) -> str:
    kudos = day['best_kudos']
    top = day['top_named']
    if not kudos:
        variants = [
            "The public has wisely chosen not to encourage this further.",
            "Mercifully, nobody has rushed in to validate the behaviour yet.",
            "No kudos, which may be the closest thing to responsible adult supervision available here.",
        ]
        return variants[idx % len(variants)]
    if spice >= 2:
        variants = [
            f"{kudos} kudos suggests people support the behaviour; whether they should is another matter.",
            f"The {kudos} kudos imply a surprising amount of public enthusiasm for this kind of thing.",
            f"{kudos} people looked at this and thought, yes, let's encourage this further. Disturbing, but touching.",
            f"Somehow this picked up {kudos} kudos, so the public remains fully complicit.",
        ]
        return variants[idx % len(variants)]
    variants = [
        f"{kudos} kudos suggests the behaviour has, somehow, public backing.",
        f"The {kudos} kudos indicate that other people are willing to reward this kind of effort.",
        f"Apparently that earned {kudos} kudos, so the public remains broadly supportive of your nonsense.",
        f"That drew {kudos} kudos, which is really just community-enabled behaviour at this point.",
    ]
    return variants[idx % len(variants)]


def roast_day(day: dict[str, Any], tone: str, spice: int) -> str:
    if not day:
        return "No recent Strava activity found. A bold commitment to mystery."

    idx = pattern_index(day, tone, spice)
    title_bit = title_roast(day, spice, idx)
    social = social_line(day, spice, idx)

    if day['count'] == 1:
        opener = single_activity_opener(day, spice, idx)
        chaos = chaos_line(day, spice, idx)
        if tone == 'coach' or spice == 0:
            return f"{opener} Solid work overall. {social}"
        if tone == 'dry':
            dry_bits = [
                f"{opener} {social}",
                f"{title_bit} {opener} {social}" if title_bit else f"{opener} {social}",
                f"{opener} {chaos} {social}",
            ]
            return dry_bits[idx % len(dry_bits)]
        variants = [
            [opener, chaos, social],
            [title_bit, opener, social] if title_bit else [social, opener, chaos],
            [opener, social, chaos],
            [chaos, opener, social],
            [social, opener, title_bit] if title_bit else [social, chaos, opener],
        ]
        parts = variants[idx % len(variants)]
        return ' '.join([p for p in parts if p])

    opener = multi_activity_opener(day, idx)
    chaos = chaos_line(day, spice, idx)
    if tone == 'coach' or spice == 0:
        return f"{opener} you put together a solid day of training without completely losing the plot. {social}"
    if tone == 'dry':
        return f"{opener} you logged {day['count']} activities and {day['total_min']} moving minutes, which is a very efficient way to remain tired. {social}"
    variants = [
        [opener, chaos, social],
        [social, opener, chaos],
        [opener, social, chaos],
        [chaos, opener, social],
    ]
    parts = variants[idx % len(variants)]
    return ' '.join([p for p in parts if p])


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
