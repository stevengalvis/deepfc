"""Walk-forward models and evaluation for individual team corner totals."""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Literal, Sequence

from deepfc.corner_distribution import (
    estimate_dispersion,
    negative_binomial_negative_log_loss,
    negative_binomial_over_probability,
)
from deepfc.football_data_csv import LoadResult, load_football_data_csv
from deepfc.match_data import Match
from deepfc.total_corners import CHAMPIONSHIP_CODE, DEFAULT_EVALUATION_START


TEAM_CORNER_LINES = (3.5, 4.5, 5.5, 6.5)
DEFAULT_PRIOR_MATCHES = 5
Venue = Literal["home", "away"]


@dataclass
class TeamCornerHistory:
    """Corners won and allowed by a team in one venue role."""

    matches: int = 0
    corners_won: int = 0
    corners_allowed: int = 0

    def record(self, corners_won: int, corners_allowed: int) -> None:
        self.matches += 1
        self.corners_won += corners_won
        self.corners_allowed += corners_allowed


@dataclass(frozen=True)
class TeamCornerPrediction:
    """One pre-match prediction for one team's full-match corner count."""

    match: Match
    team: str
    venue: Venue
    expected_corners: float
    actual_corners: int
    over_probabilities: dict[float, float]
    dispersion: float


@dataclass(frozen=True)
class ModelPredictions:
    """Predictions from both models for the same team observations."""

    venue_average: tuple[TeamCornerPrediction, ...]
    team_opponent: tuple[TeamCornerPrediction, ...]


def smoothed_average(
    observed_corners: int,
    observed_matches: int,
    league_average: float,
    prior_matches: int = DEFAULT_PRIOR_MATCHES,
) -> float:
    """Blend observed team history with prior matches at the league average."""

    if prior_matches <= 0:
        raise ValueError("prior_matches must be greater than zero")
    prior_corners = prior_matches * league_average
    return (observed_corners + prior_corners) / (
        observed_matches + prior_matches
    )


def expected_team_corners(
    team_history: TeamCornerHistory,
    opponent_history: TeamCornerHistory,
    league_average: float,
    prior_matches: int = DEFAULT_PRIOR_MATCHES,
) -> float:
    """Average a team's attacking history and its opponent's concessions."""

    team_attack = smoothed_average(
        team_history.corners_won,
        team_history.matches,
        league_average,
        prior_matches,
    )
    opponent_defence = smoothed_average(
        opponent_history.corners_allowed,
        opponent_history.matches,
        league_average,
        prior_matches,
    )
    return (team_attack + opponent_defence) / 2


def walk_forward_prediction_comparison(
    matches: Iterable[Match],
    evaluation_start: date = DEFAULT_EVALUATION_START,
    prior_matches: int = DEFAULT_PRIOR_MATCHES,
) -> ModelPredictions:
    """Predict each date with venue-average and team-opponent models."""

    if prior_matches <= 0:
        raise ValueError("prior_matches must be greater than zero")

    matches_by_date: dict[date, list[Match]] = defaultdict(list)
    for match in matches:
        matches_by_date[match.match_date].append(match)

    home_history: dict[str, TeamCornerHistory] = defaultdict(TeamCornerHistory)
    away_history: dict[str, TeamCornerHistory] = defaultdict(TeamCornerHistory)
    historical_home_sum = 0
    historical_squared_home_sum = 0
    historical_away_sum = 0
    historical_squared_away_sum = 0
    historical_matches = 0

    venue_average_predictions: list[TeamCornerPrediction] = []
    team_opponent_predictions: list[TeamCornerPrediction] = []

    for match_date in sorted(matches_by_date):
        matches_on_date = matches_by_date[match_date]

        if match_date >= evaluation_start and historical_matches:
            league_home_average = historical_home_sum / historical_matches
            league_away_average = historical_away_sum / historical_matches
            home_dispersion = estimate_dispersion(
                historical_matches,
                historical_home_sum,
                historical_squared_home_sum,
            )
            away_dispersion = estimate_dispersion(
                historical_matches,
                historical_away_sum,
                historical_squared_away_sum,
            )

            for match in matches_on_date:
                venue_average_predictions.extend(
                    _fixture_predictions(
                        match,
                        league_home_average,
                        league_away_average,
                        home_dispersion,
                        away_dispersion,
                    )
                )

                expected_home_corners = expected_team_corners(
                    home_history[match.home_team],
                    away_history[match.away_team],
                    league_home_average,
                    prior_matches,
                )
                expected_away_corners = expected_team_corners(
                    away_history[match.away_team],
                    home_history[match.home_team],
                    league_away_average,
                    prior_matches,
                )
                team_opponent_predictions.extend(
                    _fixture_predictions(
                        match,
                        expected_home_corners,
                        expected_away_corners,
                        home_dispersion,
                        away_dispersion,
                    )
                )

        # Update after every prediction on this date to prevent same-day leakage.
        for match in matches_on_date:
            home_history[match.home_team].record(
                match.home_corners,
                match.away_corners,
            )
            away_history[match.away_team].record(
                match.away_corners,
                match.home_corners,
            )
            historical_home_sum += match.home_corners
            historical_squared_home_sum += match.home_corners**2
            historical_away_sum += match.away_corners
            historical_squared_away_sum += match.away_corners**2
            historical_matches += 1

    predictions = ModelPredictions(
        venue_average=tuple(venue_average_predictions),
        team_opponent=tuple(team_opponent_predictions),
    )
    _require_matching_observations(predictions)
    return predictions


def evaluate_predictions(
    predictions: Iterable[TeamCornerPrediction],
) -> dict[str, object]:
    """Calculate count and probability metrics for team-corner predictions."""

    prediction_list = list(predictions)
    if not prediction_list:
        raise ValueError("no predictions are available for evaluation")

    count = len(prediction_list)
    errors = [
        prediction.actual_corners - prediction.expected_corners
        for prediction in prediction_list
    ]
    line_metrics: dict[str, dict[str, float]] = {}
    for line in TEAM_CORNER_LINES:
        probabilities = [
            prediction.over_probabilities[line]
            for prediction in prediction_list
        ]
        outcomes = [
            float(prediction.actual_corners > line)
            for prediction in prediction_list
        ]
        line_metrics[str(line)] = {
            "brier_score": sum(
                (probability - outcome) ** 2
                for probability, outcome in zip(probabilities, outcomes)
            )
            / count,
            "mean_predicted_over_probability": sum(probabilities) / count,
            "actual_over_rate": sum(outcomes) / count,
        }

    return {
        "evaluated_team_observations": count,
        "mean_predicted_corners": sum(
            prediction.expected_corners for prediction in prediction_list
        )
        / count,
        "mean_actual_corners": sum(
            prediction.actual_corners for prediction in prediction_list
        )
        / count,
        "mae": sum(abs(error) for error in errors) / count,
        "rmse": math.sqrt(sum(error**2 for error in errors) / count),
        "negative_binomial_negative_log_loss": sum(
            negative_binomial_negative_log_loss(
                prediction.actual_corners,
                prediction.expected_corners,
                prediction.dispersion,
            )
            for prediction in prediction_list
        )
        / count,
        "mean_brier_score": sum(
            metric["brier_score"] for metric in line_metrics.values()
        )
        / len(line_metrics),
        "lines": line_metrics,
    }


def paired_bootstrap(
    predictions: ModelPredictions,
    samples: int = 1_000,
    seed: int = 7,
) -> dict[str, object]:
    """Estimate uncertainty in challenger-minus-baseline metric differences."""

    if samples <= 0:
        raise ValueError("samples must be greater than zero")
    _require_matching_observations(predictions)

    fixture_differences = _fixture_metric_differences(predictions)
    if not fixture_differences:
        raise ValueError("no predictions are available for bootstrapping")

    random_generator = random.Random(seed)
    sampled_deltas: dict[str, list[float]] = {
        "mae": [],
        "mean_brier_score": [],
    }
    fixture_count = len(fixture_differences)
    for _ in range(samples):
        sample = [
            fixture_differences[random_generator.randrange(fixture_count)]
            for _ in range(fixture_count)
        ]
        for metric in sampled_deltas:
            sampled_deltas[metric].append(
                sum(fixture[metric] for fixture in sample) / fixture_count
            )

    return {
        "samples": samples,
        "seed": seed,
        "metrics": {
            metric: _summarize_bootstrap(deltas)
            for metric, deltas in sampled_deltas.items()
        },
    }


def evaluate_prior_sensitivity(
    matches: Iterable[Match],
    prior_match_counts: Sequence[int] = (2, 5, 10),
    evaluation_start: date = DEFAULT_EVALUATION_START,
) -> dict[str, dict[str, float]]:
    """Report challenger-minus-baseline metrics for several smoothing priors."""

    match_list = list(matches)
    results: dict[str, dict[str, float]] = {}
    for prior_matches in prior_match_counts:
        predictions = walk_forward_prediction_comparison(
            match_list,
            evaluation_start,
            prior_matches,
        )
        baseline = evaluate_predictions(predictions.venue_average)
        challenger = evaluate_predictions(predictions.team_opponent)
        results[str(prior_matches)] = _metric_differences(baseline, challenger)
    return results


def run_comparison(
    csv_paths: Iterable[str | Path],
    evaluation_start: date = DEFAULT_EVALUATION_START,
    prior_matches: int = DEFAULT_PRIOR_MATCHES,
    bootstrap_samples: int = 1_000,
) -> dict[str, object]:
    """Load Championship data and compare both team-corner models."""

    loaded: LoadResult = load_football_data_csv(csv_paths)
    _require_championship(loaded.matches)
    predictions = walk_forward_prediction_comparison(
        loaded.matches,
        evaluation_start,
        prior_matches,
    )
    baseline = evaluate_predictions(predictions.venue_average)
    challenger = evaluate_predictions(predictions.team_opponent)

    return {
        "competition": "EFL Championship",
        "target": "individual_team_full_match_corners",
        "evaluation_start": evaluation_start.isoformat(),
        "prior_matches": prior_matches,
        "data_quality": {
            "rows_read": loaded.rows_read,
            "rows_loaded": loaded.rows_loaded,
            "rows_without_corner_results": loaded.rows_without_corner_results,
        },
        "models": {
            "venue_average": {
                "overall": baseline,
                "by_venue": _evaluate_by_venue(predictions.venue_average),
            },
            "team_opponent": {
                "overall": challenger,
                "by_venue": _evaluate_by_venue(predictions.team_opponent),
            },
        },
        "team_opponent_minus_venue_average": _metric_differences(
            baseline,
            challenger,
        ),
        "paired_bootstrap": paired_bootstrap(
            predictions,
            bootstrap_samples,
        ),
    }


def _fixture_predictions(
    match: Match,
    expected_home_corners: float,
    expected_away_corners: float,
    home_dispersion: float,
    away_dispersion: float,
) -> tuple[TeamCornerPrediction, TeamCornerPrediction]:
    return (
        _make_prediction(
            match,
            match.home_team,
            "home",
            expected_home_corners,
            match.home_corners,
            home_dispersion,
        ),
        _make_prediction(
            match,
            match.away_team,
            "away",
            expected_away_corners,
            match.away_corners,
            away_dispersion,
        ),
    )


def _make_prediction(
    match: Match,
    team: str,
    venue: Venue,
    expected_corners: float,
    actual_corners: int,
    dispersion: float,
) -> TeamCornerPrediction:
    return TeamCornerPrediction(
        match=match,
        team=team,
        venue=venue,
        expected_corners=expected_corners,
        actual_corners=actual_corners,
        over_probabilities={
            line: negative_binomial_over_probability(
                expected_corners,
                line,
                dispersion,
            )
            for line in TEAM_CORNER_LINES
        },
        dispersion=dispersion,
    )


def _require_matching_observations(predictions: ModelPredictions) -> None:
    baseline_keys = [
        (
            prediction.match,
            prediction.team,
            prediction.venue,
            prediction.actual_corners,
        )
        for prediction in predictions.venue_average
    ]
    challenger_keys = [
        (
            prediction.match,
            prediction.team,
            prediction.venue,
            prediction.actual_corners,
        )
        for prediction in predictions.team_opponent
    ]
    if baseline_keys != challenger_keys:
        raise ValueError("models must contain identical observations")


def _fixture_metric_differences(
    predictions: ModelPredictions,
) -> list[dict[str, float]]:
    by_fixture: dict[Match, list[dict[str, float]]] = defaultdict(list)
    for baseline, challenger in zip(
        predictions.venue_average,
        predictions.team_opponent,
    ):
        actual = baseline.actual_corners
        baseline_brier = sum(
            (
                baseline.over_probabilities[line]
                - float(actual > line)
            )
            ** 2
            for line in TEAM_CORNER_LINES
        ) / len(TEAM_CORNER_LINES)
        challenger_brier = sum(
            (
                challenger.over_probabilities[line]
                - float(actual > line)
            )
            ** 2
            for line in TEAM_CORNER_LINES
        ) / len(TEAM_CORNER_LINES)
        by_fixture[baseline.match].append(
            {
                "mae": abs(actual - challenger.expected_corners)
                - abs(actual - baseline.expected_corners),
                "mean_brier_score": challenger_brier - baseline_brier,
            }
        )

    return [
        {
            metric: sum(observation[metric] for observation in observations)
            / len(observations)
            for metric in ("mae", "mean_brier_score")
        }
        for observations in by_fixture.values()
    ]


def _summarize_bootstrap(deltas: list[float]) -> dict[str, float]:
    ordered = sorted(deltas)
    return {
        "mean_delta": sum(deltas) / len(deltas),
        "lower_95": ordered[int(0.025 * (len(ordered) - 1))],
        "upper_95": ordered[int(0.975 * (len(ordered) - 1))],
        "challenger_win_rate": sum(delta < 0 for delta in deltas) / len(deltas),
    }


def _metric_differences(
    baseline: dict[str, object],
    challenger: dict[str, object],
) -> dict[str, float]:
    metrics = (
        "mae",
        "rmse",
        "negative_binomial_negative_log_loss",
        "mean_brier_score",
    )
    return {
        metric: float(challenger[metric]) - float(baseline[metric])
        for metric in metrics
    }


def _evaluate_by_venue(
    predictions: Iterable[TeamCornerPrediction],
) -> dict[str, dict[str, object]]:
    prediction_list = list(predictions)
    return {
        venue: evaluate_predictions(
            prediction
            for prediction in prediction_list
            if prediction.venue == venue
        )
        for venue in ("home", "away")
    }


def _require_championship(matches: Iterable[Match]) -> None:
    unexpected_competitions = {
        match.competition
        for match in matches
        if match.competition != CHAMPIONSHIP_CODE
    }
    if unexpected_competitions:
        unexpected = ", ".join(sorted(unexpected_competitions))
        raise ValueError(
            f"model supports Championship rows ({CHAMPIONSHIP_CODE}) only; "
            f"found: {unexpected}"
        )


def _print_summary(result: dict[str, object]) -> None:
    models = result["models"]
    assert isinstance(models, dict)
    baseline_model = models["venue_average"]
    challenger_model = models["team_opponent"]
    assert isinstance(baseline_model, dict)
    assert isinstance(challenger_model, dict)
    baseline = baseline_model["overall"]
    challenger = challenger_model["overall"]
    assert isinstance(baseline, dict)
    assert isinstance(challenger, dict)

    print("DeepFC Championship individual team-corners comparison")
    print(f"Evaluated observations: {baseline['evaluated_team_observations']}")
    print("Metric        Venue average  Team + opponent")
    print(f"MAE           {baseline['mae']:.4f}         {challenger['mae']:.4f}")
    print(f"RMSE          {baseline['rmse']:.4f}         {challenger['rmse']:.4f}")
    print(
        f"NB NLL        {baseline['negative_binomial_negative_log_loss']:.4f}"
        f"         {challenger['negative_binomial_negative_log_loss']:.4f}"
    )
    print(
        f"Mean Brier    {baseline['mean_brier_score']:.4f}         "
        f"{challenger['mean_brier_score']:.4f}"
    )
    print("\nJSON result")
    print(json.dumps(result, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare Championship individual team-corner models."
    )
    parser.add_argument("csv_paths", nargs="+", type=Path)
    parser.add_argument(
        "--evaluation-start",
        type=date.fromisoformat,
        default=DEFAULT_EVALUATION_START,
        help="First date to score, in YYYY-MM-DD format (default: 2018-07-01).",
    )
    parser.add_argument(
        "--prior-matches",
        type=int,
        default=DEFAULT_PRIOR_MATCHES,
        help="League-average matches used to smooth team history (default: 5).",
    )
    parser.add_argument(
        "--bootstrap-samples",
        type=int,
        default=1_000,
        help="Paired fixture bootstrap samples (default: 1000).",
    )
    args = parser.parse_args()
    _print_summary(
        run_comparison(
            args.csv_paths,
            args.evaluation_start,
            args.prior_matches,
            args.bootstrap_samples,
        )
    )


if __name__ == "__main__":
    main()
