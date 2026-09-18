from datetime import date
from pathlib import Path

import pytest

from deepfc.football_data_csv import load_football_data_csv


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "football_data_sample.csv"


def test_loads_and_maps_football_data_columns() -> None:
    result = load_football_data_csv([FIXTURE_PATH])

    first_match = result.matches[0]
    assert first_match.match_date == date(2017, 8, 5)
    assert first_match.competition == "E1"
    assert first_match.home_team == "Alpha"
    assert first_match.away_team == "Beta"
    assert first_match.home_corners == 6
    assert first_match.away_corners == 4


def test_reports_row_quality_counts() -> None:
    result = load_football_data_csv([FIXTURE_PATH])

    assert result.rows_read == 6
    assert result.rows_loaded == 5
    assert result.rows_without_corner_results == 1


def test_rejects_csv_without_required_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "missing-columns.csv"
    csv_path.write_text("Date,HomeTeam,AwayTeam\n01/01/2026,A,B\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        load_football_data_csv([csv_path])


def test_reports_file_and_row_for_invalid_completed_match(tmp_path: Path) -> None:
    csv_path = tmp_path / "invalid-corners.csv"
    csv_path.write_text(
        "Div,Date,HomeTeam,AwayTeam,HC,AC\n"
        "E1,05/08/2017,Alpha,Beta,not-a-number,4\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"invalid-corners\.csv row 2"):
        load_football_data_csv([csv_path])


def test_rejects_partially_missing_corner_result(tmp_path: Path) -> None:
    csv_path = tmp_path / "partial-result.csv"
    csv_path.write_text(
        "Div,Date,HomeTeam,AwayTeam,HC,AC\n"
        "E1,05/08/2017,Alpha,Beta,6,\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="corner count is missing"):
        load_football_data_csv([csv_path])
