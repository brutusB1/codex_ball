# College Football Meta Guide

This project provides a command line tool for monitoring college football games in progress.
It aggregates TV channel assignments, highlights close games late in the second half, and
ranks matchups to help decide which game to watch.

## Features

* Fetches the ESPN college football scoreboard for a specific date (defaults to today).
* Normalizes each game into structured data that includes team names, TV broadcasts, start
  time, and live status information.
* Computes an "interest" score that favors ranked matchups and especially games that are
  close in the 3rd or 4th quarter.
* Renders a compact table that can be sorted by interest score or filtered to only show
  live games.
* Can operate offline by pointing to a stored JSON scoreboard snapshot, enabling
  repeatable testing.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
cfbmeta --date 20231021 --top 8
```

### CLI Options

* `--date YYYYMMDD` – Fetches the scoreboard for the given date.
* `--scoreboard PATH` – Uses a local ESPN scoreboard JSON file instead of fetching from
  the network.
* `--only-live` – Shows only games that are currently in progress.
* `--top N` – Limits the output to the top `N` games by interest score.
* `--show-all` – Displays the full scoreboard instead of only ranked games.

Running `cfbmeta --help` prints the full list of options.

## Development

Install the development dependencies and run the tests:

```bash
pip install -e .[dev]
pytest
```

The project intentionally separates data fetching from analytics so that tests can run
entirely against the bundled sample scoreboard snapshot in `tests/data`.
