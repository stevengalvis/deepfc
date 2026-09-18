"""Chronological baseline and evaluation for full-match total corners."""

import argparse
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from deepfc.football_data_csv import LoadResult, load_football_data_csv
from deepfc.match_data import Match


CORNER_LINES = (8.5, 9.5, 10.5, 11.5)
CHAMPIONSHIP_CODE = "E1"
DEFAULT_EVALUATION_START = date(2018, 7, 1)


@dataclass(frozen=True)
class Prediction:
    """One pre-match prediction produced during walk-forward evaluation."""

    match: Match
    expected_total: float
    over_probabilities: dict[float, float]
    negative_binomial_dispersion: float


def poisson_over_probability(expected_total: float, line: float) -> float:
    """Return P(total corners > line) under a Poisson distribution."""

    if expected_total <= 0:
        raise ValueError("expected_total must be greater than zero")
    if line < 0 or not math.isclose(line % 1, 0.5):
        raise ValueError("line must be a non-negative half line")

    largest_under_total = math.floor(line)
    probability = math.exp(-expected_total)
    cumulative_probability = probability
    for total in range(1, largest_under_total + 1):
        probability *= expected_total / total
        cumulative_probability += probability
    return max(0.0, min(1.0, 1.0 - cumulative_probability))


def _negative_binomial_parameters(
    expected_total: float,
    negative_binomial_dispersion: float,
) -> tuple[float, float]:
    """Convert a mean and dispersion into Negative Binomial parameters."""

    distribution_shape = 1.0 / negative_binomial_dispersion
    distribution_probability = distribution_shape / (
        distribution_shape + expected_total
    )
    return distribution_shape, distribution_probability


def negative_binomial_over_probability(
    expected_total: float,
    line: float,
    negative_binomial_dispersion: float,
) -> float:
    """Return P(total corners > line) under a Negative Binomial distribution."""

    if expected_total <= 0:
        raise ValueError("expected_total must be greater than zero")
    if line < 0 or not math.isclose(line % 1, 0.5):
        raise ValueError("line must be a non-negative half line")
    if negative_binomial_dispersion < 0:
        raise ValueError("negative_binomial_dispersion must not be negative")
    if math.isclose(negative_binomial_dispersion, 0.0, abs_tol=1e-12):
        return poisson_over_probability(expected_total, line)

    distribution_shape, distribution_probability = (
        _negative_binomial_parameters(
            expected_total,
            negative_binomial_dispersion,
        )
    )
    probability = distribution_probability**distribution_shape
    cumulative_probability = probability
    for total in range(1, math.floor(line) + 1):
        probability *= (
            (total - 1 + distribution_shape) / total
        ) * (1.0 - distribution_probability)
        cumulative_probability += probability
    return max(0.0, min(1.0, 1.0 - cumulative_probability))


def negative_binomial_negative_log_loss(
    actual_total: int,
    expected_total: float,
    negative_binomial_dispersion: float,
) -> float:
    """Return the Negative Binomial negative log likelihood for one total."""

    if isinstance(actual_total, bool) or not isinstance(actual_total, int):
        raise ValueError("actual_total must be a non-negative integer")
    if actual_total < 0:
        raise ValueError("actual_total must be a non-negative integer")
    if expected_total <= 0:
        raise ValueError("expected_total must be greater than zero")
    if negative_binomial_dispersion < 0:
        raise ValueError("negative_binomial_dispersion must not be negative")
    if math.isclose(negative_binomial_dispersion, 0.0, abs_tol=1e-12):
        return (
            expected_total
            - actual_total * math.log(expected_total)
            + math.lgamma(actual_total + 1)
        )

    distribution_shape, distribution_probability = (
        _negative_binomial_parameters(
            expected_total,
            negative_binomial_dispersion,
        )
    )
    log_probability = (
        math.lgamma(actual_total + distribution_shape)
        - math.lgamma(distribution_shape)
        - math.lgamma(actual_total + 1)
        + distribution_shape * math.log(distribution_probability)
        + actual_total * math.log1p(-distribution_probability)
    )
    return -log_probability


def _estimate_negative_binomial_dispersion(
    match_count: int,
    corner_sum: int,
    squared_corner_sum: int,
) -> float:
    """Estimate prior-match overdispersion with the method of moments."""

    if match_count < 2:
        return 0.0
    expected_total = corner_sum / match_count
    if expected_total <= 0:
        return 0.0
    sample_variance = (
        squared_corner_sum - corner_sum**2 / match_count
    ) / (match_count - 1)
    return max(0.0, (sample_variance - expected_total) / expected_total**2)


def walk_forward_predictions(
    matches: Iterable[Match],
    evaluation_start: date = DEFAULT_EVALUATION_START,
) -> list[Prediction]:
    """Predict each date using only matches completed on earlier dates."""

    matches_by_date: dict[date, list[Match]] = defaultdict(list)
    for match in matches:
        matches_by_date[match.match_date].append(match)

    historical_corner_sum = 0
    historical_squared_corner_sum = 0
    historical_match_count = 0
    predictions: list[Prediction] = []

    for match_date in sorted(matches_by_date):
        same_date_matches = matches_by_date[match_date]
        if match_date >= evaluation_start and historical_match_count:
            expected_total = historical_corner_sum / historical_match_count
            negative_binomial_dispersion = _estimate_negative_binomial_dispersion(
                historical_match_count,
                historical_corner_sum,
                historical_squared_corner_sum,
            )
            over_probabilities = {
                line: negative_binomial_over_probability(
                    expected_total,
                    line,
                    negative_binomial_dispersion,
                )
                for line in CORNER_LINES
            }
            predictions.extend(
                Prediction(
                    match=match,
                    expected_total=expected_total,
                    over_probabilities=over_probabilities,
                    negative_binomial_dispersion=negative_binomial_dispersion,
                )
                for match in same_date_matches
            )

        historical_corner_sum += sum(
            match.total_corners for match in same_date_matches
        )
        historical_squared_corner_sum += sum(
            match.total_corners**2 for match in same_date_matches
        )
        historical_match_count += len(same_date_matches)

    return predictions


def evaluate_predictions(predictions: Iterable[Prediction]) -> dict[str, object]:
    """Calculate count and probability metrics as a JSON-serializable dict."""

    prediction_list = list(predictions)
    if not prediction_list:
        raise ValueError("no predictions are available for evaluation")

    count = len(prediction_list)
    absolute_errors = [
        abs(prediction.expected_total - prediction.match.total_corners)
        for prediction in prediction_list
    ]
    squared_errors = [error**2 for error in absolute_errors]
    negative_log_losses = [
        negative_binomial_negative_log_loss(
            prediction.match.total_corners,
            prediction.expected_total,
            prediction.negative_binomial_dispersion,
        )
        for prediction in prediction_list
    ]

    line_metrics: dict[str, dict[str, float]] = {}
    for line in CORNER_LINES:
        predicted_over = [
            prediction.over_probabilities[line] for prediction in prediction_list
        ]
        actual_over = [
            float(prediction.match.total_corners > line)
            for prediction in prediction_list
        ]
        mean_predicted_over = sum(predicted_over) / count
        actual_over_rate = sum(actual_over) / count
        line_metrics[str(line)] = {
            "brier_score": sum(
                (probability - outcome) ** 2
                for probability, outcome in zip(predicted_over, actual_over)
            )
            / count,
            "mean_predicted_over_probability": mean_predicted_over,
            "mean_predicted_under_probability": 1.0 - mean_predicted_over,
            "actual_over_rate": actual_over_rate,
            "actual_under_rate": 1.0 - actual_over_rate,
        }

    return {
        "evaluated_matches": count,
        "mean_predicted_total": sum(
            prediction.expected_total for prediction in prediction_list
        )
        / count,
        "mean_actual_total": sum(
            prediction.match.total_corners for prediction in prediction_list
        )
        / count,
        "mae": sum(absolute_errors) / count,
        "rmse": math.sqrt(sum(squared_errors) / count),
        "negative_binomial_negative_log_loss": (
            sum(negative_log_losses) / count
        ),
        "mean_brier_score": sum(
            metrics["brier_score"] for metrics in line_metrics.values()
        )
        / len(line_metrics),
        "lines": line_metrics,
    }


def run_evaluation(
    csv_paths: Iterable[str | Path],
    evaluation_start: date = DEFAULT_EVALUATION_START,
) -> dict[str, object]:
    """Load CSVs, run walk-forward predictions, and return the evaluation."""

    loaded: LoadResult = load_football_data_csv(csv_paths)
    unexpected_competitions = {
        match.competition
        for match in loaded.matches
        if match.competition != CHAMPIONSHIP_CODE
    }
    if unexpected_competitions:
        unexpected = ", ".join(sorted(unexpected_competitions))
        raise ValueError(
            f"V1 supports Championship rows ({CHAMPIONSHIP_CODE}) only; found: "
            f"{unexpected}"
        )

    metrics = evaluate_predictions(
        walk_forward_predictions(loaded.matches, evaluation_start)
    )
    return {
        "competition": "EFL Championship",
        "target": "full_match_total_corners",
        "evaluation_start": evaluation_start.isoformat(),
        "data_quality": {
            "rows_read": loaded.rows_read,
            "rows_loaded": loaded.rows_loaded,
            "rows_without_corner_results": loaded.rows_without_corner_results,
        },
        "evaluation": metrics,
    }


def _print_summary(result: dict[str, object]) -> None:
    evaluation = result["evaluation"]
    assert isinstance(evaluation, dict)
    print("DeepFC Championship full-match total corners baseline")
    print(f"Evaluated matches: {evaluation['evaluated_matches']}")
    print(f"MAE: {evaluation['mae']:.3f}")
    print(f"RMSE: {evaluation['rmse']:.3f}")
    print(
        "Negative Binomial NLL: "
        f"{evaluation['negative_binomial_negative_log_loss']:.3f}"
    )
    print("\nJSON result")
    print(json.dumps(result, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate a Championship full-match total-corners baseline."
    )
    parser.add_argument("csv_paths", nargs="+", type=Path)
    parser.add_argument(
        "--evaluation-start",
        type=date.fromisoformat,
        default=DEFAULT_EVALUATION_START,
        help="First date to score, in YYYY-MM-DD format (default: 2018-07-01).",
    )
    args = parser.parse_args()
    _print_summary(run_evaluation(args.csv_paths, args.evaluation_start))


if __name__ == "__main__":
    main()
