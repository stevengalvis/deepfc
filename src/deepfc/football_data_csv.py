"""Load Football-Data CSV files into DeepFC's canonical match format."""

import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from deepfc.match_data import Match


REQUIRED_COLUMNS = {
    "Date",
    "Div",
    "HomeTeam",
    "AwayTeam",
    "HC",
    "AC",
}
DATE_FORMATS = ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d")


@dataclass(frozen=True)
class LoadResult:
    """Loaded matches and row-quality counts from one or more CSV files."""

    matches: tuple[Match, ...]
    rows_read: int
    rows_loaded: int
    rows_missing_corners: int
    rows_invalid: int


def _parse_date(raw_date: str) -> date:
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(raw_date.strip(), date_format).date()
        except ValueError:
            continue
    raise ValueError(f"unsupported match date: {raw_date!r}")


def _parse_corners(raw_corners: str) -> int:
    value = float(raw_corners.strip())
    if not value.is_integer() or value < 0:
        raise ValueError("corner counts must be non-negative integers")
    return int(value)


def load_football_data_csv(paths: Iterable[str | Path]) -> LoadResult:
    """Load completed matches and report rows that could not be used."""

    matches: list[Match] = []
    rows_read = 0
    rows_missing_corners = 0
    rows_invalid = 0

    for path_value in paths:
        path = Path(path_value)
        with path.open(encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            columns = set(reader.fieldnames or ())
            missing_columns = REQUIRED_COLUMNS - columns
            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise ValueError(f"{path} is missing required columns: {missing}")

            for row in reader:
                rows_read += 1
                if not (row["HC"] or "").strip() or not (row["AC"] or "").strip():
                    rows_missing_corners += 1
                    continue

                try:
                    matches.append(
                        Match(
                            match_date=_parse_date(row["Date"] or ""),
                            competition=(row["Div"] or "").strip(),
                            home_team=(row["HomeTeam"] or "").strip(),
                            away_team=(row["AwayTeam"] or "").strip(),
                            home_corners=_parse_corners(row["HC"] or ""),
                            away_corners=_parse_corners(row["AC"] or ""),
                        )
                    )
                except (TypeError, ValueError):
                    rows_invalid += 1

    matches.sort(key=lambda match: match.match_date)
    return LoadResult(
        matches=tuple(matches),
        rows_read=rows_read,
        rows_loaded=len(matches),
        rows_missing_corners=rows_missing_corners,
        rows_invalid=rows_invalid,
    )
