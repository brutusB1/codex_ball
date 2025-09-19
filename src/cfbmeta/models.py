"""Domain models for college football games."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Sequence



@dataclass
class TeamScore:
    """Represents a team's score and metadata."""

    name: str
    abbreviation: str
    score: int
    record: Optional[str] = None
    rank: Optional[int] = None


@dataclass
class Game:
    """Normalized representation of a college football game."""

    id: str
    start_time: datetime
    status: str
    period: int
    clock: str
    is_live: bool
    venue: Optional[str]
    broadcasts: Sequence[str]
    home: TeamScore
    away: TeamScore
    notes: List[str] = field(default_factory=list)

    @property
    def score_margin(self) -> int:
        return abs(self.home.score - self.away.score)

    @property
    def is_final(self) -> bool:
        return "final" in self.status.lower()

    @property
    def winner(self) -> Optional[TeamScore]:
        if not self.is_final:
            return None
        if self.home.score == self.away.score:
            return None
        return self.home if self.home.score > self.away.score else self.away

    @classmethod
    def from_espn_event(cls, event: dict) -> "Game":
        competition = event["competitions"][0]
        status = competition["status"]["type"]
        competitors = competition["competitors"]
        home_data = next(c for c in competitors if c["homeAway"] == "home")
        away_data = next(c for c in competitors if c["homeAway"] == "away")

        def _team_score(data: dict) -> TeamScore:
            team = data["team"]
            rank = team.get("rank")
            return TeamScore(
                name=team.get("displayName") or team.get("name"),
                abbreviation=team.get("abbreviation", ""),
                score=int(data.get("score", 0)),
                record=next((rec.get("summary") for rec in data.get("records", [])), None),
                rank=int(rank) if rank is not None else None,
            )

        start_time = _parse_datetime(competition["date"])
        broadcasts = _broadcasts(competition)

        return cls(
            id=event.get("id") or competition.get("id"),
            start_time=start_time,
            status=status.get("name", "STATUS_UNKNOWN"),
            period=int(status.get("period", 0)),
            clock=status.get("displayClock", ""),
            is_live=status.get("state") == "in",
            venue=_venue_name(competition),
            broadcasts=broadcasts,
            home=_team_score(home_data),
            away=_team_score(away_data),
            notes=_build_notes(status, competition),
        )


def _broadcasts(competition: dict) -> Sequence[str]:
    broadcasts = competition.get("broadcasts") or []
    names: List[str] = []
    for broadcast in broadcasts:
        if broadcast.get("media") != "TV":
            continue
        for name in broadcast.get("names", []):
            if name not in names:
                names.append(name)
    if not names and competition.get("geoBroadcasts"):
        for geo in competition["geoBroadcasts"]:
            media = geo.get("media")
            if media and media.get("type") == "TV" and geo.get("type", {}).get("shortName"):
                channel = f"{geo['type']['shortName']} {media.get('channel', '').strip()}".strip()
                if channel and channel not in names:
                    names.append(channel)
    return names


def _venue_name(competition: dict) -> Optional[str]:
    venue = competition.get("venue") or {}
    return venue.get("fullName")


def _build_notes(status: dict, competition: dict) -> List[str]:
    notes: List[str] = []
    if status.get("state") == "pre":
        if competition.get("odds"):
            odds_text = competition["odds"][0].get("details")
            if odds_text:
                notes.append(odds_text)
    headlines = competition.get("headlines") or []
    if headlines:
        primary = headlines[0]
        if primary.get("shortLinkText"):
            notes.append(primary["shortLinkText"])
    return notes


def parse_games(scoreboard: dict) -> Iterable[Game]:
    for event in scoreboard.get("events", []):
        try:
            yield Game.from_espn_event(event)
        except Exception:  # pragma: no cover - guard against unexpected API changes
            continue


def _parse_datetime(value: str) -> datetime:
    if value.endswith('Z'):
        value = value[:-1] + '+00:00'
    return datetime.fromisoformat(value).astimezone(timezone.utc)
