#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str((ROOT / 'src').resolve()))

from daily_strava_roast.prompt_builder import build_roast_prompt


def main() -> int:
    context = {
        'date': '2026-03-27',
        'activity_count': 2,
        'sports': ['run', 'tennis'],
        'dominant_sport': 'run',
        'activity_names': ['Lunch Run', 'Evening Tennis'],
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
    assert 'Write exactly one short paragraph' in prompt
    assert '- sports: run, tennis' in prompt
    assert '- repeat_sport_recently: True' in prompt
    assert 'Avoid sounding like a dashboard' in prompt
    print('prompt builder test passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
