import json
import math
from datetime import date
from pathlib import Path

import pytest

from deepfc.match_data import Match
from deepfc.total_corners import (
    SUPPORTED_TOTAL_CORNER_LINES,
    TeamVenueCornerStats,
    _estimate_corners_for_team,
    _smoothed_corners_per_match,
    compare_total_corner_models,
    evaluate_total_corner_predictions,
    poisson_over_probability,
    predict_total_corners_with_league_average,
    predict_total_corners_with_team_strength,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "football_data_sample.csv"


def make_match(
    match_date: date,
    home_team: str,
    away_team: str,
    home_corners: int,
    away_corners: int = 0,
    season_start_year: int | None = None,
) -> Match:
    if season_start_year is None:
        season_start_year = (
            match_date.year if match_date.month >= 7 else match_date.year - 1
        )
    return Match(
        match_date,
        "E1",
        home_team,
        away_team,
        home_corners,
        away_corners,
        season_start_year,
    )


def test_poisson_over_and_under_are_complements() -> None:
    over_probability = poisson_over_probability(10.0, 9.5)

    assert 0.0 < over_probability < 1.0
    assert over_probability + (1.0 - over_probability) == pytest.approx(1.0)


def test_over_probability_decreases_as_line_increases() -> None:
    probabilities = [
        poisson_over_probability(10.0, line)
        for line in SUPPORTED_TOTAL_CORNER_LINES
    ]

    assert probabilities == sorted(probabilities, reverse=True)


def test_league_average_does_not_leak_same_date_results() -> None:
    matches = [
        make_match(date(2017, 8, 1), "A", "B", 6, 4),
        make_match(date(2018, 8, 1), "C", "D", 2),
        make_match(date(2018, 8, 1), "E", "F", 18),
        make_match(date(2018, 8, 8), "G", "H", 14),
    ]

    predictions = predict_total_corners_with_league_average(
        matches,
        date(2018, 7, 1),
    )

    assert [prediction.expected_total_corners for prediction in predictions] == [
        10.0,
        10.0,
        10.0,
    ]


def test_team_venue_stats_accumulate_explicit_sums() -> None:
    stats = TeamVenueCornerStats()

    stats.add_match(corners_for_in_match=7, corners_against_in_match=4)
    stats.add_match(corners_for_in_match=5, corners_against_in_match=6)

    assert stats.match_count == 2
    assert stats.corners_for_sum == 12
    assert stats.corners_against_sum == 10


def test_smoothing_uses_league_average_as_five_match_prior() -> None:
    no_history = _smoothed_corners_per_match(
        observed_corner_sum=0,
        observed_match_count=0,
        league_corners_per_match=5.0,
    )
    two_matches = _smoothed_corners_per_match(
        observed_corner_sum=14,
        observed_match_count=2,
        league_corners_per_match=5.0,
    )

    assert no_history == 5.0
    assert two_matches == pytest.approx(39 / 7)


def test_team_estimate_combines_corners_for_and_opponent_corners_against() -> None:
    team_stats = TeamVenueCornerStats(
        match_count=2,
        corners_for_sum=14,
        corners_against_sum=8,
    )
    opponent_stats = TeamVenueCornerStats(
        match_count=2,
        corners_for_sum=9,
        corners_against_sum=10,
    )

    expected_corners = _estimate_corners_for_team(
        team_venue_stats=team_stats,
        opponent_venue_stats=opponent_stats,
        league_corners_per_match=5.0,
    )

    assert expected_corners == pytest.approx(((14 + 25) / 7 + (10 + 25) / 7) / 2)


def test_team_strength_does_not_leak_same_date_results() -> None:
    matches = [
        make_match(date(2017, 8, 1), "Warmup A", "Warmup B", 5, 5),
        make_match(date(2018, 8, 1), "A", "B", 10, 0),
        make_match(date(2018, 8, 1), "A", "C", 0, 10),
    ]

    predictions = predict_total_corners_with_team_strength(
        matches,
        date(2018, 7, 1),
    )

    assert [prediction.expected_total_corners for prediction in predictions] == [
        10.0,
        10.0,
    ]


def test_team_strength_resets_team_history_for_new_season() -> None:
    matches = [
        make_match(date(2017, 8, 1), "Warmup A", "Warmup B", 5, 5),
        make_match(date(2018, 8, 1), "A", "B", 10, 0),
        make_match(date(2018, 8, 8), "A", "C", 10, 0),
        make_match(date(2019, 8, 1), "A", "D", 4, 6),
    ]

    predictions = predict_total_corners_with_team_strength(
        matches,
        date(2018, 7, 1),
    )

    assert predictions[-1].expected_total_corners == pytest.approx(10.0)


def test_team_strength_keeps_history_during_extended_season() -> None:
    matches = [
        make_match(date(2018, 8, 1), "Warmup A", "Warmup B", 5, 5),
        make_match(date(2019, 8, 1), "A", "B", 20, 0),
        make_match(
            date(2020, 7, 1),
            "A",
            "C",
            4,
            6,
            season_start_year=2019,
        ),
    ]

    predictions = predict_total_corners_with_team_strength(
        matches,
        date(2019, 7, 1),
    )

    assert predictions[-1].expected_total_corners > 15.0


def test_evaluation_returns_expected_metrics() -> None:
    matches = [
        make_match(date(2017, 8, 1), "A", "B", 6, 4),
        make_match(date(2018, 8, 1), "C", "D", 8),
        make_match(date(2018, 8, 8), "E", "F", 12),
    ]

    metrics = evaluate_total_corner_predictions(
        predict_total_corners_with_league_average(
            matches,
            date(2018, 7, 1),
        )
    )

    assert metrics["evaluated_matches"] == 2
    assert metrics["mae"] == pytest.approx(2.5)
    assert metrics["rmse"] == pytest.approx(math.sqrt(6.5))
    assert set(metrics["lines"]) == {"8.5", "9.5", "10.5", "11.5"}
    assert 0.0 < metrics["mean_brier_score"] < 1.0


def test_comparison_is_json_serializable_and_uses_identical_matches() -> None:
    result = compare_total_corner_models([FIXTURE_PATH])

    assert result["competition"] == "EFL Championship"
    assert result["target"] == "full_match_total_corners"
    assert result["data_quality"]["rows_loaded"] == 5
    assert result["data_quality"]["rows_without_corner_results"] == 1
    assert result["models"]["league_average"]["evaluated_matches"] == 3
    assert result["models"]["team_strength"]["evaluated_matches"] == 3
    json.dumps(result)


def test_comparison_rejects_non_championship_data(tmp_path: Path) -> None:
    csv_path = tmp_path / "premier-league.csv"
    csv_path.write_text(
        "Div,Date,HomeTeam,AwayTeam,HC,AC\n"
        "E0,05/08/2017,Alpha,Beta,6,4\n"
        "E0,04/08/2018,Beta,Alpha,5,5\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Championship rows"):
        compare_total_corner_models([csv_path])


@pytest.mark.parametrize("line", [-0.5, 9.0])
def test_poisson_probability_rejects_unsupported_lines(line: float) -> None:
    with pytest.raises(ValueError):
        poisson_over_probability(10.0, line)
