from dataclasses import replace
from datetime import date, timedelta

import pytest

from deepfc.corner_distribution import estimate_dispersion
from deepfc.match_data import Match
from experiments.dispersion import (
    compare_dispersion_models,
    paired_block_intervals,
    weighted_dispersion,
)
from experiments.time_decay import CornerObservation, compare_models


def match_history(count: int = 70) -> list[Match]:
    return [
        Match(
            date(2019, 1, 1) + timedelta(days=7 * index),
            "E1", "A", "B",
            (2, 10, 4, 8)[index % 4],
            (9, 1, 7, 3)[index % 4],
        )
        for index in range(count)
    ]


def observations() -> list[CornerObservation]:
    result = []
    for match in match_history(20):
        result.extend((
            CornerObservation(
                match, match.home_team, match.away_team, "home",
                match.home_corners, match.away_corners,
            ),
            CornerObservation(
                match, match.away_team, match.home_team, "away",
                match.away_corners, match.home_corners,
            ),
        ))
    return result


def test_unweighted_pooled_dispersion_matches_retained_estimator() -> None:
    history = observations()
    values = [item.corners_for for item in history]
    expected = estimate_dispersion(len(values), sum(values), sum(value**2 for value in values))
    assert weighted_dispersion(history, date(2020, 1, 1)) == expected


def test_venue_filter_uses_only_requested_role() -> None:
    history = observations()
    home_values = [item.corners_for for item in history if item.venue == "home"]
    expected = estimate_dispersion(
        len(home_values), sum(home_values), sum(value**2 for value in home_values),
    )
    assert weighted_dispersion(history, date(2020, 1, 1), venue="home") == expected


def test_weighted_variance_uses_unbiased_reliability_denominator() -> None:
    prediction_date = date(2020, 1, 1)
    old_match = Match(prediction_date - timedelta(days=360), "E1", "A", "B", 2, 3)
    recent_match = Match(prediction_date - timedelta(days=180), "E1", "A", "C", 10, 4)
    history = [
        CornerObservation(old_match, "A", "B", "home", 2, 3),
        CornerObservation(recent_match, "A", "C", "home", 10, 4),
    ]
    weights = (0.25, 0.5)
    values = (2, 10)
    total_weight = sum(weights)
    mean = sum(w * value for w, value in zip(weights, values)) / total_weight
    denominator = total_weight - sum(w**2 for w in weights) / total_weight
    variance = sum(w * (value - mean) ** 2 for w, value in zip(weights, values)) / denominator
    expected = max(0, (variance - mean) / mean**2)
    assert weighted_dispersion(
        history, prediction_date, venue="home", half_life_days=180,
    ) == pytest.approx(expected)


def test_baseline_exactly_reproduces_fixed_180_day_model() -> None:
    matches = match_history()
    compared = compare_dispersion_models(matches).predictions
    assert compared["pooled_all_history"] == compare_models(matches).time_weighted


def test_dispersion_methods_preserve_means_and_fixture_cohort() -> None:
    compared = compare_dispersion_models(match_history()).predictions
    baseline = compared["pooled_all_history"]
    identity = lambda values: [
        (item.match, item.venue, item.expected_corners, item.actual_corners)
        for item in values
    ]
    assert all(identity(values) == identity(baseline) for values in compared.values())
    assert any(
        item.dispersion != baseline[index].dispersion
        for values in compared.values()
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
    original = compare_dispersion_models(matches).predictions
    modified = compare_dispersion_models(changed).predictions
    for name in original:
        first = [item for item in original[name] if item.match.match_date == target_date]
        second = [item for item in modified[name] if item.match.match_date == target_date]
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


def test_invalid_weighted_dispersion_inputs_are_rejected() -> None:
    history = observations()
    with pytest.raises(ValueError, match="precede"):
        weighted_dispersion(history, history[-1].match.match_date)
    with pytest.raises(ValueError, match="positive"):
        weighted_dispersion(history, date(2020, 1, 1), half_life_days=0)
