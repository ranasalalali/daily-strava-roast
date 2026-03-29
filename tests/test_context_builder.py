#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str((ROOT / 'src').resolve()))

from daily_strava_roast.context_builder import build_roast_context


def main() -> int:
    activities = json.loads((ROOT / 'tests' / 'fixtures' / 'sample_activities.json').read_text())
    summaries = [
        {
            'name': a['name'],
            'sport': a['sport_type'],
            'distance_km': round(a['distance'] / 1000.0, 2),
            'moving_min': round(a['moving_time'] / 60),
            'elev_m': round(a['total_elevation_gain']),
            'kudos': a['kudos_count'],
            'avg_hr': round(a['average_heartrate']) if a.get('average_heartrate') else None,
            'max_hr': None,
            'trainer': bool(a.get('trainer')),
        }
        for a in activities
    ]
    day = {
        'date': '2026-03-27',
        'count': 2,
        'sports': ['Run', 'Tennis'],
        'names': ['Lunch Run', 'Evening Tennis'],
        'total_km': 13.65,
        'total_min': 98,
        'total_elev': 84,
        'total_kudos': 10,
        'indoor_count': 0,
        'summaries': summaries,
    }
    state = {'recent': [{'sports': ['Run']}]}
    ctx = build_roast_context(day, 'playful', 3, state)
    assert ctx['activity_count'] == 2
    assert ctx['dominant_sport'] in {'run', 'tennis'}
    assert ctx['totals']['distance_km'] == 13.65
    assert ctx['pattern_hints']['repeat_sport_recently'] is True
    assert 'recent_families' in ctx['roast_memory']
    print('context builder test passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
