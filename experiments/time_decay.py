"""Research whether recent Championship matches deserve more weight."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from itertools import groupby
import json
import math
from pathlib import Path
import random
from typing import Iterable, Literal

from deepfc.corner_distribution import (
    estimate_dispersion,
    negative_binomial_over_probability,
)
from deepfc.football_data_csv import load_football_data_csv
from deepfc.match_data import Match
from deepfc.team_corners import (
    TEAM_CORNER_LINES,
    TeamCornerPrediction,
    evaluate_predictions,
    walk_forward_prediction_comparison,
)


HALF_LIFE_DAYS = 180
EVALUATION_START = date(2018, 7, 1)
Venue = Literal["home", "away"]


@dataclass(frozen=True)
class CornerObservation:
    match: Match
    team: str
    opponent: str
    venue: Venue
    corners_for: int
    corners_allowed: int


@dataclass(frozen=True)
class ComparedPredictions:
    deepfc: tuple[TeamCornerPrediction, ...]
    equal_weight: tuple[TeamCornerPrediction, ...]
    time_weighted: tuple[TeamCornerPrediction, ...]


def time_weight(age_days: int, half_life_days: int = HALF_LIFE_DAYS) -> float:
    """Return an exponential weight that halves every configured half-life."""
    if age_days < 0 or half_life_days <= 0:
        raise ValueError("age and half-life must be non-negative and positive")
    return 0.5 ** (age_days / half_life_days)


def expected_team_corners(
    history: Iterable[CornerObservation],
    team: str,
    opponent: str,
    venue: Venue,
    prediction_date: date,
    *,
    half_life_days: int | None,
    smoothing_matches: float = 5.0,
    team_prior_matches: float | None = None,
) -> float:
    """Estimate venue attack × opposing concessions relative to the league."""
    observations = list(history)
    team_prior = smoothing_matches if team_prior_matches is None else team_prior_matches
    if not math.isfinite(team_prior) or team_prior <= 0:
        raise ValueError("team prior must be finite and positive")
    if any(item.match.match_date >= prediction_date for item in observations):
        raise ValueError("historical matches must precede the prediction date")
    opposite: Venue = "away" if venue == "home" else "home"

    def totals(items: Iterable[CornerObservation], field: str) -> tuple[float, float]:
        weighted_sum = weighted_count = 0.0
        for item in items:
            weight = (
                1.0 if half_life_days is None
                else time_weight((prediction_date - item.match.match_date).days, half_life_days)
            )
            weighted_sum += weight * getattr(item, field)
            weighted_count += weight
        return weighted_sum, weighted_count

    league_sum, league_count = totals(
        (item for item in observations if item.venue == venue), "corners_for",
    )
    attack_sum, attack_count = totals(
        (item for item in observations if item.team == team and item.venue == venue),
        "corners_for",
    )
    allowed_sum, allowed_count = totals(
        (item for item in observations if item.team == opponent and item.venue == opposite),
        "corners_allowed",
    )
    league_rate = (league_sum + smoothing_matches) / (league_count + smoothing_matches)
    attack_rate = (
        attack_sum + team_prior * league_rate
    ) / (attack_count + team_prior)
    allowed_rate = (
        allowed_sum + team_prior * league_rate
    ) / (allowed_count + team_prior)
    return attack_rate * allowed_rate / league_rate


def compare_models(
    matches: Iterable[Match],
    *,
    evaluation_start: date = EVALUATION_START,
    min_history: int = 100,
    min_venue_history: int = 5,
    time_weighted_prior_matches: float = 5.0,
) -> ComparedPredictions:
    """Compare three models on one common, leakage-safe fixture cohort."""
    ordered = sorted(matches, key=lambda match: match.match_date)
    if not ordered or any(match.competition != "E1" for match in ordered):
        raise ValueError("provide nonempty Championship (E1) history only")
    fixture_keys = [(m.match_date, m.home_team, m.away_team) for m in ordered]
    if len(set(fixture_keys)) != len(fixture_keys):
        raise ValueError("duplicate fixture; supply non-overlapping season files")

    deepfc_by_team = {
        (prediction.match, prediction.venue): prediction
        for prediction in walk_forward_prediction_comparison(
            ordered, evaluation_start,
        ).team_opponent
    }
    history: list[CornerObservation] = []
    deepfc, equal_weight, time_weighted = [], [], []

    for match_date, date_group in groupby(ordered, key=lambda match: match.match_date):
        matches_on_date = list(date_group)
        if match_date >= evaluation_start and len(history) >= min_history:
            corner_sum = sum(item.corners_for for item in history)
            dispersion = estimate_dispersion(
                len(history), corner_sum,
                sum(item.corners_for**2 for item in history),
            )
            for match in matches_on_date:
                home_history = sum(
                    item.team == match.home_team and item.venue == "home"
                    for item in history
                )
                away_history = sum(
                    item.team == match.away_team and item.venue == "away"
                    for item in history
                )
                if min(home_history, away_history) < min_venue_history:
                    continue
                for team, opponent, venue, actual in (
                    (match.home_team, match.away_team, "home", match.home_corners),
                    (match.away_team, match.home_team, "away", match.away_corners),
                ):
                    deepfc.append(deepfc_by_team[match, venue])
                    for destination, half_life in (
                        (equal_weight, None),
                        (time_weighted, HALF_LIFE_DAYS),
                    ):
                        expected = expected_team_corners(
                            history, team, opponent, venue, match_date,
                            half_life_days=half_life,
                            team_prior_matches=(time_weighted_prior_matches
                                                if half_life is not None else None),
                        )
                        destination.append(TeamCornerPrediction(
                            match=match,
                            team=team,
                            venue=venue,
                            expected_corners=expected,
                            actual_corners=actual,
                            over_probabilities={
                                line: negative_binomial_over_probability(
                                    expected, line, dispersion,
                                )
                                for line in TEAM_CORNER_LINES
                            },
                            dispersion=dispersion,
                        ))

        # Predict the entire date before adding any result from that date.
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

    return ComparedPredictions(
        tuple(deepfc), tuple(equal_weight), tuple(time_weighted),
    )


def paired_block_brier_interval(
    baseline: tuple[TeamCornerPrediction, ...],
    challenger: tuple[TeamCornerPrediction, ...],
    *,
    samples: int = 2_000,
    seed: int = 7,
) -> dict[str, float]:
    """Bootstrap paired 28-day blocks; negative differences favor challenger."""
    if not baseline or len(baseline) != len(challenger) or samples <= 0:
        raise ValueError("matching nonempty predictions and positive samples required")
    blocks: dict[int, list[float]] = defaultdict(list)
    for before, after in zip(baseline, challenger):
        if (before.match, before.venue) != (after.match, after.venue):
            raise ValueError("predictions must describe identical ordered observations")
        delta = sum(
            (after.over_probabilities[line] - (after.actual_corners > line)) ** 2
            - (before.over_probabilities[line] - (before.actual_corners > line)) ** 2
            for line in TEAM_CORNER_LINES
        ) / len(TEAM_CORNER_LINES)
        blocks[before.match.match_date.toordinal() // 28].append(delta)
    block_totals = [(len(values), sum(values)) for values in blocks.values()]
    generator = random.Random(seed)
    differences = []
    for _ in range(samples):
        selected = generator.choices(block_totals, k=len(block_totals))
        differences.append(
            sum(total for _, total in selected) / sum(count for count, _ in selected)
        )
    differences.sort()
    return {
        "lower_95": differences[int(0.025 * (samples - 1))],
        "upper_95": differences[int(0.975 * (samples - 1))],
        "fraction_below_zero": sum(value < 0 for value in differences) / samples,
    }


def run_experiment(paths: Iterable[Path]) -> dict[str, object]:
    loaded = load_football_data_csv(paths)
    compared = compare_models(loaded.matches)
    models = {
        "deepfc": compared.deepfc,
        "equal_weight": compared.equal_weight,
        "time_weighted_180": compared.time_weighted,
    }
    return {
        "settings": {
            "competition": "E1",
            "evaluation_start": EVALUATION_START.isoformat(),
            "half_life_days": HALF_LIFE_DAYS,
            "lines": TEAM_CORNER_LINES,
        },
        "data_quality": {
            "rows_read": loaded.rows_read,
            "rows_loaded": loaded.rows_loaded,
            "rows_without_corner_results": loaded.rows_without_corner_results,
        },
        "models": {name: evaluate_predictions(predictions) for name, predictions in models.items()},
        "brier_intervals": {
            "time_weighted_minus_equal_weight": paired_block_brier_interval(
                compared.equal_weight, compared.time_weighted,
            ),
            "time_weighted_minus_deepfc": paired_block_brier_interval(
                compared.deepfc, compared.time_weighted,
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_paths", nargs="+", type=Path)
    args = parser.parse_args()
    print(json.dumps(run_experiment(args.csv_paths), indent=2))


if __name__ == "__main__":
    main()
