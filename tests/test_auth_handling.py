#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str((ROOT / 'src').resolve()))

import daily_strava_roast.cli as cli


def main() -> int:
    auth_msg = cli.auth_unavailable_message(cli.StravaAuthError('Strava activity fetch failed with 401'))
    recovery_msg = cli.auth_unavailable_message(
        cli.StravaAuthError('Strava activity fetch failed with 401'),
        {'status': 'reauth_required', 'auth_url': 'https://example.com/auth'},
    )
    data_msg = cli.data_unavailable_message(cli.StravaDataUnavailableError('network timeout'))
    assert 'not a confirmed rest day' in auth_msg.lower()
    assert 'authentication failure' in auth_msg.lower()
    assert 'reauthorisation' in recovery_msg.lower()
    assert 'not a confirmed rest day' in data_msg.lower()
    assert cli.reauth_available(Path('/tmp/definitely-missing-script.py'), 'secret') is False
    print('auth handling test passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
