"""Walk-forward models and evaluation for full-match total corners."""

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


SUPPORTED_TOTAL_CORNER_LINES = (8.5, 9.5, 10.5, 11.5)
CHAMPIONSHIP_CODE = "E1"
DEFAULT_EVALUATION_START_DATE = date(2018, 7, 1)
TEAM_STATS_PRIOR_MATCH_COUNT = 5


@dataclass(frozen=True)
class TotalCornersPrediction:
    """One pre-match total-corners prediction."""

    match: Match
    expected_total_corners: float
    over_probability_by_line: dict[float, float]


@dataclass
class TeamVenueCornerStats:
    """A team's accumulated corner statistics at home or away."""

    match_count: int = 0
    corners_for_sum: int = 0
    corners_against_sum: int = 0

    def add_match(
        self,
        corners_for_in_match: int,
        corners_against_in_match: int,
    ) -> None:
        """Add one completed match to the accumulated statistics."""

        self.match_count += 1
        self.corners_for_sum += corners_for_in_match
        self.corners_against_sum += corners_against_in_match


def poisson_over_probability(expected_total_corners: float, line: float) -> float:
    """Return P(total corners > line) under a Poisson distribution."""

    if expected_total_corners <= 0:
        raise ValueError("expected_total_corners must be greater than zero")
    if line < 0 or not math.isclose(line % 1, 0.5):
        raise ValueError("line must be a non-negative half line")

    largest_under_total = math.floor(line)
    probability = math.exp(-expected_total_corners)
    cumulative_probability = probability
    for total_corners in range(1, largest_under_total + 1):
        probability *= expected_total_corners / total_corners
        cumulative_probability += probability
    return max(0.0, min(1.0, 1.0 - cumulative_probability))


def _group_matches_by_date(matches: Iterable[Match]) -> dict[date, list[Match]]:
    matches_by_date: dict[date, list[Match]] = defaultdict(list)
    for match in matches:
        matches_by_date[match.match_date].append(match)
    return matches_by_date


def _build_total_corners_prediction(
    match: Match,
    expected_total_corners: float,
) -> TotalCornersPrediction:
    return TotalCornersPrediction(
        match=match,
        expected_total_corners=expected_total_corners,
        over_probability_by_line={
            line: poisson_over_probability(expected_total_corners, line)
            for line in SUPPORTED_TOTAL_CORNER_LINES
        },
    )


def predict_total_corners_with_league_average(
    matches: Iterable[Match],
    evaluation_start_date: date = DEFAULT_EVALUATION_START_DATE,
) -> list[TotalCornersPrediction]:
    """Predict each fixture using the average from all earlier match dates."""

    matches_by_date = _group_matches_by_date(matches)
    league_corner_sum = 0
    league_match_count = 0
    predictions: list[TotalCornersPrediction] = []

    for match_date in sorted(matches_by_date):
        matches_on_date = matches_by_date[match_date]
        if match_date >= evaluation_start_date and league_match_count:
            league_total_corners_per_match = league_corner_sum / league_match_count
            predictions.extend(
                _build_total_corners_prediction(
                    match=match,
                    expected_total_corners=league_total_corners_per_match,
                )
                for match in matches_on_date
            )

        league_corner_sum += sum(match.total_corners for match in matches_on_date)
        league_match_count += len(matches_on_date)

    return predictions


def _smoothed_corners_per_match(
    observed_corner_sum: int,
    observed_match_count: int,
    league_corners_per_match: float,
) -> float:
    """Blend observed team corners with five matches at the league average."""

    prior_corner_sum = TEAM_STATS_PRIOR_MATCH_COUNT * league_corners_per_match
    return (observed_corner_sum + prior_corner_sum) / (
        observed_match_count + TEAM_STATS_PRIOR_MATCH_COUNT
    )


def _estimate_corners_for_team(
    team_venue_stats: TeamVenueCornerStats,
    opponent_venue_stats: TeamVenueCornerStats,
    league_corners_per_match: float,
) -> float:
    """Combine a team's corners for with its opponent's corners against."""

    team_corners_for_per_match = _smoothed_corners_per_match(
        observed_corner_sum=team_venue_stats.corners_for_sum,
        observed_match_count=team_venue_stats.match_count,
        league_corners_per_match=league_corners_per_match,
    )
    opponent_corners_against_per_match = _smoothed_corners_per_match(
        observed_corner_sum=opponent_venue_stats.corners_against_sum,
        observed_match_count=opponent_venue_stats.match_count,
        league_corners_per_match=league_corners_per_match,
    )
    return (team_corners_for_per_match + opponent_corners_against_per_match) / 2


def predict_total_corners_with_team_strength(
    matches: Iterable[Match],
    evaluation_start_date: date = DEFAULT_EVALUATION_START_DATE,
) -> list[TotalCornersPrediction]:
    """Predict from current-season venue-specific team corner strength."""

    matches_by_date = _group_matches_by_date(matches)
    league_match_count = 0
    league_home_corners_sum = 0
    league_away_corners_sum = 0
    home_corner_stats_by_team: dict[str, TeamVenueCornerStats] = defaultdict(
        TeamVenueCornerStats
    )
    away_corner_stats_by_team: dict[str, TeamVenueCornerStats] = defaultdict(
        TeamVenueCornerStats
    )
    active_season_start_year: int | None = None
    predictions: list[TotalCornersPrediction] = []

    for match_date in sorted(matches_by_date):
        matches_on_date = matches_by_date[match_date]
        season_start_years = {
            match.season_start_year for match in matches_on_date
        }
        if len(season_start_years) != 1:
            raise ValueError("matches on the same date must belong to one season")
        season_start_year = next(iter(season_start_years))
        if season_start_year != active_season_start_year:
            home_corner_stats_by_team.clear()
            away_corner_stats_by_team.clear()
            active_season_start_year = season_start_year

        if match_date >= evaluation_start_date and league_match_count:
            league_home_corners_per_match = (
                league_home_corners_sum / league_match_count
            )
            league_away_corners_per_match = (
                league_away_corners_sum / league_match_count
            )

            for match in matches_on_date:
                expected_home_corners = _estimate_corners_for_team(
                    team_venue_stats=home_corner_stats_by_team[match.home_team],
                    opponent_venue_stats=away_corner_stats_by_team[match.away_team],
                    league_corners_per_match=league_home_corners_per_match,
                )
                expected_away_corners = _estimate_corners_for_team(
                    team_venue_stats=away_corner_stats_by_team[match.away_team],
                    opponent_venue_stats=home_corner_stats_by_team[match.home_team],
                    league_corners_per_match=league_away_corners_per_match,
                )
                predictions.append(
                    _build_total_corners_prediction(
                        match=match,
                        expected_total_corners=(
                            expected_home_corners + expected_away_corners
                        ),
                    )
                )

        for match in matches_on_date:
            home_corner_stats_by_team[match.home_team].add_match(
                corners_for_in_match=match.home_corners,
                corners_against_in_match=match.away_corners,
            )
            away_corner_stats_by_team[match.away_team].add_match(
                corners_for_in_match=match.away_corners,
                corners_against_in_match=match.home_corners,
            )
            league_home_corners_sum += match.home_corners
            league_away_corners_sum += match.away_corners
            league_match_count += 1

    return predictions


def evaluate_total_corner_predictions(
    predictions: Iterable[TotalCornersPrediction],
) -> dict[str, object]:
    """Calculate count and probability metrics as a JSON-serializable dict."""

    prediction_list = list(predictions)
    if not prediction_list:
        raise ValueError("no predictions are available for evaluation")

    prediction_count = len(prediction_list)
    absolute_errors = [
        abs(prediction.expected_total_corners - prediction.match.total_corners)
        for prediction in prediction_list
    ]
    squared_errors = [error**2 for error in absolute_errors]
    negative_log_losses = [
        prediction.expected_total_corners
        - prediction.match.total_corners
        * math.log(prediction.expected_total_corners)
        + math.lgamma(prediction.match.total_corners + 1)
        for prediction in prediction_list
    ]

    line_metrics: dict[str, dict[str, float]] = {}
    for line in SUPPORTED_TOTAL_CORNER_LINES:
        predicted_over_probabilities = [
            prediction.over_probability_by_line[line]
            for prediction in prediction_list
        ]
        actual_over_outcomes = [
            float(prediction.match.total_corners > line)
            for prediction in prediction_list
        ]
        mean_predicted_over_probability = (
            sum(predicted_over_probabilities) / prediction_count
        )
        actual_over_rate = sum(actual_over_outcomes) / prediction_count
        line_metrics[str(line)] = {
            "brier_score": sum(
                (probability - outcome) ** 2
                for probability, outcome in zip(
                    predicted_over_probabilities,
                    actual_over_outcomes,
                )
            )
            / prediction_count,
            "mean_predicted_over_probability": mean_predicted_over_probability,
            "mean_predicted_under_probability": (
                1.0 - mean_predicted_over_probability
            ),
            "actual_over_rate": actual_over_rate,
            "actual_under_rate": 1.0 - actual_over_rate,
        }

    return {
        "evaluated_matches": prediction_count,
        "mean_predicted_total": sum(
            prediction.expected_total_corners for prediction in prediction_list
        )
        / prediction_count,
        "mean_actual_total": sum(
            prediction.match.total_corners for prediction in prediction_list
        )
        / prediction_count,
        "mae": sum(absolute_errors) / prediction_count,
        "rmse": math.sqrt(sum(squared_errors) / prediction_count),
        "poisson_negative_log_loss": (
            sum(negative_log_losses) / prediction_count
        ),
        "mean_brier_score": sum(
            metrics["brier_score"] for metrics in line_metrics.values()
        )
        / len(line_metrics),
        "lines": line_metrics,
    }


def _metric_change(
    league_average_metrics: dict[str, object],
    team_strength_metrics: dict[str, object],
    metric_name: str,
) -> float:
    return float(team_strength_metrics[metric_name]) - float(
        league_average_metrics[metric_name]
    )


def compare_total_corner_models(
    csv_paths: Iterable[str | Path],
    evaluation_start_date: date = DEFAULT_EVALUATION_START_DATE,
) -> dict[str, object]:
    """Evaluate league-average and team-strength models on identical matches."""

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

    league_average_predictions = predict_total_corners_with_league_average(
        loaded.matches,
        evaluation_start_date,
    )
    team_strength_predictions = predict_total_corners_with_team_strength(
        loaded.matches,
        evaluation_start_date,
    )
    if [prediction.match for prediction in league_average_predictions] != [
        prediction.match for prediction in team_strength_predictions
    ]:
        raise RuntimeError("models did not evaluate the same matches")

    league_average_metrics = evaluate_total_corner_predictions(
        league_average_predictions
    )
    team_strength_metrics = evaluate_total_corner_predictions(
        team_strength_predictions
    )
    league_line_metrics = league_average_metrics["lines"]
    team_line_metrics = team_strength_metrics["lines"]
    if not isinstance(league_line_metrics, dict) or not isinstance(
        team_line_metrics, dict
    ):
        raise RuntimeError("line metrics have an unexpected format")

    return {
        "competition": "EFL Championship",
        "target": "full_match_total_corners",
        "evaluation_start": evaluation_start_date.isoformat(),
        "data_quality": {
            "rows_read": loaded.rows_read,
            "rows_loaded": loaded.rows_loaded,
            "rows_without_corner_results": loaded.rows_without_corner_results,
        },
        "models": {
            "league_average": league_average_metrics,
            "team_strength": team_strength_metrics,
        },
        "team_strength_minus_league_average": {
            "mae": _metric_change(
                league_average_metrics, team_strength_metrics, "mae"
            ),
            "rmse": _metric_change(
                league_average_metrics, team_strength_metrics, "rmse"
            ),
            "poisson_negative_log_loss": _metric_change(
                league_average_metrics,
                team_strength_metrics,
                "poisson_negative_log_loss",
            ),
            "mean_brier_score": _metric_change(
                league_average_metrics,
                team_strength_metrics,
                "mean_brier_score",
            ),
            "brier_score_by_line": {
                line: float(team_line_metrics[line]["brier_score"])
                - float(league_line_metrics[line]["brier_score"])
                for line in league_line_metrics
            },
        },
    }


def _print_model_comparison(result: dict[str, object]) -> None:
    models = result["models"]
    if not isinstance(models, dict):
        raise RuntimeError("model metrics have an unexpected format")
    league_average = models["league_average"]
    team_strength = models["team_strength"]
    if not isinstance(league_average, dict) or not isinstance(team_strength, dict):
        raise RuntimeError("model metrics have an unexpected format")

    print("DeepFC Championship full-match total corners model comparison")
    print(f"Evaluated matches: {league_average['evaluated_matches']}")
    print("Metric        League average  Team strength")
    print(
        f"MAE           {league_average['mae']:.3f}           "
        f"{team_strength['mae']:.3f}"
    )
    print(
        f"RMSE          {league_average['rmse']:.3f}           "
        f"{team_strength['rmse']:.3f}"
    )
    print(
        f"Poisson NLL   {league_average['poisson_negative_log_loss']:.3f}"
        f"           {team_strength['poisson_negative_log_loss']:.3f}"
    )
    print(
        f"Mean Brier    {league_average['mean_brier_score']:.4f}          "
        f"{team_strength['mean_brier_score']:.4f}"
    )
    print("\nJSON result")
    print(json.dumps(result, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compare Championship league-average and team-strength "
            "total-corners models."
        )
    )
    parser.add_argument("csv_paths", nargs="+", type=Path)
    parser.add_argument(
        "--evaluation-start",
        type=date.fromisoformat,
        default=DEFAULT_EVALUATION_START_DATE,
        help="First date to score, in YYYY-MM-DD format (default: 2018-07-01).",
    )
    args = parser.parse_args()
    _print_model_comparison(
        compare_total_corner_models(args.csv_paths, args.evaluation_start)
    )


if __name__ == "__main__":
    main()
