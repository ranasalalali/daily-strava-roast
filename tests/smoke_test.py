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
    payload = sr.build_daily_payload(activities)
    assert payload['activity_count'] == 2
    assert payload['days'][0]['rollup']['count'] == 2

    roast = sr.roast_day(payload['days'][0]['rollup'], 'playful', 2)
    assert 'Lunch Run' in roast or 'Evening Tennis' in roast
    assert 'disciplined little carnival of exertion' in roast

    print('smoke test passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
