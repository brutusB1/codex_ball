from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOREBOARD = PROJECT_ROOT / "tests" / "data" / "espn_scoreboard_sample.json"


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": "src"}
    return subprocess.run(
        [sys.executable, "-m", "cfbmeta.cli", *args],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env=env,
    )


def test_cli_json_output_includes_metadata() -> None:
    result = _run_cli([
        "--scoreboard",
        str(SCOREBOARD),
        "--top",
        "2",
        "--format",
        "json",
    ])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "games" in payload
    assert payload["games"], "Expected at least one game in JSON payload"
    first = payload["games"][0]
    for field in ("interest", "broadcasts", "summary"):
        assert field in first
    assert "is_favorite" in first


def test_cli_favorite_survives_live_filter() -> None:
    result = _run_cli([
        "--scoreboard",
        str(SCOREBOARD),
        "--only-live",
        "--top",
        "3",
        "--favorites",
        "NAVY",
    ])
    assert result.returncode == 0, result.stderr
    assert "★ NAVY 24 @ AF 27" in result.stdout
