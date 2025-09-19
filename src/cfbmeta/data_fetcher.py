"""Utilities to load the ESPN college football scoreboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import json
from urllib import request, parse

SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"


class ScoreboardLoadError(RuntimeError):
    """Raised when a scoreboard cannot be loaded."""


def load_scoreboard(date: Optional[str] = None, scoreboard_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads a scoreboard either from disk or via the ESPN API.

    Args:
        date: Optional YYYYMMDD date string. Required when fetching from the network.
        scoreboard_path: Optional path to a JSON file to load instead of fetching.

    Returns:
        Parsed JSON dictionary containing scoreboard data.
    """

    if scoreboard_path:
        return _load_from_path(scoreboard_path)

    params = {"limit": "300"}
    if date:
        params["dates"] = date
    url = SCOREBOARD_URL + "?" + parse.urlencode(params)
    try:
        with request.urlopen(url, timeout=10) as response:  # pragma: no cover - network
            data = response.read().decode("utf-8")
    except Exception as exc:  # pragma: no cover - network errors
        raise ScoreboardLoadError("Unable to fetch scoreboard") from exc

    return json.loads(data)


def _load_from_path(path: str) -> Dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise ScoreboardLoadError(f"Scoreboard file not found: {path}")
    return json.loads(file_path.read_text(encoding="utf-8"))
