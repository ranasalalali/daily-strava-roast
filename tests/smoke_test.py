#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

import strava_roast as sr  # type: ignore


def main() -> int:
    activities = json.loads((ROOT / 'tests' / 'fixtures' / 'sample_activities.json').read_text())
    roast = sr.roast_block(activities, 'playful', 1)
    assert 'Evening Tennis' in roast
    assert 'Lunch Run' in roast
    assert 'Overall:' in roast

    summary = [sr.summarize_activity(a) for a in activities]
    assert summary[0]['sport'] == 'Tennis'
    assert summary[1]['distance_km'] == 8.42

    empty = sr.roast_block([], 'dry', 1)
    assert 'No recent Strava activity' in empty

    print('smoke test passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
