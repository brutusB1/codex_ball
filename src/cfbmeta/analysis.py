"""Scoring and formatting logic for the meta guide."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Iterable, List, Sequence

from .models import Game


def interest_score(game: Game, now: datetime | None = None) -> float:
    """Computes a heuristic score describing how watchable a game is."""

    score = 0.0
    if game.home.rank or game.away.rank:
        ranked_bonus = 5.0
        if game.home.rank and game.away.rank:
            ranked_bonus += 5.0
        score += ranked_bonus

    if game.is_live:
        score += 40.0
        if game.period >= 3:
            score += 15.0
            score += max(0.0, 20.0 - 2.5 * game.score_margin)
        else:
            score += max(0.0, 8.0 - 1.0 * game.score_margin)
        score += _pace_bonus(game)
    elif game.is_final:
        score += 5.0  # recaps for finished thrillers
        score += max(0.0, 20.0 - 2.5 * game.score_margin)
    else:
        score += 2.0  # future games

    if now is None:
        now = datetime.now(timezone.utc)
    kickoff_delta = (game.start_time - now).total_seconds() / 3600.0
    if kickoff_delta > 0:
        score += max(0.0, 6.0 - kickoff_delta)  # near-future kickoffs
    elif -2.5 < kickoff_delta <= 0 and not game.is_live:
        score += 3.0  # recently completed

    return round(score, 2)


def _pace_bonus(game: Game) -> float:
    pace_lookup = {
        "0:00": 0.0,
        "0:01": 0.0,
    }
    if game.clock in pace_lookup:
        return pace_lookup[game.clock]
    if not game.clock:
        return 0.0
    try:
        minutes, seconds = map(int, game.clock.split(":"))
        total_seconds = minutes * 60 + seconds
    except ValueError:
        return 0.0
    if total_seconds < 120:
        return 8.0
    if total_seconds < 300:
        return 4.0
    return 0.0


def build_game_summary(game: Game, include_notes: bool = False) -> str:
    parts: List[str] = []
    teams = f"{game.away.abbreviation} {game.away.score} @ {game.home.abbreviation} {game.home.score}"
    parts.append(teams)
    status = game.status
    if game.is_live:
        status = f"Q{game.period} {game.clock}"
    parts.append(status)
    if game.broadcasts:
        parts.append("TV: " + ", ".join(game.broadcasts))
    if include_notes and game.notes:
        parts.extend(game.notes)
    return " | ".join(parts)


def summarize_games(games: Sequence[Game], include_notes: bool = False) -> List[dict]:
    return [
        {
            **asdict(game),
            "interest": interest_score(game),
            "summary": build_game_summary(game, include_notes=include_notes),
        }
        for game in games
    ]


def select_top_games(games: Iterable[Game], limit: int | None = None) -> List[Game]:
    ranked = sorted(games, key=interest_score, reverse=True)
    if limit is None:
        return ranked
    return ranked[:limit]
