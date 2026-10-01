"""Test attack and concession signal strength in the 180-day model."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
import hashlib
import json
from pathlib import Path
import random
from typing import Iterable

from deepfc.corner_distribution import negative_binomial_negative_log_loss
from deepfc.football_data_csv import load_football_data_csv
from deepfc.match_data import Match
from deepfc.team_corners import TEAM_CORNER_LINES, TeamCornerPrediction, evaluate_predictions
from experiments.time_decay import compare_models


SELECTION_END = date(2023, 7, 1)
VALIDATION_END = date(2024, 7, 1)
BASELINE = (1.0, 1.0)
STRENGTHS = (0.5, 0.75, 1.0)
ALTERNATIVES = tuple(
    (attack, concession)
    for attack in STRENGTHS
    for concession in STRENGTHS
    if (attack, concession) != BASELINE
)


def model_name(strengths: tuple[float, float]) -> str:
    """Return a stable label for attack and concession exponents."""
    return f"attack_{strengths[0]:g}_concession_{strengths[1]:g}"


def generate_predictions(
    matches: Iterable[Match],
) -> dict[tuple[float, float], tuple[TeamCornerPrediction, ...]]:
    """Generate the fixed baseline and a small predeclared exponent grid."""
    match_list = list(matches)
    settings = (BASELINE,) + ALTERNATIVES
    predictions = {
        strengths: compare_models(
            match_list,
            time_weighted_attack_strength=strengths[0],
            time_weighted_concession_strength=strengths[1],
        ).time_weighted
        for strengths in settings
    }
    baseline_identity = [
        (item.match, item.venue, item.actual_corners, item.dispersion)
        for item in predictions[BASELINE]
    ]
    if any([
        (item.match, item.venue, item.actual_corners, item.dispersion)
        for item in values
    ] != baseline_identity for values in predictions.values()):
        raise ValueError("all signal strengths must score identical observations")
    return predictions


def select_alternative(
    predictions: dict[tuple[float, float], tuple[TeamCornerPrediction, ...]],
) -> tuple[float, float]:
    """Choose the alternative with the best earlier-season mean Brier score."""
    return min(
        ALTERNATIVES,
        key=lambda strengths: (
            evaluate_predictions(
                item for item in predictions[strengths]
                if item.match.match_date < SELECTION_END
            )["mean_brier_score"],
            strengths,
        ),
    )


def paired_block_intervals(
    baseline: tuple[TeamCornerPrediction, ...],
    candidate: tuple[TeamCornerPrediction, ...],
    *,
    samples: int = 2_000,
    seed: int = 7,
) -> dict[str, dict[str, float]]:
    """Bootstrap paired 28-day blocks for Brier, count NLL and MAE deltas."""
    if not baseline or len(baseline) != len(candidate) or samples <= 0:
        raise ValueError("matching nonempty predictions and positive samples required")
    blocks: dict[int, list[tuple[float, float, float]]] = defaultdict(list)
    for before, after in zip(baseline, candidate):
        if (before.match, before.venue) != (after.match, after.venue):
            raise ValueError("predictions must describe identical observations")
        outcome = before.actual_corners
        brier_delta = sum(
            (after.over_probabilities[line] - (outcome > line)) ** 2
            - (before.over_probabilities[line] - (outcome > line)) ** 2
            for line in TEAM_CORNER_LINES
        ) / len(TEAM_CORNER_LINES)
        nll_delta = (
            negative_binomial_negative_log_loss(
                outcome, after.expected_corners, after.dispersion,
            )
            - negative_binomial_negative_log_loss(
                outcome, before.expected_corners, before.dispersion,
            )
        )
        mae_delta = (
            abs(outcome - after.expected_corners)
            - abs(outcome - before.expected_corners)
        )
        blocks[before.match.match_date.toordinal() // 28].append(
            (brier_delta, nll_delta, mae_delta)
        )
    totals = [
        (
            len(values),
            sum(item[0] for item in values),
            sum(item[1] for item in values),
            sum(item[2] for item in values),
        )
        for values in blocks.values()
    ]
    generator = random.Random(seed)
    draws = {
        "mean_brier_score": [],
        "negative_binomial_negative_log_loss": [],
        "mae": [],
    }
    for _ in range(samples):
        selected = generator.choices(totals, k=len(totals))
        count = sum(item[0] for item in selected)
        for index, name in enumerate(draws, start=1):
            draws[name].append(sum(item[index] for item in selected) / count)
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
    """Select before 2023/24 and evaluate one frozen signal-strength candidate."""
    predictions = generate_predictions(matches)
    selected = select_alternative(predictions)
    baseline_values = predictions[BASELINE]
    candidate_values = predictions[selected]
    tuning = lambda item: item.match.match_date < SELECTION_END
    validation = lambda item: SELECTION_END <= item.match.match_date < VALIDATION_END
    test = lambda item: item.match.match_date >= VALIDATION_END
    return {
        "settings": {
            "competition": "E1",
            "model": "fixed_180_day_team_corners",
            "baseline_attack_strength": BASELINE[0],
            "baseline_concession_strength": BASELINE[1],
            "candidate_strengths": ALTERNATIVES,
            "selection_metric": "mean_brier_score",
            "selection_end_exclusive": SELECTION_END.isoformat(),
            "validation_end_exclusive": VALIDATION_END.isoformat(),
            "selected_attack_strength": selected[0],
            "selected_concession_strength": selected[1],
            "later_seasons_previously_inspected": True,
        },
        "tuning": {
            model_name(strengths): evaluate_predictions(
                item for item in values if tuning(item)
            )
            for strengths, values in predictions.items()
        },
        "validation_2023_24": _comparison(
            tuple(item for item in baseline_values if validation(item)),
            tuple(item for item in candidate_values if validation(item)),
        ),
        "retrospective_test_2024_26": _comparison(
            tuple(item for item in baseline_values if test(item)),
            tuple(item for item in candidate_values if test(item)),
        ),
        "test_by_season": {
            str(year): _comparison(
                tuple(item for item in baseline_values if _season(item) == year),
                tuple(item for item in candidate_values if _season(item) == year),
            )
            for year in sorted({_season(item) for item in baseline_values if test(item)})
        },
        "test_by_venue": {
            venue: _comparison(
                tuple(item for item in baseline_values if test(item) and item.venue == venue),
                tuple(item for item in candidate_values if test(item) and item.venue == venue),
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
