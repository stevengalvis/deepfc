import json
from datetime import date
from pathlib import Path

import pytest

from deepfc.match_data import Match
from deepfc.team_corners import (
    TEAM_CORNER_LINES,
    ModelPredictions,
    TeamCornerHistory,
    TeamCornerPrediction,
    evaluate_predictions,
    evaluate_prior_sensitivity,
    expected_team_corners,
    paired_bootstrap,
    run_comparison,
    smoothed_average,
    walk_forward_prediction_comparison,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "football_data_sample.csv"


def make_match(
    match_date: date,
    home_team: str,
    away_team: str,
    home_corners: int,
    away_corners: int,
) -> Match:
    return Match(
        match_date,
        "E1",
        home_team,
        away_team,
        home_corners,
        away_corners,
    )


def test_one_match_creates_home_and_away_predictions() -> None:
    matches = [
        make_match(date(2017, 8, 1), "Warmup A", "Warmup B", 6, 4),
        make_match(date(2018, 8, 1), "Cardiff", "Millwall", 7, 3),
    ]

    comparison = walk_forward_prediction_comparison(
        matches,
        date(2018, 7, 1),
    )

    assert [
        (prediction.team, prediction.venue, prediction.actual_corners)
        for prediction in comparison.team_opponent
    ] == [
        ("Cardiff", "home", 7),
        ("Millwall", "away", 3),
    ]


def test_smoothing_uses_configured_league_average_prior() -> None:
    assert smoothed_average(14, 2, 5.0, prior_matches=5) == pytest.approx(39 / 7)
    assert smoothed_average(0, 0, 5.0, prior_matches=5) == 5.0


def test_team_estimate_combines_attack_and_opponent_defence() -> None:
    team_history = TeamCornerHistory(
        matches=2,
        corners_won=14,
        corners_allowed=8,
    )
    opponent_history = TeamCornerHistory(
        matches=2,
        corners_won=9,
        corners_allowed=10,
    )

    prediction = expected_team_corners(
        team_history,
        opponent_history,
        league_average=5.0,
        prior_matches=5,
    )

    assert prediction == pytest.approx(((14 + 25) / 7 + (10 + 25) / 7) / 2)


def test_same_date_results_do_not_affect_each_other() -> None:
    matches = [
        make_match(date(2017, 8, 1), "Warmup A", "Warmup B", 5, 5),
        make_match(date(2018, 8, 1), "A", "B", 10, 0),
        make_match(date(2018, 8, 1), "A", "C", 0, 10),
    ]

    comparison = walk_forward_prediction_comparison(
        matches,
        date(2018, 7, 1),
    )

    assert [
        prediction.expected_corners
        for prediction in comparison.team_opponent
    ] == [5.0, 5.0, 5.0, 5.0]


def test_team_corner_dispersion_uses_individual_venue_totals() -> None:
    matches = [
        make_match(date(2017, 8, 1), "A", "B", 0, 10),
        make_match(date(2017, 8, 8), "C", "D", 10, 0),
        make_match(date(2018, 8, 1), "E", "F", 5, 5),
    ]

    comparison = walk_forward_prediction_comparison(
        matches,
        date(2018, 7, 1),
    )

    home_prediction, away_prediction = comparison.venue_average
    assert home_prediction.dispersion == pytest.approx(1.8)
    assert away_prediction.dispersion == pytest.approx(1.8)


def test_evaluation_reports_team_corner_metrics() -> None:
    matches = [
        make_match(date(2017, 8, 1), "A", "B", 5, 5),
        make_match(date(2018, 8, 1), "C", "D", 7, 3),
    ]
    predictions = walk_forward_prediction_comparison(
        matches,
        date(2018, 7, 1),
    ).venue_average

    metrics = evaluate_predictions(predictions)

    assert metrics["evaluated_team_observations"] == 2
    assert metrics["mae"] == 2.0
    assert set(metrics["lines"]) == {
        str(line) for line in TEAM_CORNER_LINES
    }


def test_prior_sensitivity_evaluates_each_requested_prior() -> None:
    matches = [
        make_match(date(2017, 8, 1), "A", "B", 5, 5),
        make_match(date(2018, 8, 1), "A", "B", 7, 3),
    ]

    sensitivity = evaluate_prior_sensitivity(
        matches,
        prior_match_counts=(2, 5, 10),
        evaluation_start=date(2018, 7, 1),
    )

    assert set(sensitivity) == {"2", "5", "10"}
    assert all("mae" in differences for differences in sensitivity.values())


def test_paired_bootstrap_is_reproducible_and_paired_by_fixture() -> None:
    match = make_match(date(2018, 8, 1), "A", "B", 7, 3)

    def prediction(team: str, actual: int, expected: float) -> TeamCornerPrediction:
        return TeamCornerPrediction(
            match=match,
            team=team,
            venue="home" if team == "A" else "away",
            expected_corners=expected,
            actual_corners=actual,
            over_probabilities={line: 0.5 for line in TEAM_CORNER_LINES},
            dispersion=0.0,
        )

    comparison = ModelPredictions(
        venue_average=(prediction("A", 7, 5), prediction("B", 3, 5)),
        team_opponent=(prediction("A", 7, 6), prediction("B", 3, 4)),
    )

    result = paired_bootstrap(comparison, samples=20, seed=12)

    assert result == paired_bootstrap(comparison, samples=20, seed=12)
    assert result["metrics"]["mae"]["mean_delta"] == -1.0
    assert result["metrics"]["mae"]["challenger_win_rate"] == 1.0


def test_comparison_is_json_serializable_and_uses_same_observations() -> None:
    result = run_comparison([FIXTURE_PATH], bootstrap_samples=20)

    assert result["competition"] == "EFL Championship"
    assert result["target"] == "individual_team_full_match_corners"
    assert result["data_quality"]["rows_loaded"] == 5
    baseline = result["models"]["venue_average"]["overall"]
    challenger = result["models"]["team_opponent"]["overall"]
    assert baseline["evaluated_team_observations"] == 6
    assert challenger["evaluated_team_observations"] == 6
    json.dumps(result)
