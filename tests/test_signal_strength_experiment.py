from dataclasses import replace
from datetime import date, timedelta

from deepfc.match_data import Match
from experiments.signal_strength import (
    BASELINE,
    generate_predictions,
    paired_block_intervals,
)
from experiments.time_decay import compare_models


def match_history() -> list[Match]:
    return [
        Match(
            date(2019, 1, 1) + timedelta(days=7 * index),
            "E1", "A", "B",
            (2, 10, 4, 8)[index % 4],
            (9, 1, 7, 3)[index % 4],
        )
        for index in range(70)
    ]


def test_baseline_exactly_reproduces_fixed_180_day_model() -> None:
    matches = match_history()
    assert generate_predictions(matches)[BASELINE] == compare_models(matches).time_weighted


def test_strength_grid_preserves_fixture_cohort_and_dispersion() -> None:
    predictions = generate_predictions(match_history())
    baseline = predictions[BASELINE]
    identity = lambda values: [
        (item.match, item.venue, item.actual_corners, item.dispersion)
        for item in values
    ]
    assert all(identity(values) == identity(baseline) for values in predictions.values())
    assert any(
        item.expected_corners != baseline[index].expected_corners
        for strengths, values in predictions.items() if strengths != BASELINE
        for index, item in enumerate(values)
    )


def test_same_date_and_future_results_cannot_change_target_predictions() -> None:
    matches = match_history()
    target_date = matches[60].match_date
    changed = [
        replace(item, home_corners=30, away_corners=25)
        if item.match_date >= target_date else item
        for item in matches
    ]
    original = generate_predictions(matches)
    modified = generate_predictions(changed)
    for strengths in original:
        first = [item for item in original[strengths] if item.match.match_date == target_date]
        second = [item for item in modified[strengths] if item.match.match_date == target_date]
        assert [
            (item.expected_corners, item.dispersion, item.over_probabilities)
            for item in first
        ] == [
            (item.expected_corners, item.dispersion, item.over_probabilities)
            for item in second
        ]


def test_identical_predictions_have_zero_intervals() -> None:
    predictions = compare_models(match_history()).time_weighted
    intervals = paired_block_intervals(predictions, predictions, samples=50)
    assert all(result == {
        "lower_95": 0.0, "upper_95": 0.0, "fraction_below_zero": 0.0,
    } for result in intervals.values())
