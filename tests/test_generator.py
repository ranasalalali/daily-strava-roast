#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str((ROOT / 'src').resolve()))

from daily_strava_roast.generator import (
    GenerationFailedError,
    GenerationUnavailableError,
    generate_roast_paragraph,
)


def test_missing_runner() -> None:
    try:
        generate_roast_paragraph({}, 'hello', runner=None, model='demo')
    except GenerationUnavailableError as exc:
        assert 'No model runner configured' in str(exc)
    else:
        raise AssertionError('expected GenerationUnavailableError')


def test_missing_model() -> None:
    try:
        generate_roast_paragraph({}, 'hello', runner='cat', model=None)
    except GenerationUnavailableError as exc:
        assert 'No model name configured' in str(exc)
    else:
        raise AssertionError('expected GenerationUnavailableError')


def test_successful_generation() -> None:
    text = generate_roast_paragraph({}, 'hello world', runner='cat', model='/dev/stdin')
    assert text == 'hello world'


def test_runner_failure() -> None:
    try:
        generate_roast_paragraph({}, 'hello', runner='false', model='ignored')
    except GenerationFailedError:
        return
    raise AssertionError('expected GenerationFailedError')


def main() -> int:
    test_missing_runner()
    test_missing_model()
    test_successful_generation()
    test_runner_failure()
    print('generator test passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
