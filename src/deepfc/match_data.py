"""Canonical match data used by every DeepFC model."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Match:
    """One completed football match in DeepFC's source-independent format."""

    match_date: date
    competition: str
    home_team: str
    away_team: str
    home_corners: int
    away_corners: int

    def __post_init__(self) -> None:
        if not isinstance(self.match_date, date):
            raise ValueError("match_date must be a date")

        for field_name in ("competition", "home_team", "away_team"):
            value = getattr(self, field_name)
            if not value.strip():
                raise ValueError(f"{field_name} must not be empty")

        if self.home_team.strip() == self.away_team.strip():
            raise ValueError("home_team and away_team must be different")

        for field_name in ("home_corners", "away_corners"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")

    @property
    def total_corners(self) -> int:
        """Return the full-match corner total."""

        return self.home_corners + self.away_corners
