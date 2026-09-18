import json
import math
from datetime import date
from pathlib import Path

import pytest

from deepfc.match_data import Match
from deepfc.total_corners import (
    CORNER_LINES,
    _estimate_negative_binomial_dispersion,
    evaluate_predictions,
    negative_binomial_negative_log_loss,
    negative_binomial_over_probability,
    poisson_over_probability,
    run_evaluation,
    walk_forward_predictions,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "football_data_sample.csv"


def make_match(match_date: date, home: str, away: str, total: int) -> Match:
    return Match(match_date, "E1", home, away, total, 0)


def test_poisson_over_and_under_are_complements() -> None:
    over_probability = poisson_over_probability(10.0, 9.5)

    assert 0.0 < over_probability < 1.0
    assert over_probability + (1.0 - over_probability) == pytest.approx(1.0)


def test_over_probability_decreases_as_line_increases() -> None:
    probabilities = [poisson_over_probability(10.0, line) for line in CORNER_LINES]

    assert probabilities == sorted(probabilities, reverse=True)


def test_negative_binomial_matches_poisson_with_zero_dispersion() -> None:
    assert negative_binomial_over_probability(10.0, 9.5, 0.0) == pytest.approx(
        poisson_over_probability(10.0, 9.5)
    )


def test_negative_binomial_assigns_more_probability_to_high_total() -> None:
    poisson_probability = poisson_over_probability(10.0, 14.5)
    negative_binomial_probability = negative_binomial_over_probability(
        10.0,
        14.5,
        0.02,
    )

    assert negative_binomial_probability > poisson_probability


def test_dispersion_estimate_uses_only_observed_variance() -> None:
    assert _estimate_negative_binomial_dispersion(2, 20, 400) == pytest.approx(
        1.9
    )
    assert _estimate_negative_binomial_dispersion(1, 10, 100) == 0.0
    assert _estimate_negative_binomial_dispersion(2, 0, 0) == 0.0


def test_walk_forward_does_not_leak_same_date_results() -> None:
    matches = [
        make_match(date(2017, 8, 1), "A", "B", 10),
        make_match(date(2018, 8, 1), "C", "D", 2),
        make_match(date(2018, 8, 1), "E", "F", 18),
        make_match(date(2018, 8, 8), "G", "H", 14),
    ]

    predictions = walk_forward_predictions(matches, date(2018, 7, 1))

    assert [prediction.expected_total for prediction in predictions] == [10.0, 10.0, 10.0]


def test_walk_forward_estimates_dispersion_without_same_date_leakage() -> None:
    matches = [
        make_match(date(2017, 8, 1), "A", "B", 0),
        make_match(date(2017, 8, 8), "C", "D", 20),
        make_match(date(2018, 8, 1), "E", "F", 2),
        make_match(date(2018, 8, 1), "G", "H", 18),
    ]

    predictions = walk_forward_predictions(
        matches,
        date(2018, 7, 1),
    )

    assert [prediction.expected_total for prediction in predictions] == [10.0, 10.0]
    assert [
        prediction.negative_binomial_dispersion for prediction in predictions
    ] == [
        pytest.approx(1.9),
        pytest.approx(1.9),
    ]


def test_evaluation_returns_expected_metrics() -> None:
    matches = [
        make_match(date(2017, 8, 1), "A", "B", 10),
        make_match(date(2018, 8, 1), "C", "D", 8),
        make_match(date(2018, 8, 8), "E", "F", 12),
    ]

    metrics = evaluate_predictions(
        walk_forward_predictions(matches, date(2018, 7, 1))
    )

    assert metrics["evaluated_matches"] == 2
    assert metrics["mae"] == pytest.approx(2.5)
    assert metrics["rmse"] == pytest.approx(math.sqrt(6.5))
    assert set(metrics["lines"]) == {"8.5", "9.5", "10.5", "11.5"}
    assert 0.0 < metrics["mean_brier_score"] < 1.0


def test_evaluation_reports_negative_binomial_count_loss() -> None:
    matches = [
        make_match(date(2017, 8, 1), "A", "B", 0),
        make_match(date(2017, 8, 8), "C", "D", 20),
        make_match(date(2018, 8, 1), "E", "F", 10),
    ]
    predictions = walk_forward_predictions(
        matches,
        date(2018, 7, 1),
    )

    metrics = evaluate_predictions(predictions)

    assert "poisson_negative_log_loss" not in metrics
    assert metrics["negative_binomial_negative_log_loss"] == pytest.approx(
        negative_binomial_negative_log_loss(10, 10.0, 1.9)
    )


def test_run_evaluation_is_json_serializable() -> None:
    result = run_evaluation([FIXTURE_PATH])

    assert result["competition"] == "EFL Championship"
    assert result["target"] == "full_match_total_corners"
    assert result["data_quality"]["rows_loaded"] == 5
    assert result["data_quality"]["rows_without_corner_results"] == 1
    json.dumps(result)


def test_run_evaluation_rejects_non_championship_data(tmp_path: Path) -> None:
    csv_path = tmp_path / "premier-league.csv"
    csv_path.write_text(
        "Div,Date,HomeTeam,AwayTeam,HC,AC\n"
        "E0,05/08/2017,Alpha,Beta,6,4\n"
        "E0,04/08/2018,Beta,Alpha,5,5\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Championship rows"):
        run_evaluation([csv_path])


@pytest.mark.parametrize("line", [-0.5, 9.0])
def test_poisson_probability_rejects_unsupported_lines(line: float) -> None:
    with pytest.raises(ValueError):
        poisson_over_probability(10.0, line)
