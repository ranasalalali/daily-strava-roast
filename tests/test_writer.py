#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str((ROOT / 'src').resolve()))

from daily_strava_roast.prompt_builder import build_roast_prompt
from daily_strava_roast.writer import write_roast_preview


def test_preview_multi_activity() -> None:
    context = {
        'date': '2026-03-27',
        'activity_count': 2,
        'sports': ['tennis', 'run'],
        'dominant_sport': 'tennis',
        'activity_names': ['Evening Tennis', 'Lunch Run'],
        'totals': {
            'distance_km': 13.65,
            'moving_minutes': 98,
            'elevation_m': 84,
            'kudos': 10,
        },
        'effort': {
            'avg_hr': 141,
            'max_hr': None,
        },
        'pattern_hints': {
            'indoor_count': 0,
            'repeat_sport_recently': True,
        },
        'style': {
            'tone': 'playful',
            'spice': 3,
        },
    }
    prompt = build_roast_prompt(context)
    text = write_roast_preview(context, prompt)
    assert '13.65 km' in text
    assert '98 moving minutes' in text
    assert '10 kudos' in text
    assert '\n' not in text


def test_preview_no_activity() -> None:
    context = {
        'date': '2026-03-27',
        'activity_count': 0,
        'sports': [],
        'dominant_sport': None,
        'activity_names': [],
        'totals': {
            'distance_km': 0,
            'moving_minutes': 0,
            'elevation_m': 0,
            'kudos': 0,
        },
        'effort': {
            'avg_hr': None,
            'max_hr': None,
        },
        'pattern_hints': {
            'indoor_count': 0,
            'repeat_sport_recently': False,
        },
        'style': {
            'tone': 'dry',
            'spice': 2,
        },
    }
    prompt = build_roast_prompt(context)
    text = write_roast_preview(context, prompt)
    assert 'No Strava activity today' in text
    assert 'rest day' in text.lower()


def main() -> int:
    test_preview_multi_activity()
    test_preview_no_activity()
    print('writer test passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
