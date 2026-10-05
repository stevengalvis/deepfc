from dataclasses import replace
from datetime import date, timedelta

import pytest

from deepfc.match_data import Match
from experiments.shot_pressure import (
    BASELINE_STRENGTH,
    MatchShots,
    ShotObservation,
    generate_predictions,
    load_shot_data,
    shot_pressure_feature,
)
from experiments.time_decay import compare_models


def shot_match(index: int) -> MatchShots:
    match = Match(
        date(2019, 1, 1) + timedelta(days=7 * index),
        "E1", "A", "B",
        (2, 10, 4, 8)[index % 4],
        (9, 1, 7, 3)[index % 4],
    )
    return MatchShots(match, 14, 9, 5, 3)


def test_more_attacking_shot_pressure_produces_positive_feature() -> None:
    prediction_date = date(2020, 1, 1)
    history = [
        ShotObservation(date(2019, 12, 1), "A", "home", 20, 8, 8, 2),
        ShotObservation(date(2019, 12, 1), "B", "away", 8, 20, 2, 8),
        ShotObservation(date(2019, 12, 1), "C", "home", 8, 8, 2, 2),
        ShotObservation(date(2019, 12, 1), "D", "away", 8, 8, 2, 2),
    ]
    assert shot_pressure_feature(history, "A", "B", "home", prediction_date) > 0


def test_shot_feature_rejects_same_date_history() -> None:
    prediction_date = date(2020, 1, 1)
    history = [ShotObservation(prediction_date, "A", "home", 10, 8, 4, 2)]
    with pytest.raises(ValueError, match="precede"):
        shot_pressure_feature(history, "A", "B", "home", prediction_date)


def test_zero_strength_exactly_reproduces_fixed_180_day_model() -> None:
    matches = [shot_match(index) for index in range(70)]
    expected = compare_models(item.match for item in matches).time_weighted
    assert generate_predictions(matches)[BASELINE_STRENGTH] == expected


def test_all_strengths_use_same_observations_and_dispersion() -> None:
    predictions = generate_predictions(shot_match(index) for index in range(70))
    baseline = predictions[BASELINE_STRENGTH]
    identity = lambda values: [
        (item.match, item.venue, item.actual_corners, item.dispersion)
        for item in values
    ]
    assert all(identity(values) == identity(baseline) for values in predictions.values())


def test_same_date_shots_and_results_cannot_change_predictions() -> None:
    matches = [shot_match(index) for index in range(70)]
    target_date = matches[60].match.match_date
    changed = [
        replace(
            item,
            match=replace(item.match, home_corners=30, away_corners=25),
            home_shots=40,
            away_shots=35,
            home_shots_on_target=20,
            away_shots_on_target=18,
        )
        if item.match.match_date >= target_date else item
        for item in matches
    ]
    original = generate_predictions(matches)
    modified = generate_predictions(changed)
    for strength in original:
        before = [item for item in original[strength] if item.match.match_date == target_date]
        after = [item for item in modified[strength] if item.match.match_date == target_date]
        assert [
            (item.expected_corners, item.dispersion, item.over_probabilities)
            for item in before
        ] == [
            (item.expected_corners, item.dispersion, item.over_probabilities)
            for item in after
        ]


def test_quarantined_shots_do_not_remove_target_from_cohort() -> None:
    matches = [shot_match(index) for index in range(70)]
    matches[60] = replace(
        matches[60],
        home_shots=None,
        away_shots=None,
        home_shots_on_target=None,
        away_shots_on_target=None,
    )
    predictions = generate_predictions(matches)
    target = matches[60].match
    assert all(
        sum(item.match == target for item in values) == 2
        for values in predictions.values()
    )


def test_known_impossible_source_row_is_quarantined(tmp_path) -> None:
    csv_path = tmp_path / "E1.csv"
    csv_path.write_text(
        "Date,Div,HomeTeam,AwayTeam,HC,AC,HS,AS,HST,AST\n"
        "10/11/2024,E1,Burnley,Swansea,5,4,2,10,7,3\n",
        encoding="utf-8",
    )
    loaded = load_shot_data([csv_path])
    assert loaded.quarantined_shot_rows == 1
    assert loaded.matches[0].has_valid_shots is False
