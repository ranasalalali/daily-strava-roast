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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_TOKEN_FILE = Path.home() / ".openclaw" / "workspace" / "agents" / "tars-fit" / "strava_tokens.json"
DEFAULT_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "216808")
DEFAULT_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
DEFAULT_STATE_FILE = Path.home() / '.openclaw' / 'workspace' / 'daily-strava-roast' / 'state' / 'recent_roasts.json'


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate a daily Strava roast from recent activity.")
    p.add_argument("command", choices=["summary", "roast"], nargs="?", default="roast")
    p.add_argument("--token-file", default=str(DEFAULT_TOKEN_FILE), help="Path to strava token JSON")
    p.add_argument("--client-id", default=DEFAULT_CLIENT_ID)
    p.add_argument("--client-secret", default=DEFAULT_CLIENT_SECRET)
    p.add_argument("--days", type=int, default=2, help="Look back N days for recent activity")
    p.add_argument("--limit", type=int, default=6, help="Max activities to fetch")
    p.add_argument("--lookback-limit", type=int, default=30, help="How many activities to scan when looking for the last recorded activity")
    p.add_argument("--tone", choices=["dry", "playful", "savage", "coach"], default="playful")
    p.add_argument("--spice", type=int, choices=[0, 1, 2, 3], default=3, help="Roast intensity from 0 (gentle) to 3 (scorched)")
    p.add_argument("--state-file", default=str(DEFAULT_STATE_FILE), help="Path to roast memory state file")
    p.add_argument("--json", action="store_true")
    p.add_argument("--pretty", action="store_true")
    p.add_argument("--variation-seed", default=None, help="Optional seed to vary roast selection")
    return p


def load_tokens(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def save_tokens(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"recent": []}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {"recent": []}



def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n")



def remember_roast(path: Path, state: dict[str, Any], entry: dict[str, Any]) -> None:
    recent = state.get("recent", [])
    recent.append(entry)
    state["recent"] = recent[-10:]
    save_state(path, state)



def recent_sports_context(state: dict[str, Any]) -> list[str]:
    sports = []
    for item in state.get("recent", []):
        sports.extend(item.get("sports", []))
    return sports[-20:]


def refresh_tokens(tokens: dict[str, Any], path: Path, client_id: str, client_secret: str | None) -> dict[str, Any]:
    if tokens.get("expires_at", 0) > int(time.time()) + 300:
        return tokens
    if not client_secret:
        raise RuntimeError(
            "Strava access token is expired or near expiry, but STRAVA_CLIENT_SECRET is not set. "
            "Set STRAVA_CLIENT_SECRET so the tool can refresh tokens by default."
        )
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


def fetch_recent_activity(tokens: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode({"per_page": limit, "page": 1})
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
        "max_hr": round(a.get("max_heartrate") or 0) or None,
        "avg_watts": round(a.get("average_watts") or 0) or None,
        "suffer": a.get("suffer_score"),
        "date_local": a.get("start_date_local"),
        "timezone": a.get("timezone"),
        "trainer": bool(a.get("trainer")),
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


def pattern_index(day: dict[str, Any], tone: str, spice: int, variation_seed: str | None = None) -> int:
    seed = f"{day.get('date')}|{','.join(day.get('names', []))}|{tone}|{spice}|{day.get('count')}"
    if variation_seed:
        seed += f"|{variation_seed}"
    return zlib.crc32(seed.encode())


def sport_label(sport: str) -> str:
    s = sport.lower()
    if 'run' in s:
        return 'a run'
    if 'ride' in s or 'cycle' in s:
        return 'a ride'
    if 'tennis' in s:
        return 'some tennis'
    if 'weight' in s:
        return 'some weight training'
    return s


def social_sentence(day: dict[str, Any], spice: int, idx: int) -> str:
    kudos = day['best_kudos']
    if not kudos:
        variants = [
            "Nobody has rushed in to validate the behaviour, which may be the healthiest part of the whole story.",
            "No kudos showed up, leaving the public technically innocent.",
            "Mercifully, nobody decided this needed encouragement."
        ]
        return variants[idx % len(variants)]
    if spice >= 2:
        variants = [
            f"{kudos} kudos suggests people are willing to encourage this sort of behaviour, which feels supportive in the way feeding a gremlin after midnight is supportive.",
            f"The {kudos} kudos imply a surprising amount of public support for what was, at minimum, an aggressively optional amount of effort.",
            f"Somehow this still collected {kudos} kudos, so the public remains fully complicit."
        ]
        return variants[idx % len(variants)]
    variants = [
        f"It still pulled in {kudos} kudos, so the public is broadly on board with your nonsense.",
        f"The {kudos} kudos suggest this had more community support than it strictly needed.",
        f"Apparently {kudos} people saw this and approved, which is honestly quite sweet."
    ]
    return variants[idx % len(variants)]


def effort_sentence(day: dict[str, Any], spice: int, idx: int) -> str:
    count = day['count']
    total_min = day['total_min']
    total_km = day['total_km']
    total_elev = day['total_elev']
    if count == 1:
        bits = [f"{total_min} moving minutes"]
        if total_km > 0:
            bits.append(f"{total_km} km")
        if total_elev > 0:
            bits.append(f"{total_elev} m of climbing")
        joined = ', '.join(bits[:-1]) + (f", and {bits[-1]}" if len(bits) > 1 else bits[0])
        variants = [
            f"It wasn't an all-day epic, but {joined} still adds up to a fairly committed way to make your legs resent you.",
            f"By the end of it, you'd stacked up {joined}, which is plenty if your goal was to make fatigue feel earned.",
            f"That's {joined}, which is a neat amount of work for something that was presumably meant to fit into a normal day."
        ]
        return variants[idx % len(variants)]
    variants = [
        f"Taken together, it came to {count} activities and {total_min} moving minutes — basically a well-organized argument against sitting still.",
        f"All together, you turned the day into {count} activities and {total_min} moving minutes of carefully scheduled inconvenience.",
        f"By the time it was over, you'd piled up {count} activities and {total_min} moving minutes, which is a tidy little festival of exertion."
    ]
    return variants[idx % len(variants)]


def opener_sentence(day: dict[str, Any], idx: int) -> str:
    if day['count'] == 1:
        first = day['summaries'][0]
        sport = sport_label(first['sport'])
        variants = {
            'ride': [
                "You opened the day with a ride, which is a very committed way to spend your free will.",
                "Apparently a ride was how this day was going to begin, because moderation once again failed to make the guest list.",
                "You started with a ride, which is a nice healthy habit if you ignore the part where it keeps making you tired."
            ],
            'run': [
                "You somehow turned part of the day into a run, which remains one of the more honest ways to suffer in public.",
                "You decided a run belonged in the schedule, because peace and quiet were clearly never serious contenders.",
                "A run made it onto the agenda, which is always a bold way to announce that comfort can wait."
            ],
            'tennis': [
                "You devoted part of the day to tennis, which is cardio wearing a blazer and pretending to be civilized.",
                "Tennis made the schedule, because apparently regular exercise wasn't quite theatrical enough.",
                "You found time for tennis, which is a charming way to disguise repeated sprinting as leisure."
            ],
            'weight training': [
                "You carved out time for weight training, because even indoors you apparently still like negotiating with gravity.",
                "Weight training entered the picture, which is what happens when a normal day needs more consequences.",
                "You went for weight training, because simply existing in peace was never really the plan."
            ],
        }
        choices = variants.get(sport, ["You managed to make exercise part of the day again, which feels consistent if not always wise."]); return choices[idx % len(choices)]

    sport_mix = join_names([sport_label(s) for s in day['sports']])
    variants = [
        f"You somehow turned the day into {sport_mix}, which is a fairly bold way to avoid being accused of taking it easy.",
        f"At some point the schedule collected {sport_mix}, and from there the day had no real chance of staying normal.",
        f"What started as an ordinary day ended up featuring {sport_mix}, which feels ambitious in a way your body probably noticed."
    ]
    return variants[idx % len(variants)]


def hr_sentence(day: dict[str, Any], idx: int) -> str | None:
    first = day['summaries'][0] if day['summaries'] else None
    if not first:
        return None
    avg_hr = first.get('avg_hr')
    max_hr = first.get('max_heartrate') or first.get('max_hr')
    sport = sport_label(first['sport'])
    if not max_hr:
        return None
    if max_hr >= 185:
        variants = [
            f"The max heart rate peaking at {max_hr} suggests you did, at some point, stop pretending this was casual.",
            f"A max heart rate of {max_hr} is a nice little reminder that you were, briefly, very much involved in your own suffering.",
            f"Topping out at {max_hr} bpm does imply you visited the upper floors of your effort range, so points for commitment."
        ]
        return variants[idx % len(variants)]
    if max_hr <= 150 and sport in {'a run', 'a ride'}:
        variants = [
            f"The heart rate stayed civilised enough that the session reads as controlled rather than chaotic, which is almost suspiciously mature.",
            f"For something like this, a max heart rate of {max_hr} suggests you either paced beautifully or never fully signed the emotional consent form.",
            f"The max heart rate never got especially theatrical, which may mean discipline — or unfinished business."
        ]
        return variants[idx % len(variants)]
    return None



def kicker_sentence(day: dict[str, Any], spice: int, idx: int, state: dict[str, Any] | None = None) -> str:
    recent_sports = recent_sports_context(state or {})
    repeated = any(s in recent_sports for s in day['sports'])
    hr = hr_sentence(day, idx)
    if hr and idx % 3 == 0:
        return hr
    if day['indoor_count'] and day['count'] > 1:
        variants = [
            "It had a pleasing mix of outdoor optimism and indoor refusal to choose peace.",
            "Between the fresh air and the indoor consequences, the whole thing somehow felt almost balanced.",
            "It was a nice blend of outside ambition and inside stubbornness, which is very on brand."
        ]
        return variants[idx % len(variants)]
    if repeated and spice >= 2:
        variants = [
            "Also, this is starting to look less like variety and more like a recurring character trait.",
            "At this point the pattern is becoming part of the lore.",
            "There is now enough repetition here to call it a theme, not an accident."
        ]
        return variants[idx % len(variants)]
    if spice >= 2:
        variants = [
            "Disciplined, productive, and just unhinged enough to stay interesting.",
            "Respectable on paper, faintly unhinged in practice — exactly where the fun lives.",
            "Solid work, though still just chaotic enough to keep your better judgment unemployed."
        ]
        return variants[idx % len(variants)]
    variants = [
        "All in all, a pretty decent little block of effort.",
        "Taken together, it was annoyingly competent.",
        "As these things go, it was a good day to be unnecessarily active."
    ]
    return variants[idx % len(variants)]


def days_since(date_str: str | None) -> int | None:
    if not date_str:
        return None
    try:
        ts = time.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
        then = int(time.mktime(ts))
        return max(0, int((time.time() - then) // 86400))
    except Exception:
        return None



def no_activity_roast(tone: str, spice: int, last_activity: dict[str, Any] | None = None) -> str:
    gap = days_since(last_activity.get('start_date_local')) if last_activity else None

    if gap is not None and gap >= 180:
        variants = [
            f"No activity today, and your last logged effort was {gap} days ago. At this point the training block hasn't gone quiet so much as slipped into folklore. If you came back tomorrow, even your own activity feed might react like it had seen a ghost.",
            f"Still nothing today. The last Strava entry was {gap} days ago, which means your fitness narrative is now mostly oral tradition. We're well beyond recovery here; this is the sort of gap that makes old workouts sound mythological.",
            f"No activity today. Your last recorded workout was {gap} days ago, so this has drifted clean past rest and into archaeology. Somewhere in the distance, your previous consistency is being discussed like a lost civilization.",
        ]
        return variants[(gap + spice) % len(variants)]

    if gap is not None and gap >= 90:
        variants = [
            f"No activity today, and the last one was {gap} days ago. We're no longer in a quiet patch; we're in excavation season. At this point Strava is less waiting for your return and more preserving the site.",
            f"Still quiet today. After {gap} days without a log, this has started to feel less like training and more like archive research. The feed isn't stale so much as historically significant.",
            f"Nothing today, and the last workout was {gap} days ago. Even the motivation is probably covered in dust by now. This isn't a pause; it's a museum wing.",
        ]
        return variants[(gap + spice) % len(variants)]

    if gap is not None and gap >= 30:
        variants = [
            f"No activity today, and the last one was {gap} days ago. This is starting to feel less like a rest block and more like witness protection for cardio. At some point even your training plan is going to stop texting first.",
            f"Still quiet today. After {gap} days without a log, even Strava seems unsure whether to wait or move on. We're now well into the kind of silence that starts to develop personality.",
            f"Nothing today, and the last workout was {gap} days ago. The storyline hasn't ended, but it has definitely wandered off between seasons. If this is still a plan, it's become a very abstract one.",
        ]
        return variants[(gap + spice) % len(variants)]

    if gap is not None and gap >= 14:
        variants = [
            f"No activity today, and it's been {gap} days since the last log. At this point 'rest day' is being asked to do some heroic work. We're edging into the kind of absence that starts needing an explanation, or at least a decent excuse.",
            f"Still nothing today. With a {gap}-day gap, this has graduated from recovery into a proper little disappearance. Not a crisis yet, but certainly enough silence for the training plan to feel snubbed.",
            f"Nothing on Strava today, and the last activity was {gap} days ago. That is no longer a pause; it's a storyline choice. A bold one, too, considering your previous enthusiasm for avoidable exertion.",
        ]
        return variants[(gap + spice) % len(variants)]

    if gap is not None and gap >= 7:
        variants = [
            f"No activity today, and it's been {gap} days since the last one. That's no longer a blip; that's the beginning of a minor disappearance. We are now comfortably beyond 'busy week' territory and into something much more narratively interesting.",
            f"Still quiet today. A {gap}-day gap is long enough for the training plan to start feeling ghosted. Not dramatic enough for concern, perhaps, but absolutely enough for a raised eyebrow and a pointed little cough.",
            f"Nothing logged today, and the last activity was {gap} days ago. This is the kind of silence that starts out as recovery and slowly acquires the energy of avoidance. Charming, but suspicious.",
        ]
        return variants[(gap + spice) % len(variants)]

    if gap is not None and gap >= 3:
        variants = [
            f"No activity today, and it's been {gap} days since the last one. Not alarming, just enough to make things mildly suspicious. The body may call it recovery; the narrative calls it a noticeable pause.",
            f"Still quiet today. A {gap}-day gap is perfectly legal, though not especially convincing. We're not in disappearance territory yet, but we are absolutely lingering near the edge of it.",
            f"Nothing logged today, and the last effort was {gap} days ago. We may be drifting from recovery into creative interpretation, which is always an interesting stage of the process.",
        ]
        return variants[(gap + spice) % len(variants)]

    if tone == 'coach' or spice == 0:
        variants = [
            "No Strava activity today. Recovery counts, even when it is less entertaining. Sensible work isn't always visible, but it does still count.",
            "Nothing logged today. Rest is valid, even if it leaves the roast with less material. Not every good training day needs to be loud.",
            "Quiet day on Strava. Sensible, restorative, and slightly inconvenient for the content pipeline. Your legs are probably grateful, even if they remain poor conversationalists.",
        ]
        return variants[spice % len(variants)]
    if spice >= 2:
        variants = [
            "No Strava activity today. Either you rested like a professional or simply left no witnesses. Hard to say which, but the silence is doing a lot of work.",
            "Quiet day on Strava. Recovery is valid; disappearing completely is just dramatic. Still, you have to respect the commitment to keeping the feed suspiciously tidy.",
            "Nothing logged today. Very mature, very restful, very suspicious. The joints are relieved, the timeline is not.",
            "No activity today. Your joints are thrilled, even if the roast economy is not. Somewhere inside your body, something is quietly sending a thank-you note.",
        ]
        return variants[spice % len(variants)]
    variants = [
        "No Strava activity today. Rest day, stealth day, or admin day — all plausible. Not every plotline needs a training montage.",
        "Nothing logged today. Maybe recovery, maybe mystery, maybe both. Either way, the day seems to have happened mostly off-camera.",
        "Quiet day on Strava. A rare appearance from moderation, or at least something wearing its clothes. Fair enough, honestly.",
    ]
    return variants[spice % len(variants)]


def roast_day(day: dict[str, Any], tone: str, spice: int, state: dict[str, Any] | None = None, variation_seed: str | None = None) -> str:
    if not day:
        return no_activity_roast(tone, spice)

    recent = state.get('recent', []) if state else []
    variation_base = variation_seed or f"run-{len(recent)}"
    idx = pattern_index(day, tone, spice, variation_base)
    opener = opener_sentence(day, idx)
    effort = effort_sentence(day, spice, idx)
    social = social_sentence(day, spice, idx)
    kicker = kicker_sentence(day, spice, idx, state)

    if tone == 'coach' or spice == 0:
        return f"{opener} {effort} {social}"

    if tone == 'dry':
        patterns = [
            f"{opener} {effort} {social}",
            f"{effort} {opener} {social}",
            f"{opener} {social} {kicker}",
        ]
        return patterns[idx % len(patterns)]

    patterns = [
        f"{opener} {effort} {social}",
        f"{social} {opener} {kicker}",
        f"{opener} {kicker} {social}",
        f"{effort} {social} {kicker}",
    ]
    return patterns[idx % len(patterns)]


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
        if latest_day:
            state = load_state(Path(args.state_file).expanduser())
            roast = roast_day(latest_day, args.tone, args.spice, state, args.variation_seed)
            remember_roast(Path(args.state_file).expanduser(), state, {
                'at': datetime.now(timezone.utc).isoformat(),
                'date': latest_day.get('date'),
                'sports': latest_day.get('sports', []),
                'count': latest_day.get('count'),
                'tone': args.tone,
                'spice': args.spice,
                'roast': roast,
            })
        else:
            recent = fetch_recent_activity(tokens, args.lookback_limit)
            roast = no_activity_roast(args.tone, args.spice, recent[0] if recent else None)
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
