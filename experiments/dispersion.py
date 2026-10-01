"""Test venue and recency choices for 180-day model dispersion."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date
import hashlib
from itertools import groupby
import json
import math
from pathlib import Path
import random
from typing import Iterable, Literal

from deepfc.corner_distribution import (
    estimate_dispersion,
    negative_binomial_negative_log_loss,
    negative_binomial_over_probability,
)
from deepfc.football_data_csv import load_football_data_csv
from deepfc.match_data import Match
from deepfc.team_corners import TEAM_CORNER_LINES, TeamCornerPrediction, evaluate_predictions
from experiments.time_decay import (
    EVALUATION_START,
    HALF_LIFE_DAYS,
    CornerObservation,
    compare_models,
    time_weight,
)


CALIBRATION_END = date(2023, 7, 1)
VALIDATION_END = date(2024, 7, 1)
Venue = Literal["home", "away"]
ALTERNATIVES = ("venue_all_history", "pooled_180_day", "venue_180_day")


@dataclass(frozen=True)
class DispersionComparison:
    """Predictions sharing identical fixtures, means and actual counts."""

    predictions: dict[str, tuple[TeamCornerPrediction, ...]]


def weighted_dispersion(
    history: Iterable[CornerObservation],
    prediction_date: date,
    *,
    venue: Venue | None = None,
    half_life_days: int | None = None,
) -> float:
    """Estimate NB2 dispersion with optional venue filtering and time weights."""
    observations = [item for item in history if venue is None or item.venue == venue]
    if any(item.match.match_date >= prediction_date for item in observations):
        raise ValueError("historical matches must precede the prediction date")
    if half_life_days is not None and half_life_days <= 0:
        raise ValueError("half_life_days must be positive")
    if len(observations) < 2:
        return 0.0
    if half_life_days is None:
        return estimate_dispersion(
            len(observations),
            sum(item.corners_for for item in observations),
            sum(item.corners_for**2 for item in observations),
        )

    weighted_count = weighted_square_count = weighted_sum = weighted_squared_sum = 0.0
    for item in observations:
        weight = time_weight(
            (prediction_date - item.match.match_date).days,
            half_life_days,
        )
        weighted_count += weight
        weighted_square_count += weight**2
        weighted_sum += weight * item.corners_for
        weighted_squared_sum += weight * item.corners_for**2
    variance_denominator = weighted_count - weighted_square_count / weighted_count
    if variance_denominator <= 0:
        return 0.0
    mean = weighted_sum / weighted_count
    if mean <= 0:
        return 0.0
    variance = (weighted_squared_sum - weighted_sum**2 / weighted_count) / variance_denominator
    return max(0.0, (variance - mean) / mean**2)


def compare_dispersion_models(matches: Iterable[Match]) -> DispersionComparison:
    """Apply four dispersion methods to one fixed set of 180-day means."""
    ordered = sorted(matches, key=lambda item: item.match_date)
    if not ordered or any(item.competition != "E1" for item in ordered):
        raise ValueError("provide nonempty Championship (E1) history only")
    fixed = compare_models(ordered).time_weighted
    baseline_by_key = {(item.match, item.venue): item for item in fixed}
    candidate_lists = {name: [] for name in ALTERNATIVES}
    history: list[CornerObservation] = []

    for match_date, date_group in groupby(ordered, key=lambda item: item.match_date):
        matches_on_date = list(date_group)
        eligible = [
            item for item in matches_on_date
            if (item, "home") in baseline_by_key
        ]
        if eligible:
            dispersion = {
                "venue_all_history": {
                    venue: weighted_dispersion(history, match_date, venue=venue)
                    for venue in ("home", "away")
                },
                "pooled_180_day": {
                    venue: weighted_dispersion(
                        history, match_date, half_life_days=HALF_LIFE_DAYS,
                    )
                    for venue in ("home", "away")
                },
                "venue_180_day": {
                    venue: weighted_dispersion(
                        history, match_date, venue=venue,
                        half_life_days=HALF_LIFE_DAYS,
                    )
                    for venue in ("home", "away")
                },
            }
            for match in eligible:
                for venue in ("home", "away"):
                    baseline = baseline_by_key[match, venue]
                    for name in ALTERNATIVES:
                        value = dispersion[name][venue]
                        candidate_lists[name].append(replace(
                            baseline,
                            dispersion=value,
                            over_probabilities={
                                line: negative_binomial_over_probability(
                                    baseline.expected_corners, line, value,
                                )
                                for line in TEAM_CORNER_LINES
                            },
                        ))

        for match in matches_on_date:
            history.extend((
                CornerObservation(
                    match, match.home_team, match.away_team, "home",
                    match.home_corners, match.away_corners,
                ),
                CornerObservation(
                    match, match.away_team, match.home_team, "away",
                    match.away_corners, match.home_corners,
                ),
            ))

    predictions = {"pooled_all_history": fixed}
    predictions.update({name: tuple(values) for name, values in candidate_lists.items()})
    identities = [(item.match, item.venue) for item in fixed]
    if any([(item.match, item.venue) for item in values] != identities
           for values in predictions.values()):
        raise ValueError("all dispersion methods must score identical observations")
    return DispersionComparison(predictions)


def select_alternative(
    predictions: dict[str, tuple[TeamCornerPrediction, ...]],
) -> str:
    """Select the alternative with the best earlier-season mean Brier score."""
    return min(
        ALTERNATIVES,
        key=lambda name: evaluate_predictions(
            item for item in predictions[name]
            if item.match.match_date < CALIBRATION_END
        )["mean_brier_score"],
    )


def paired_block_intervals(
    baseline: tuple[TeamCornerPrediction, ...],
    candidate: tuple[TeamCornerPrediction, ...],
    *,
    samples: int = 2_000,
    seed: int = 7,
) -> dict[str, dict[str, float]]:
    """Bootstrap paired 28-day blocks for Brier and count-NLL deltas."""
    if not baseline or len(baseline) != len(candidate) or samples <= 0:
        raise ValueError("matching nonempty predictions and positive samples required")
    blocks: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for before, after in zip(baseline, candidate):
        if (before.match, before.venue) != (after.match, after.venue):
            raise ValueError("predictions must describe identical observations")
        brier_delta = sum(
            (after.over_probabilities[line] - (after.actual_corners > line)) ** 2
            - (before.over_probabilities[line] - (before.actual_corners > line)) ** 2
            for line in TEAM_CORNER_LINES
        ) / len(TEAM_CORNER_LINES)
        nll_delta = (
            negative_binomial_negative_log_loss(
                after.actual_corners, after.expected_corners, after.dispersion,
            )
            - negative_binomial_negative_log_loss(
                before.actual_corners, before.expected_corners, before.dispersion,
            )
        )
        blocks[before.match.match_date.toordinal() // 28].append((brier_delta, nll_delta))
    totals = [
        (len(values), sum(item[0] for item in values), sum(item[1] for item in values))
        for values in blocks.values()
    ]
    generator = random.Random(seed)
    draws = {"mean_brier_score": [], "negative_binomial_negative_log_loss": []}
    for _ in range(samples):
        selected = generator.choices(totals, k=len(totals))
        count = sum(item[0] for item in selected)
        draws["mean_brier_score"].append(sum(item[1] for item in selected) / count)
        draws["negative_binomial_negative_log_loss"].append(
            sum(item[2] for item in selected) / count
        )
    return {name: _interval(values) for name, values in draws.items()}


def _interval(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "lower_95": ordered[int(0.025 * (len(ordered) - 1))],
        "upper_95": ordered[int(0.975 * (len(ordered) - 1))],
        "fraction_below_zero": sum(value < 0 for value in values) / len(values),
    }


def _comparison(
    baseline: tuple[TeamCornerPrediction, ...],
    candidate: tuple[TeamCornerPrediction, ...],
) -> dict[str, object]:
    raw = evaluate_predictions(baseline)
    changed = evaluate_predictions(candidate)
    metric_names = (
        "mae", "rmse", "negative_binomial_negative_log_loss", "mean_brier_score",
    )
    return {
        "baseline": raw,
        "candidate": changed,
        "candidate_minus_baseline": {
            name: changed[name] - raw[name] for name in metric_names
        },
        "paired_28_day_intervals": paired_block_intervals(baseline, candidate),
    }


def run_experiment(matches: Iterable[Match]) -> dict[str, object]:
    """Select before 2023/24 and evaluate the frozen dispersion alternative."""
    compared = compare_dispersion_models(matches).predictions
    baseline = compared["pooled_all_history"]
    selected_name = select_alternative(compared)
    selected = compared[selected_name]
    tuning = lambda item: item.match.match_date < CALIBRATION_END
    validation = lambda item: CALIBRATION_END <= item.match.match_date < VALIDATION_END
    test = lambda item: item.match.match_date >= VALIDATION_END
    return {
        "settings": {
            "competition": "E1",
            "mean_model": "fixed_180_day_team_corners",
            "baseline_dispersion": "pooled_all_history",
            "alternative_dispersion_methods": ALTERNATIVES,
            "selection_metric": "mean_brier_score",
            "selection_end_exclusive": CALIBRATION_END.isoformat(),
            "validation_end_exclusive": VALIDATION_END.isoformat(),
            "selected_alternative": selected_name,
            "later_seasons_previously_inspected": True,
        },
        "tuning": {
            name: evaluate_predictions(item for item in values if tuning(item))
            for name, values in compared.items()
        },
        "validation_2023_24": _comparison(
            tuple(item for item in baseline if validation(item)),
            tuple(item for item in selected if validation(item)),
        ),
        "retrospective_test_2024_26": _comparison(
            tuple(item for item in baseline if test(item)),
            tuple(item for item in selected if test(item)),
        ),
        "test_by_season": {
            str(year): _comparison(
                tuple(item for item in baseline if _season(item) == year),
                tuple(item for item in selected if _season(item) == year),
            )
            for year in sorted({_season(item) for item in baseline if test(item)})
        },
        "test_by_venue": {
            venue: _comparison(
                tuple(item for item in baseline if test(item) and item.venue == venue),
                tuple(item for item in selected if test(item) and item.venue == venue),
            )
            for venue in ("home", "away")
        },
    }


def _season(prediction: TeamCornerPrediction) -> int:
    match_date = prediction.match.match_date
    return match_date.year - int(match_date.month < 7)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_paths", nargs="+", type=Path)
    args = parser.parse_args()
    loaded = load_football_data_csv(args.csv_paths)
    result = run_experiment(loaded.matches)
    result["data_quality"] = {
        "rows_read": loaded.rows_read,
        "rows_loaded": loaded.rows_loaded,
        "rows_without_corner_results": loaded.rows_without_corner_results,
    }
    result["source_files"] = [
        {"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in args.csv_paths
    ]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
