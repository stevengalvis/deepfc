from datetime import date

import pytest

from deepfc.match_data import Match


def test_match_calculates_total_corners() -> None:
    match = Match(date(2026, 8, 8), "E1", "Birmingham", "Millwall", 7, 4)

    assert match.total_corners == 11


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("competition", ""),
        ("match_date", "2026-08-08"),
        ("home_team", " "),
        ("away_team", ""),
        ("home_corners", -1),
        ("away_corners", 2.5),
    ],
)
def test_match_rejects_invalid_values(field: str, value: object) -> None:
    values = {
        "match_date": date(2026, 8, 8),
        "competition": "E1",
        "home_team": "Birmingham",
        "away_team": "Millwall",
        "home_corners": 7,
        "away_corners": 4,
    }
    values[field] = value

    with pytest.raises(ValueError):
        Match(**values)  # type: ignore[arg-type]


def test_match_rejects_same_home_and_away_team() -> None:
    with pytest.raises(ValueError, match="must be different"):
        Match(date(2026, 8, 8), "E1", "Millwall", "MILLWALL", 7, 4)
