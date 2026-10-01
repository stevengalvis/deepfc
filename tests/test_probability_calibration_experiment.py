from datetime import date, timedelta

import pytest

from deepfc.match_data import Match
from deepfc.team_corners import TEAM_CORNER_LINES, TeamCornerPrediction
from experiments.probability_calibration import (
    CALIBRATION_END,
    LogisticCalibrator,
    apply_calibration,
    fit_by_line,
    fit_logistic_calibrator,
    paired_block_interval,
    probability_metrics,
    run_experiment,
)


def prediction(index: int, probability: float, actual: int) -> TeamCornerPrediction:
    match = Match(
        date(2020, 1, 1) + timedelta(days=index),
        "E1", f"Home {index}", f"Away {index}", actual, 3,
    )
    return TeamCornerPrediction(
        match, match.home_team, "home", 5.0, actual,
        {line: probability for line in TEAM_CORNER_LINES}, 0.2,
    )


def test_identity_calibrator_preserves_probability() -> None:
    calibrator = LogisticCalibrator(0, 1)
    for probability in (0.01, 0.2, 0.5, 0.8, 0.99):
        assert calibrator.transform(probability) == pytest.approx(probability)


def test_fit_corrects_overconfident_probabilities() -> None:
    probabilities = [0.8] * 10
    outcomes = [1.0] * 6 + [0.0] * 4
    calibrator = fit_logistic_calibrator(probabilities, outcomes)
    assert calibrator.transform(0.8) == pytest.approx(0.6, abs=1e-8)


def test_fitted_calibration_improves_training_log_loss() -> None:
    observations = tuple(
        prediction(index, probability, actual)
        for index, (probability, actual) in enumerate(
            [(0.8, 8)] * 6 + [(0.8, 0)] * 4 + [(0.2, 8)] * 4 + [(0.2, 0)] * 6
        )
    )
    calibrated = apply_calibration(observations, fit_by_line(observations))
    assert (
        probability_metrics(calibrated)["binary_negative_log_loss"]
        < probability_metrics(observations)["binary_negative_log_loss"]
    )


def test_apply_calibration_changes_only_market_probabilities() -> None:
    original = prediction(0, 0.8, 8)
    calibrators = {line: LogisticCalibrator(-0.2, 0.9) for line in TEAM_CORNER_LINES}
    calibrated = apply_calibration((original,), calibrators)[0]
    assert calibrated.over_probabilities != original.over_probabilities
    assert calibrated.match == original.match
    assert calibrated.team == original.team
    assert calibrated.venue == original.venue
    assert calibrated.expected_corners == original.expected_corners
    assert calibrated.actual_corners == original.actual_corners
    assert calibrated.dispersion == original.dispersion


def test_each_line_gets_its_own_calibrator() -> None:
    observations = []
    for index in range(20):
        item = prediction(index, 0.5, 8 if index < 10 else 0)
        item = TeamCornerPrediction(
            item.match, item.team, item.venue, item.expected_corners,
            index % 8, {line: 0.5 for line in TEAM_CORNER_LINES}, item.dispersion,
        )
        observations.append(item)
    calibrators = fit_by_line(observations)
    assert set(calibrators) == set(TEAM_CORNER_LINES)
    assert len({model.intercept for model in calibrators.values()}) > 1


def test_identical_predictions_have_zero_paired_intervals() -> None:
    observations = tuple(prediction(index, 0.6, index % 8) for index in range(20))
    result = paired_block_interval(observations, observations, samples=50)
    for metric in result.values():
        assert metric == {"lower_95": 0.0, "upper_95": 0.0, "fraction_below_zero": 0.0}


@pytest.mark.parametrize("probability", [-0.1, 1.1, float("nan")])
def test_invalid_probabilities_are_rejected(probability: float) -> None:
    with pytest.raises(ValueError, match="probability"):
        LogisticCalibrator(0, 1).transform(probability)


def test_fit_rejects_mismatched_or_nonbinary_data() -> None:
    with pytest.raises(ValueError):
        fit_logistic_calibrator([0.5], [])
    with pytest.raises(ValueError):
        fit_logistic_calibrator([0.5], [0.2])


def test_post_calibration_results_cannot_change_fitted_parameters() -> None:
    matches = [
        Match(
            date(2018, 1, 1) + timedelta(days=7 * index),
            "E1", "A", "B",
            (2, 10, 4, 8)[index % 4],
            (9, 1, 7, 3)[index % 4],
        )
        for index in range(420)
    ]
    changed = [
        Match(
            item.match_date, item.competition, item.home_team, item.away_team,
            30 if item.match_date >= CALIBRATION_END else item.home_corners,
            25 if item.match_date >= CALIBRATION_END else item.away_corners,
        )
        for item in matches
    ]
    assert (
        run_experiment(matches)["fitted_calibrators"]
        == run_experiment(changed)["fitted_calibrators"]
    )
