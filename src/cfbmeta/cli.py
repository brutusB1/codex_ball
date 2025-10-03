"""Command line interface for the college football meta guide."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence

from .analysis import (
    build_game_summary,
    interest_score,
    select_top_games,
    summarize_games,
)
from .data_fetcher import ScoreboardLoadError, load_scoreboard
from .models import Game, parse_games


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
    parser.add_argument(
        "--favorites",
        help="Comma separated team names or abbreviations to keep in view",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format for the ranked games",
    )
    parser.add_argument(
        "--output",
        help="Optional file path to write the results (defaults to stdout)",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        scoreboard = load_scoreboard(date=args.date, scoreboard_path=args.scoreboard)
    except ScoreboardLoadError as exc:
        print(f"Error: {exc}")
        return 1

    favorites = _parse_favorites(args.favorites)

    games = list(parse_games(scoreboard))
    if args.only_live:
        games = [g for g in games if g.is_live or _is_favorite(g, favorites)]
    if not args.show_all:
        games = [
            g
            for g in games
            if g.is_live or g.home.rank or g.away.rank or _is_favorite(g, favorites)
        ]

    ranked_games = select_top_games(games, limit=args.top)

    if args.format == "json":
        return _emit_json(ranked_games, favorites, args)

    now = datetime.now(timezone.utc)
    rows: List[str] = []
    for game in ranked_games:
        summary = build_game_summary(game, include_notes=args.include_notes)
        if _is_favorite(game, favorites):
            summary = "★ " + summary
        rows.append(f"[{interest_score(game, now=now):5.2f}] {summary}")

    if not rows:
        return _write_output("No games matched the filters.", args.output)

    header = "College Football Meta Guide\n" + "=" * 32
    body = "\n".join(rows)
    text = f"{header}\n{body}"
    return _write_output(text, args.output)


def _emit_json(
    games: Sequence[Game], favorites: Sequence[str], args: argparse.Namespace
) -> int:
    summaries = summarize_games(games, include_notes=args.include_notes)
    for entry, game in zip(summaries, games):
        entry["is_favorite"] = _is_favorite(game, favorites)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "games": summaries,
    }
    json_text = json.dumps(payload, indent=2)
    return _write_output(json_text, args.output)


def _write_output(text: str, output_path: str | None) -> int:
    if output_path:
        Path(output_path).write_text(text + ("\n" if not text.endswith("\n") else ""))
    else:
        print(text)
    return 0


def _parse_favorites(raw: str | None) -> List[str]:
    if not raw:
        return []
    return [token.strip().casefold() for token in raw.split(",") if token.strip()]


def _is_favorite(game: Game, favorites: Sequence[str]) -> bool:
    if not favorites:
        return False

    identifiers = {
        game.home.abbreviation.casefold(),
        game.away.abbreviation.casefold(),
        game.home.name.casefold(),
        game.away.name.casefold(),
    }
    return any(fav in identifiers for fav in favorites)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())
