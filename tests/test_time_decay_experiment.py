from dataclasses import replace
from datetime import date, timedelta

import pytest

from deepfc.match_data import Match
from experiments.time_decay import (
    HALF_LIFE_DAYS,
    CornerObservation,
    compare_models,
    expected_team_corners,
    paired_block_brier_interval,
    time_weight,
)


def match_history() -> list[Match]:
    return [
        Match(
            date(2019, 1, 1) + timedelta(days=7 * index),
            "E1", "A", "B",
            (2, 10, 4, 8)[index % 4],
            (9, 1, 7, 3)[index % 4],
        )
        for index in range(60)
    ]


def test_weight_halves_every_180_days() -> None:
    assert time_weight(0) == 1
    assert time_weight(90) == pytest.approx(2 ** -0.5)
    assert time_weight(180) == 0.5
    assert time_weight(360) == 0.25
    with pytest.raises(ValueError):
        time_weight(-1)


def test_weighted_expected_corners_favor_recent_results() -> None:
    prediction_date = date(2020, 1, 1)
    old = Match(date(2019, 1, 6), "E1", "A", "B", 2, 4)
    recent = Match(date(2019, 12, 22), "E1", "A", "B", 10, 4)
    history = [
        CornerObservation(old, "A", "B", "home", 2, 4),
        CornerObservation(old, "B", "A", "away", 4, 2),
        CornerObservation(recent, "A", "B", "home", 10, 4),
        CornerObservation(recent, "B", "A", "away", 4, 10),
    ]
    equal = expected_team_corners(
        history, "A", "B", "home", prediction_date, half_life_days=None,
    )
    weighted = expected_team_corners(
        history, "A", "B", "home", prediction_date,
        half_life_days=HALF_LIFE_DAYS,
    )
    assert weighted > equal


def test_weighted_attack_and_concessions_use_effective_match_counts() -> None:
    prediction_date = date(2020, 1, 1)
    old = Match(prediction_date - timedelta(days=360), "E1", "A", "B", 2, 4)
    recent = Match(prediction_date - timedelta(days=180), "E1", "A", "C", 10, 3)
    opponent = Match(prediction_date - timedelta(days=180), "E1", "D", "B", 8, 6)
    history = [
        CornerObservation(old, "A", "B", "home", 2, 4),
        CornerObservation(old, "B", "A", "away", 4, 2),
        CornerObservation(recent, "A", "C", "home", 10, 3),
        CornerObservation(recent, "C", "A", "away", 3, 10),
        CornerObservation(opponent, "D", "B", "home", 8, 6),
        CornerObservation(opponent, "B", "D", "away", 6, 8),
    ]
    # League home rates use all three home teams: weights 1/4, 1/2, 1/2.
    league_rate = (2 * .25 + 10 * .5 + 8 * .5 + 5) / (.25 + .5 + .5 + 5)
    attack_rate = (2 * .25 + 10 * .5 + 5 * league_rate) / (.25 + .5 + 5)
    concession_rate = (2 * .25 + 8 * .5 + 5 * league_rate) / (.25 + .5 + 5)
    expected = attack_rate * concession_rate / league_rate

    assert expected_team_corners(
        history, "A", "B", "home", prediction_date, half_life_days=180,
    ) == pytest.approx(expected)


@pytest.mark.parametrize("half_life", [None, HALF_LIFE_DAYS])
def test_expected_corners_reject_same_date_and_future_history(half_life: int | None) -> None:
    prediction_date = date(2020, 1, 1)
    match = Match(prediction_date, "E1", "A", "B", 3, 4)
    history = [CornerObservation(match, "A", "B", "home", 3, 4)]
    with pytest.raises(ValueError, match="precede"):
        expected_team_corners(
            history, "A", "B", "home", prediction_date,
            half_life_days=half_life,
        )


def test_all_models_use_the_same_fixture_cohort() -> None:
    compared = compare_models(match_history())
    identities = lambda values: [(item.match, item.venue) for item in values]
    assert identities(compared.deepfc) == identities(compared.equal_weight)
    assert identities(compared.deepfc) == identities(compared.time_weighted)
    assert len(compared.deepfc) == 20


def test_same_date_results_cannot_change_predictions() -> None:
    matches = match_history()
    target_date = matches[50].match_date
    original = compare_models(matches)
    changed = compare_models([
        replace(match, home_corners=30, away_corners=25)
        if match.match_date >= target_date else match
        for match in matches
    ])
    for first, second in (
        (original.deepfc, changed.deepfc),
        (original.equal_weight, changed.equal_weight),
        (original.time_weighted, changed.time_weighted),
    ):
        first_day = [item for item in first if item.match.match_date == target_date]
        second_day = [item for item in second if item.match.match_date == target_date]
        assert [(item.expected_corners, item.over_probabilities) for item in first_day] == [
            (item.expected_corners, item.over_probabilities) for item in second_day
        ]


def test_bootstrap_is_zero_for_identical_predictions() -> None:
    predictions = compare_models(match_history()).time_weighted
    result = paired_block_brier_interval(predictions, predictions, samples=50)
    assert result == {
        "lower_95": 0,
        "upper_95": 0,
        "fraction_below_zero": 0,
    }


@pytest.mark.parametrize("problem", ["empty", "wrong_league", "duplicate"])
def test_invalid_history_is_rejected(problem: str) -> None:
    matches = match_history()
    if problem == "empty":
        matches = []
    elif problem == "wrong_league":
        matches[0] = replace(matches[0], competition="E0")
    else:
        matches.append(matches[0])
    with pytest.raises(ValueError):
        compare_models(matches)
