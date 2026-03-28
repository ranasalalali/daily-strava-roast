from __future__ import annotations

import os
import subprocess
from typing import Any


DEFAULT_MODEL_RUNNER = os.getenv("DAILY_STRAVA_ROAST_MODEL_RUNNER")
DEFAULT_MODEL_NAME = os.getenv("DAILY_STRAVA_ROAST_MODEL")


class GenerationUnavailableError(RuntimeError):
    pass


class GenerationFailedError(RuntimeError):
    pass


def _clean_output(text: str) -> str:
    return " ".join(text.strip().split())


def generate_roast_paragraph(
    context: dict[str, Any],
    prompt: str,
    *,
    runner: str | None = None,
    model: str | None = None,
    timeout_seconds: int = 60,
) -> str:
    del context  # reserved for future non-prompt generation paths

    resolved_runner = runner or DEFAULT_MODEL_RUNNER
    resolved_model = model or DEFAULT_MODEL_NAME

    if not resolved_runner:
        raise GenerationUnavailableError(
            "No model runner configured. Set DAILY_STRAVA_ROAST_MODEL_RUNNER or pass --model-runner."
        )
    if not resolved_model:
        raise GenerationUnavailableError(
            "No model name configured. Set DAILY_STRAVA_ROAST_MODEL or pass --model."
        )

    try:
        result = subprocess.run(
            [resolved_runner, resolved_model],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GenerationUnavailableError(f"Model runner not found: {resolved_runner}") from exc
    except subprocess.TimeoutExpired as exc:
        raise GenerationFailedError(f"Model generation timed out after {timeout_seconds}s") from exc

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise GenerationFailedError(stderr or f"Model runner exited with code {result.returncode}")

    output = _clean_output(result.stdout)
    if not output:
        raise GenerationFailedError("Model runner returned empty output")
    return output
