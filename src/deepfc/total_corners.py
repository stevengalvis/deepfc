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


def walk_forward_predictions(
    matches: Iterable[Match],
    evaluation_start: date = DEFAULT_EVALUATION_START,
) -> list[Prediction]:
    """Predict each date using only matches completed on earlier dates."""

    matches_by_date: dict[date, list[Match]] = defaultdict(list)
    for match in matches:
        matches_by_date[match.match_date].append(match)

    historical_total = 0
    historical_matches = 0
    predictions: list[Prediction] = []

    for match_date in sorted(matches_by_date):
        same_date_matches = matches_by_date[match_date]
        if match_date >= evaluation_start and historical_matches:
            expected_total = historical_total / historical_matches
            over_probabilities = {
                line: poisson_over_probability(expected_total, line)
                for line in CORNER_LINES
            }
            predictions.extend(
                Prediction(
                    match=match,
                    expected_total=expected_total,
                    over_probabilities=over_probabilities,
                )
                for match in same_date_matches
            )

        historical_total += sum(match.total_corners for match in same_date_matches)
        historical_matches += len(same_date_matches)

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
        prediction.expected_total
        - prediction.match.total_corners * math.log(prediction.expected_total)
        + math.lgamma(prediction.match.total_corners + 1)
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
        "poisson_negative_log_loss": sum(negative_log_losses) / count,
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
    print(f"Poisson NLL: {evaluation['poisson_negative_log_loss']:.3f}")
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
