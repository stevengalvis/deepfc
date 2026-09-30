"""Run explicitly with the pinned Zeno checkout on PYTHONPATH; no live data."""

from dataclasses import replace
from datetime import date, timedelta
import math

import pytest

from deepfc.match_data import Match
from deepfc.team_corners import walk_forward_prediction_comparison
from experiments.compare_team_corners import (
    compare_predictions, count_loss, observations_from_matches,
    paired_block_bootstrap, summarize, verify_production_parity,
)
from modelfc.corner_recency_experiment import _decay_mean
from modelfc.matches import Venue


def history() -> list[Match]:
    return [Match(date(2019, 1, 1) + timedelta(days=7 * i), "E1", "A", "B",
                  (2, 10, 4, 8)[i % 4], (9, 1, 7, 3)[i % 4])
            for i in range(60)]


def test_common_cohort_keeps_original_deepfc_predictions():
    matches = history()
    models = compare_predictions(matches)
    keys = lambda rows: [(p.match, p.venue) for p in rows]
    assert keys(models["deepfc"]) == keys(models["zeno"]) == keys(models["zeno_decay_180"])
    assert len(models["zeno"]) == 20  # 50 fixtures supply the 100-observation gate.
    retained = {(p.match, p.venue) for p in models["deepfc"]}
    original = walk_forward_prediction_comparison(matches).team_opponent
    assert models["deepfc"] == [p for p in original if (p.match, p.venue) in retained]
    assert [p.dispersion for p in models["zeno"]] == [p.dispersion for p in models["zeno_decay_180"]]


@pytest.mark.parametrize("constant_counts", [False, True])
def test_production_parity_includes_negative_binomial_and_poisson_like_fallback(constant_counts):
    matches = history()
    if constant_counts:
        matches = [replace(m, home_corners=5, away_corners=5) for m in matches]
    rows = compare_predictions(matches)["zeno"]
    result = verify_production_parity(matches, rows)
    assert result["fixtures_checked"] == 10
    assert result["max_absolute_difference"] < 1e-10
    if constant_counts:
        assert rows[0].dispersion == 1e-9
    assert all(math.isfinite(count_loss(p)) for p in rows)


def test_same_date_and_future_results_cannot_change_predictions():
    matches = history()
    target = matches[50]
    same_date = replace(target, away_team="C", home_corners=15, away_corners=1)
    # Give C prior away history so this is also an eligible same-date fixture.
    matches = [replace(m, away_team="C") if i % 2 else m for i, m in enumerate(matches)]
    matches.append(same_date)
    before = compare_predictions(matches)
    changed = [replace(m, home_corners=30, away_corners=25)
               if m.match_date >= target.match_date else m for m in matches]
    after = compare_predictions(changed)
    for name in before:
        first = [p for p in before[name] if p.match.match_date == target.match_date]
        second = [p for p in after[name] if p.match.match_date == target.match_date]
        assert len(first) == len(second) == 4
        assert [(p.expected_corners, p.dispersion, p.over_probabilities) for p in first] == [
            (p.expected_corners, p.dispersion, p.over_probabilities) for p in second
        ]


def test_180_day_weight_is_half_and_prior_uses_effective_sample_size():
    reference = date(2020, 1, 1)
    matches = [Match(reference - timedelta(days=360), "E1", "A", "B", 2, 4),
               Match(reference - timedelta(days=180), "E1", "A", "B", 10, 3)]
    observations = observations_from_matches(matches)
    home = [o for o in observations if o.venue is Venue.HOME]
    away = [o for o in observations if o.venue is Venue.AWAY]
    # Weights 1/4 and 1/2; effective count 3/4, not two full observations.
    weighted_corners = 2 * .25 + 10 * .5
    league = (weighted_corners + 5) / (.75 + 5)
    rate = (weighted_corners + 5 * league) / (.75 + 5)
    actual = _decay_mean(home, home, away, reference, 180, 5)
    assert actual == pytest.approx(rate * rate / league)


def test_venue_gate_excludes_both_teams_without_removing_training_history():
    matches = history()
    matches += [replace(matches[-1], match_date=date(2021, 1, 1) + timedelta(days=i),
                        home_team="New team") for i in range(6)]
    rows = compare_predictions(matches)["zeno"]
    newcomer = [p for p in rows if p.match.home_team == "New team"]
    assert len(newcomer) == 2
    assert {p.match.match_date for p in newcomer} == {date(2021, 1, 6)}


@pytest.mark.parametrize("problem", ["duplicate", "league", "empty"])
def test_invalid_cohorts_are_rejected(problem):
    matches = history()
    if problem == "duplicate":
        matches.append(replace(matches[0], home_corners=20))
    elif problem == "league":
        matches[0] = replace(matches[0], competition="E0")
    else:
        matches = []
    with pytest.raises(ValueError):
        compare_predictions(matches)


def test_identical_models_have_zero_bootstrap_difference():
    rows = compare_predictions(history())["zeno"]
    result = paired_block_bootstrap(rows, rows, samples=50)
    assert result["blocks"] < len(rows) // 2
    for metric in ("mean_brier_score", "count_nll"):
        assert result[metric] == {"lower_95": 0, "upper_95": 0, "fraction_below_zero": 0}
    with pytest.raises(ValueError, match="identical ordered"):
        paired_block_bootstrap(rows, list(reversed(rows)), samples=50)


def test_calibration_bins_account_for_every_prediction_and_under_is_complement():
    rows = compare_predictions(history())["zeno_decay_180"]
    report = summarize(rows)
    for line, metrics in report["lines"].items():
        assert sum(b["count"] for b in metrics["calibration_bins"]) == len(rows)
        under_brier = sum(((1 - p.over_probabilities[float(line)])
                           - (p.actual_corners < float(line))) ** 2 for p in rows) / len(rows)
        assert under_brier == pytest.approx(metrics["brier_score"])
