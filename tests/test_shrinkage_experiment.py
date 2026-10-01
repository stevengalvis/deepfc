from dataclasses import replace
from datetime import date, timedelta

import pytest

from deepfc.match_data import Match
from deepfc.team_corners import TEAM_CORNER_LINES, TeamCornerPrediction
from experiments.shrinkage import calibration, select_prior
from experiments.time_decay import CornerObservation, compare_models, expected_team_corners


def history():
    return [
        Match(date(2019, 1, 1) + timedelta(days=7 * i), "E1", "A", "B",
              (2, 10, 4, 8)[i % 4], (9, 1, 7, 3)[i % 4])
        for i in range(60)
    ]


def prediction(match_date, probability):
    match = Match(match_date, "E1", "A", "B", 8, 3)
    return TeamCornerPrediction(match, "A", "home", 5.0, 8,
                                {line: probability for line in TEAM_CORNER_LINES}, 0.2)


def test_five_match_prior_preserves_existing_baseline():
    assert compare_models(history()).time_weighted == compare_models(
        history(), time_weighted_prior_matches=5.0,
    ).time_weighted


def test_team_prior_does_not_change_league_smoothing():
    prediction_date = date(2020, 1, 1)
    match = Match(prediction_date - timedelta(days=180), "E1", "A", "B", 10, 2)
    observations = [
        CornerObservation(match, "A", "B", "home", 10, 2),
        CornerObservation(match, "B", "A", "away", 2, 10),
    ]
    league_rate = (10 * 0.5 + 5) / (0.5 + 5)
    team_rate = (10 * 0.5 + 20 * league_rate) / (0.5 + 20)
    result = expected_team_corners(
        observations, "A", "B", "home", prediction_date,
        half_life_days=180, team_prior_matches=20,
    )
    assert result == pytest.approx(team_rate**2 / league_rate)
    weaker = expected_team_corners(
        observations, "A", "B", "home", prediction_date,
        half_life_days=180, team_prior_matches=1,
    )
    assert league_rate < result < weaker


def test_prior_changes_only_weighted_mean_not_cohort_or_dispersion():
    baseline = compare_models(history())
    changed = compare_models(history(), time_weighted_prior_matches=20)
    assert baseline.equal_weight == changed.equal_weight
    assert baseline.deepfc == changed.deepfc
    assert [(p.match, p.venue, p.dispersion) for p in baseline.time_weighted] == [
        (p.match, p.venue, p.dispersion) for p in changed.time_weighted
    ]
    assert any(a.expected_corners != b.expected_corners
               for a, b in zip(baseline.time_weighted, changed.time_weighted))


def test_changed_same_date_and_future_results_cannot_change_forecasts():
    matches = history()
    target_date = matches[50].match_date
    changed = [replace(m, home_corners=30, away_corners=25)
               if m.match_date >= target_date else m for m in matches]
    before = compare_models(matches, time_weighted_prior_matches=20).time_weighted
    after = compare_models(changed, time_weighted_prior_matches=20).time_weighted
    assert [(p.expected_corners, p.over_probabilities, p.dispersion)
            for p in before if p.match.match_date == target_date] == [
        (p.expected_corners, p.over_probabilities, p.dispersion)
        for p in after if p.match.match_date == target_date
    ]


def test_selection_never_uses_validation_or_test_outcomes():
    earlier = date(2022, 8, 1)
    later = date(2025, 8, 1)
    candidates = {
        5.0: (prediction(earlier, 0.9), prediction(later, 0.01)),
        20.0: (prediction(earlier, 0.6), prediction(later, 0.99)),
    }
    assert select_prior(candidates) == 5.0
    reversed_later = {k: (v[0], replace(v[1], actual_corners=0)) for k, v in candidates.items()}
    assert select_prior(reversed_later) == 5.0


def test_tied_selection_keeps_baseline():
    earlier = prediction(date(2022, 8, 1), 0.6)
    assert select_prior({1.0: (earlier,), 5.0: (earlier,)}) == 5.0


def test_calibration_reports_known_probability_gap():
    first = prediction(date(2022, 8, 1), 0.6)
    second = replace(first, actual_corners=0)
    report = calibration((first, second))
    assert report["mean_expected_calibration_error"] == pytest.approx(0.1)
    assert report["lines"]["4.5"]["bins"][0]["count"] == 2
    assert report["lines"]["4.5"]["bins"][0]["observed_over_rate"] == 0.5


@pytest.mark.parametrize("prior", [0, -1, float("nan"), float("inf")])
def test_invalid_team_priors_are_rejected(prior):
    with pytest.raises(ValueError, match="finite and positive"):
        expected_team_corners([], "A", "B", "home", date(2020, 1, 1),
                              half_life_days=180, team_prior_matches=prior)
