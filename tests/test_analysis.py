from __future__ import annotations

from datetime import datetime, timezone
import pytest

from cfbmeta.analysis import build_game_summary, interest_score, select_top_games
from cfbmeta.models import Game, parse_games
from cfbmeta.data_fetcher import load_scoreboard


@pytest.fixture(scope="module")
def sample_games() -> list[Game]:
    scoreboard = load_scoreboard(scoreboard_path="tests/data/espn_scoreboard_sample.json")
    return list(parse_games(scoreboard))


def test_parse_games(sample_games: list[Game]) -> None:
    assert len(sample_games) == 4
    first = sample_games[0]
    assert first.home.name == "Oregon Ducks"
    assert first.away.name == "Washington State Cougars"
    assert "ESPN" in first.broadcasts


def test_interest_high_for_close_late_game(sample_games: list[Game]) -> None:
    game = next(g for g in sample_games if g.id == "401514123")
    now = datetime(2023, 10, 21, 23, 45, tzinfo=timezone.utc)
    score = interest_score(game, now=now)
    assert score > 70


def test_interest_lower_for_blowout(sample_games: list[Game]) -> None:
    game = next(g for g in sample_games if g.id == "401514200")
    now = datetime(2023, 10, 21, 23, 0, tzinfo=timezone.utc)
    score = interest_score(game, now=now)
    assert score < 70


def test_final_game_has_winner_and_bonus(sample_games: list[Game]) -> None:
    game = next(g for g in sample_games if g.id == "401514400")
    assert game.winner is not None
    now = datetime(2023, 10, 22, 1, 0, tzinfo=timezone.utc)
    score = interest_score(game, now=now)
    assert score == pytest.approx(22.5, rel=1e-3)


def test_select_top_games_orders_by_interest(sample_games: list[Game]) -> None:
    now = datetime(2023, 10, 21, 23, 45, tzinfo=timezone.utc)
    ranked = select_top_games(sample_games)
    scores = [interest_score(g, now=now) for g in ranked]
    assert scores == sorted(scores, reverse=True)


def test_build_game_summary_includes_tv(sample_games: list[Game]) -> None:
    game = next(g for g in sample_games if "ESPN" in g.broadcasts)
    summary = build_game_summary(game, include_notes=True)
    assert "TV: ESPN" in summary
    assert "Ducks convert" in summary
