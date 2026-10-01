"""Test frozen logistic calibration of 180-day team-corner probabilities."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Iterable

from deepfc.football_data_csv import load_football_data_csv
from deepfc.match_data import Match
from deepfc.team_corners import TEAM_CORNER_LINES, TeamCornerPrediction
from experiments.time_decay import compare_models


CALIBRATION_END = date(2023, 7, 1)
VALIDATION_END = date(2024, 7, 1)
PROBABILITY_FLOOR = 1e-12


@dataclass(frozen=True)
class LogisticCalibrator:
    """Map a raw probability through a fitted intercept and log-odds slope."""

    intercept: float
    slope: float

    def transform(self, probability: float) -> float:
        if not 0 <= probability <= 1 or not math.isfinite(probability):
            raise ValueError("probability must be finite and between zero and one")
        bounded = min(max(probability, PROBABILITY_FLOOR), 1 - PROBABILITY_FLOOR)
        linear = self.intercept + self.slope * math.log(bounded / (1 - bounded))
        if linear >= 0:
            return 1 / (1 + math.exp(-linear))
        exponential = math.exp(linear)
        return exponential / (1 + exponential)


def fit_logistic_calibrator(
    probabilities: Iterable[float], outcomes: Iterable[float],
) -> LogisticCalibrator:
    """Fit two-parameter logistic calibration by deterministic Newton steps."""
    pairs = list(zip(probabilities, outcomes, strict=True))
    if not pairs or any(outcome not in (0.0, 1.0) for _, outcome in pairs):
        raise ValueError("nonempty binary calibration observations required")
    logits = []
    for probability, outcome in pairs:
        if not 0 <= probability <= 1 or not math.isfinite(probability):
            raise ValueError("probabilities must be finite and between zero and one")
        bounded = min(max(probability, PROBABILITY_FLOOR), 1 - PROBABILITY_FLOOR)
        logits.append((math.log(bounded / (1 - bounded)), outcome))

    intercept, slope = 0.0, 1.0
    ridge = 1e-9
    for _ in range(100):
        gradient_intercept = ridge * intercept
        gradient_slope = ridge * (slope - 1)
        hessian_intercept = ridge
        hessian_cross = 0.0
        hessian_slope = ridge
        for raw_logit, outcome in logits:
            linear = intercept + slope * raw_logit
            fitted = (
                1 / (1 + math.exp(-linear)) if linear >= 0
                else math.exp(linear) / (1 + math.exp(linear))
            )
            residual = fitted - outcome
            variance = fitted * (1 - fitted)
            gradient_intercept += residual
            gradient_slope += residual * raw_logit
            hessian_intercept += variance
            hessian_cross += variance * raw_logit
            hessian_slope += variance * raw_logit**2
        determinant = hessian_intercept * hessian_slope - hessian_cross**2
        if determinant <= 0 or not math.isfinite(determinant):
            raise ValueError("calibration fit is singular")
        intercept_step = (
            gradient_intercept * hessian_slope
            - gradient_slope * hessian_cross
        ) / determinant
        slope_step = (
            hessian_intercept * gradient_slope
            - hessian_cross * gradient_intercept
        ) / determinant
        intercept -= intercept_step
        slope -= slope_step
        if max(abs(intercept_step), abs(slope_step)) < 1e-12:
            break
    if not math.isfinite(intercept) or not math.isfinite(slope):
        raise ValueError("calibration fit did not produce finite parameters")
    return LogisticCalibrator(intercept, slope)


def fit_by_line(
    predictions: Iterable[TeamCornerPrediction],
) -> dict[float, LogisticCalibrator]:
    """Fit one frozen calibrator for each evaluated market line."""
    observations = list(predictions)
    if not observations:
        raise ValueError("calibration requires predictions")
    return {
        line: fit_logistic_calibrator(
            (item.over_probabilities[line] for item in observations),
            (float(item.actual_corners > line) for item in observations),
        )
        for line in TEAM_CORNER_LINES
    }


def apply_calibration(
    predictions: Iterable[TeamCornerPrediction],
    calibrators: dict[float, LogisticCalibrator],
) -> tuple[TeamCornerPrediction, ...]:
    """Replace market probabilities while preserving count predictions."""
    if set(calibrators) != set(TEAM_CORNER_LINES):
        raise ValueError("calibrators must cover every evaluated line")
    return tuple(
        replace(item, over_probabilities={
            line: calibrators[line].transform(item.over_probabilities[line])
            for line in TEAM_CORNER_LINES
        })
        for item in predictions
    )


def probability_metrics(
    predictions: Iterable[TeamCornerPrediction],
) -> dict[str, object]:
    """Score binary probability quality over all evaluated half-lines."""
    observations = list(predictions)
    if not observations:
        raise ValueError("probability evaluation requires predictions")
    by_line = {}
    all_pairs = []
    for line in TEAM_CORNER_LINES:
        pairs = [
            (item.over_probabilities[line], float(item.actual_corners > line))
            for item in observations
        ]
        all_pairs.extend(pairs)
        by_line[str(line)] = _probability_metrics(pairs)
    return {**_probability_metrics(all_pairs), "lines": by_line}


def _probability_metrics(pairs: list[tuple[float, float]]) -> dict[str, float]:
    brier = sum((probability - outcome) ** 2 for probability, outcome in pairs) / len(pairs)
    log_loss = sum(_binary_log_loss(probability, outcome) for probability, outcome in pairs) / len(pairs)
    bins: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for probability, outcome in pairs:
        bins[min(int(probability * 10), 9)].append((probability, outcome))
    calibration_error = sum(
        len(values) * abs(
            sum(probability for probability, _ in values) / len(values)
            - sum(outcome for _, outcome in values) / len(values)
        )
        for values in bins.values()
    ) / len(pairs)
    return {
        "brier_score": brier,
        "binary_negative_log_loss": log_loss,
        "ten_bin_expected_calibration_error": calibration_error,
    }


def _binary_log_loss(probability: float, outcome: float) -> float:
    bounded = min(max(probability, PROBABILITY_FLOOR), 1 - PROBABILITY_FLOOR)
    return -(outcome * math.log(bounded) + (1 - outcome) * math.log(1 - bounded))


def paired_block_interval(
    baseline: tuple[TeamCornerPrediction, ...],
    candidate: tuple[TeamCornerPrediction, ...],
    *,
    samples: int = 2_000,
    seed: int = 7,
) -> dict[str, dict[str, float]]:
    """Bootstrap paired 28-day blocks for Brier and binary log-loss deltas."""
    if not baseline or len(baseline) != len(candidate) or samples <= 0:
        raise ValueError("matching nonempty predictions and positive samples required")
    blocks: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for before, after in zip(baseline, candidate):
        if (before.match, before.venue) != (after.match, after.venue):
            raise ValueError("predictions must describe identical observations")
        for line in TEAM_CORNER_LINES:
            outcome = float(before.actual_corners > line)
            raw = before.over_probabilities[line]
            calibrated = after.over_probabilities[line]
            brier_delta = (calibrated - outcome) ** 2 - (raw - outcome) ** 2
            log_delta = (
                _binary_log_loss(calibrated, outcome)
                - _binary_log_loss(raw, outcome)
            )
            blocks[before.match.match_date.toordinal() // 28].append((brier_delta, log_delta))
    block_totals = [
        (len(values), sum(value[0] for value in values), sum(value[1] for value in values))
        for values in blocks.values()
    ]
    generator = random.Random(seed)
    draws = {"brier_score": [], "binary_negative_log_loss": []}
    for _ in range(samples):
        selected = generator.choices(block_totals, k=len(block_totals))
        count = sum(item[0] for item in selected)
        draws["brier_score"].append(sum(item[1] for item in selected) / count)
        draws["binary_negative_log_loss"].append(sum(item[2] for item in selected) / count)
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
    raw = probability_metrics(baseline)
    calibrated = probability_metrics(candidate)
    metrics = ("brier_score", "binary_negative_log_loss", "ten_bin_expected_calibration_error")
    return {
        "team_observations": len(baseline),
        "market_line_observations": len(baseline) * len(TEAM_CORNER_LINES),
        "raw": raw,
        "calibrated": calibrated,
        "calibrated_minus_raw": {name: calibrated[name] - raw[name] for name in metrics},
        "paired_28_day_intervals": paired_block_interval(baseline, candidate),
    }


def run_experiment(matches: Iterable[Match]) -> dict[str, object]:
    """Fit before 2023/24 and evaluate two fixed later periods."""
    predictions = compare_models(matches).time_weighted
    training = tuple(item for item in predictions if item.match.match_date < CALIBRATION_END)
    validation = tuple(
        item for item in predictions
        if CALIBRATION_END <= item.match.match_date < VALIDATION_END
    )
    test = tuple(item for item in predictions if item.match.match_date >= VALIDATION_END)
    calibrators = fit_by_line(training)
    calibrated_validation = apply_calibration(validation, calibrators)
    calibrated_test = apply_calibration(test, calibrators)
    return {
        "settings": {
            "competition": "E1",
            "model": "fixed_180_day_team_corners",
            "method": "line_specific_logistic_calibration",
            "calibration_end_exclusive": CALIBRATION_END.isoformat(),
            "validation_end_exclusive": VALIDATION_END.isoformat(),
            "lines": TEAM_CORNER_LINES,
            "later_seasons_previously_inspected": True,
        },
        "fitted_calibrators": {
            str(line): {"intercept": model.intercept, "slope": model.slope}
            for line, model in calibrators.items()
        },
        "training_metrics": {
            "raw": probability_metrics(training),
            "calibrated": probability_metrics(apply_calibration(training, calibrators)),
        },
        "validation_2023_24": _comparison(validation, calibrated_validation),
        "retrospective_test_2024_26": _comparison(test, calibrated_test),
        "test_by_season": {
            str(year): _comparison(
                tuple(item for item in test if _season(item) == year),
                tuple(item for item in calibrated_test if _season(item) == year),
            )
            for year in sorted({_season(item) for item in test})
        },
        "test_by_venue": {
            venue: _comparison(
                tuple(item for item in test if item.venue == venue),
                tuple(item for item in calibrated_test if item.venue == venue),
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
