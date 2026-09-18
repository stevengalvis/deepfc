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
DATE_FORMATS = ("%d/%m/%Y", "%d/%m/%y")


@dataclass(frozen=True)
class LoadResult:
    """Loaded matches and row-quality counts from one or more CSV files."""

    matches: tuple[Match, ...]
    rows_read: int
    rows_loaded: int
    rows_without_corner_results: int


def _parse_date(raw_date: str) -> date:
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(raw_date.strip(), date_format).date()
        except ValueError:
            continue
    raise ValueError(f"unsupported match date: {raw_date!r}")


def _parse_corners(raw_corners: str) -> int:
    raw_value = raw_corners.strip()
    if not raw_value:
        raise ValueError("corner count is missing")
    value = float(raw_value)
    if not value.is_integer() or value < 0:
        raise ValueError("corner counts must be non-negative integers")
    return int(value)


def _is_missing_corner_result(row: dict[str, str | None]) -> bool:
    """Return whether both corner fields are blank for an unplayed fixture."""

    return not (row["HC"] or "").strip() and not (row["AC"] or "").strip()


def _parse_match(
    row: dict[str, str | None],
    season_start_year: int,
) -> Match:
    """Convert one Football-Data row into a canonical Match."""

    return Match(
        match_date=_parse_date(row["Date"] or ""),
        competition=(row["Div"] or "").strip(),
        home_team=(row["HomeTeam"] or "").strip(),
        away_team=(row["AwayTeam"] or "").strip(),
        home_corners=_parse_corners(row["HC"] or ""),
        away_corners=_parse_corners(row["AC"] or ""),
        season_start_year=season_start_year,
    )


def _season_start_year(earliest_match_date: date) -> int:
    return (
        earliest_match_date.year
        if earliest_match_date.month >= 7
        else earliest_match_date.year - 1
    )


def load_football_data_csv(paths: Iterable[str | Path]) -> LoadResult:
    """Load completed matches and count fixtures without corner results."""

    matches: list[Match] = []
    rows_read = 0
    rows_without_corner_results = 0

    for path_value in paths:
        path = Path(path_value)
        with path.open(encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            columns = set(reader.fieldnames or ())
            missing_columns = REQUIRED_COLUMNS - columns
            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise ValueError(f"{path} is missing required columns: {missing}")

            numbered_rows = list(enumerate(reader, start=2))
            rows_read += len(numbered_rows)
            if not numbered_rows:
                continue

            try:
                earliest_match_date = min(
                    _parse_date(row["Date"] or "")
                    for _, row in numbered_rows
                )
            except (TypeError, ValueError) as error:
                raise ValueError(f"{path}: {error}") from error
            season_start_year = _season_start_year(earliest_match_date)

            for row_number, row in numbered_rows:
                try:
                    if _is_missing_corner_result(row):
                        rows_without_corner_results += 1
                        continue
                    matches.append(_parse_match(row, season_start_year))
                except (TypeError, ValueError) as error:
                    raise ValueError(f"{path} row {row_number}: {error}") from error

    matches.sort(key=lambda match: match.match_date)
    return LoadResult(
        matches=tuple(matches),
        rows_read=rows_read,
        rows_loaded=len(matches),
        rows_without_corner_results=rows_without_corner_results,
    )
