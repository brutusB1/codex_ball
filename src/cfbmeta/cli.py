"""Command line interface for the college football meta guide."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Iterable, List

from .analysis import build_game_summary, interest_score, select_top_games
from .data_fetcher import ScoreboardLoadError, load_scoreboard
from .models import parse_games


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="YYYYMMDD date for the scoreboard")
    parser.add_argument(
        "--scoreboard",
        help="Path to a saved ESPN scoreboard JSON file (bypasses network fetch)",
    )
    parser.add_argument("--top", type=int, default=10, help="Limit the number of games shown")
    parser.add_argument(
        "--only-live",
        action="store_true",
        help="Only show games that are currently in progress",
    )
    parser.add_argument(
        "--include-notes",
        action="store_true",
        help="Include odds/headlines in the output",
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Do not filter the scoreboard when ranking games",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        scoreboard = load_scoreboard(date=args.date, scoreboard_path=args.scoreboard)
    except ScoreboardLoadError as exc:
        print(f"Error: {exc}")
        return 1

    games = list(parse_games(scoreboard))
    if args.only_live:
        games = [g for g in games if g.is_live]
    if not args.show_all:
        games = [g for g in games if g.is_live or g.home.rank or g.away.rank]

    ranked_games = select_top_games(games, limit=args.top)

    now = datetime.now(timezone.utc)
    rows: List[str] = []
    for game in ranked_games:
        summary = build_game_summary(game, include_notes=args.include_notes)
        rows.append(f"[{interest_score(game, now=now):5.2f}] {summary}")

    if not rows:
        print("No games matched the filters.")
        return 0

    print("College Football Meta Guide")
    print("=" * 32)
    for row in rows:
        print(row)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())
