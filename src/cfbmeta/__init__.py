"""College football meta guide package."""

from .models import Game, TeamScore
from .analysis import build_game_summary, interest_score
from .data_fetcher import load_scoreboard

__all__ = [
    "Game",
    "TeamScore",
    "build_game_summary",
    "interest_score",
    "load_scoreboard",
]
