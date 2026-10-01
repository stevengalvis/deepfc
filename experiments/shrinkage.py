"""Test team-prior strength without changing the fixed 180-day model otherwise."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Iterable

from deepfc.football_data_csv import load_football_data_csv
from deepfc.match_data import Match
from deepfc.team_corners import TEAM_CORNER_LINES, TeamCornerPrediction, evaluate_predictions
from experiments.time_decay import compare_models, paired_block_brier_interval

PRIOR_MATCH_COUNTS = (1.0, 2.0, 5.0, 10.0, 20.0)
BASELINE_PRIOR = 5.0
VALIDATION_START = date(2023, 7, 1)
TEST_START = date(2024, 7, 1)


def calibration(predictions: Iterable[TeamCornerPrediction]) -> dict:
    """Fixed ten-bin reliability diagnostics, separately for each half-line."""
    observations = list(predictions)
    if not observations:
        raise ValueError("calibration needs predictions")
    lines = {}
    for line in TEAM_CORNER_LINES:
        bins = defaultdict(list)
        for prediction in observations:
            probability = prediction.over_probabilities[line]
            bins[min(int(probability * 10), 9)].append(
                (probability, float(prediction.actual_corners > line))
            )
        rows = []
        for index, pairs in sorted(bins.items()):
            rows.append({
                "lower_bound": index / 10,
                "upper_bound": (index + 1) / 10,
                "count": len(pairs),
                "mean_probability": sum(p for p, _ in pairs) / len(pairs),
                "observed_over_rate": sum(y for _, y in pairs) / len(pairs),
            })
        lines[str(line)] = {
            "bins": rows,
            "expected_calibration_error": sum(
                row["count"] * abs(row["mean_probability"] - row["observed_over_rate"])
                for row in rows
            ) / len(observations),
        }
    return {
        "mean_expected_calibration_error": sum(
            line["expected_calibration_error"] for line in lines.values()
        ) / len(lines),
        "lines": lines,
    }


def select_prior(predictions: dict[float, tuple[TeamCornerPrediction, ...]]) -> float:
    """Choose by earlier-season Brier only; prefer baseline on an exact tie."""
    scores = {}
    for prior, values in predictions.items():
        tuning = [p for p in values if p.match.match_date < VALIDATION_START]
        scores[prior] = evaluate_predictions(tuning)["mean_brier_score"]
    return min(scores, key=lambda prior: (scores[prior], prior != BASELINE_PRIOR, prior))


def _comparison(baseline, candidate) -> dict:
    baseline_metrics = evaluate_predictions(baseline)
    candidate_metrics = evaluate_predictions(candidate)
    metrics = ("mae", "rmse", "negative_binomial_negative_log_loss", "mean_brier_score")
    return {
        "baseline": baseline_metrics,
        "candidate": candidate_metrics,
        "candidate_minus_baseline": {
            key: candidate_metrics[key] - baseline_metrics[key] for key in metrics
        },
        "calibration": {"baseline": calibration(baseline), "candidate": calibration(candidate)},
        "paired_28_day_brier_interval": paired_block_brier_interval(
            tuple(baseline), tuple(candidate),
        ),
    }


def run_experiment(matches: Iterable[Match]) -> dict:
    """Tune before 2023/24; report validation and later retrospective test separately."""
    matches = list(matches)
    predictions = {}
    for prior in PRIOR_MATCH_COUNTS:
        predictions[prior] = compare_models(
            matches, time_weighted_prior_matches=prior,
        ).time_weighted
    baseline = predictions[BASELINE_PRIOR]
    identities = [(p.match, p.venue) for p in baseline]
    if any([(p.match, p.venue) for p in values] != identities for values in predictions.values()):
        raise ValueError("all priors must score the same observations")
    selected = select_prior(predictions)
    candidate = predictions[selected]
    validation = lambda p: VALIDATION_START <= p.match.match_date < TEST_START
    retrospective_test = lambda p: p.match.match_date >= TEST_START
    report = {
        "settings": {
            "competition": "E1", "half_life_days": 180,
            "baseline_team_prior_matches": BASELINE_PRIOR,
            "league_smoothing_matches": 5.0,
            "candidate_team_prior_matches": PRIOR_MATCH_COUNTS,
            "selection_metric": "mean_brier_score",
            "tuning_end_exclusive": VALIDATION_START.isoformat(),
            "validation_end_exclusive": TEST_START.isoformat(),
            "selected_team_prior_matches": selected,
            "all_seasons_previously_inspected": True,
        },
        "tuning": {
            str(prior): evaluate_predictions(p for p in values if p.match.match_date < VALIDATION_START)
            for prior, values in predictions.items()
        },
        "validation_2023_24": _comparison(
            [p for p in baseline if validation(p)], [p for p in candidate if validation(p)],
        ),
        "retrospective_test_2024_26": _comparison(
            [p for p in baseline if retrospective_test(p)],
            [p for p in candidate if retrospective_test(p)],
        ),
    }
    season = lambda p: p.match.match_date.year - int(p.match.match_date.month < 7)
    report["test_by_season"] = {
        str(year): _comparison(
            [p for p in baseline if season(p) == year],
            [p for p in candidate if season(p) == year],
        )
        for year in sorted({season(p) for p in baseline if retrospective_test(p)})
    }
    report["test_by_venue"] = {
        venue: _comparison(
            [p for p in baseline if retrospective_test(p) and p.venue == venue],
            [p for p in candidate if retrospective_test(p) and p.venue == venue],
        )
        for venue in ("home", "away")
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_paths", nargs="+", type=Path)
    args = parser.parse_args()
    loaded = load_football_data_csv(args.csv_paths)
    result = run_experiment(loaded.matches)
    result["data_quality"] = {
        "rows_read": loaded.rows_read, "rows_loaded": loaded.rows_loaded,
        "rows_without_corner_results": loaded.rows_without_corner_results,
    }
    result["source_files"] = [
        {"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in args.csv_paths
    ]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
