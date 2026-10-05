"""Test whether historical shot pressure improves team-corner predictions."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
import hashlib
from itertools import groupby
import json
import math
from pathlib import Path
import random
from typing import Iterable, Literal

from deepfc.corner_distribution import (
    negative_binomial_negative_log_loss,
    negative_binomial_over_probability,
)
from deepfc.football_data_csv import load_football_data_csv
from deepfc.match_data import Match
from deepfc.team_corners import TEAM_CORNER_LINES, TeamCornerPrediction, evaluate_predictions
from experiments.time_decay import HALF_LIFE_DAYS, compare_models, time_weight


SELECTION_END = date(2023, 7, 1)
VALIDATION_END = date(2024, 7, 1)
BASELINE_STRENGTH = 0.0
SHOT_STRENGTHS = (0.25, 0.5, 0.75, 1.0)
SMOOTHING_MATCHES = 5.0
QUARANTINED_FIXTURE = (date(2024, 11, 10), "Burnley", "Swansea")
Venue = Literal["home", "away"]


@dataclass(frozen=True)
class MatchShots:
    """Completed match plus valid full-match shot statistics, when available."""

    match: Match
    home_shots: int | None
    away_shots: int | None
    home_shots_on_target: int | None
    away_shots_on_target: int | None

    def __post_init__(self) -> None:
        values = (
            self.home_shots,
            self.away_shots,
            self.home_shots_on_target,
            self.away_shots_on_target,
        )
        if any(value is None for value in values) and not all(
            value is None for value in values
        ):
            raise ValueError("shot fields must either all be present or all be absent")

    @property
    def has_valid_shots(self) -> bool:
        return self.home_shots is not None


@dataclass(frozen=True)
class ShotObservation:
    """One team's shot production and concessions in one venue role."""

    match_date: date
    team: str
    venue: Venue
    shots_for: int
    shots_allowed: int
    shots_on_target_for: int
    shots_on_target_allowed: int


@dataclass(frozen=True)
class ShotData:
    matches: tuple[MatchShots, ...]
    rows_read: int
    rows_loaded: int
    rows_without_corner_results: int
    quarantined_shot_rows: int


def _parse_date(value: str) -> date:
    for date_format in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(value.strip(), date_format).date()
        except ValueError:
            pass
    raise ValueError(f"unsupported match date: {value!r}")


def _parse_count(value: str, field: str) -> int:
    raw = value.strip()
    if not raw:
        raise ValueError(f"{field} is missing")
    parsed = float(raw)
    if not parsed.is_integer() or parsed < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return int(parsed)


def load_shot_data(paths: Iterable[str | Path]) -> ShotData:
    """Attach Football-Data shot fields to canonical completed matches."""

    path_list = [Path(path) for path in paths]
    loaded = load_football_data_csv(path_list)
    canonical_matches = {
        (match.match_date, match.home_team, match.away_team): match
        for match in loaded.matches
    }
    shots_by_fixture: dict[
        tuple[date, str, str], tuple[int, int, int, int] | None
    ] = {}
    required = {"Date", "HomeTeam", "AwayTeam", "HC", "AC", "HS", "AS", "HST", "AST"}
    quarantined = 0

    for path in path_list:
        with path.open(encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            missing = required - set(reader.fieldnames or ())
            if missing:
                raise ValueError(f"{path} is missing required columns: {', '.join(sorted(missing))}")
            for row_number, row in enumerate(reader, start=2):
                if not (row["HC"] or "").strip() and not (row["AC"] or "").strip():
                    continue
                fixture = (
                    _parse_date(row["Date"] or ""),
                    (row["HomeTeam"] or "").strip(),
                    (row["AwayTeam"] or "").strip(),
                )
                if fixture in shots_by_fixture:
                    raise ValueError(f"duplicate fixture in shot data: {fixture}")
                try:
                    values = (
                        _parse_count(row["HS"] or "", "home shots"),
                        _parse_count(row["AS"] or "", "away shots"),
                        _parse_count(row["HST"] or "", "home shots on target"),
                        _parse_count(row["AST"] or "", "away shots on target"),
                    )
                except ValueError as error:
                    raise ValueError(f"{path} row {row_number}: {error}") from error
                home_shots, away_shots, home_on_target, away_on_target = values
                if fixture == QUARANTINED_FIXTURE:
                    if home_on_target <= home_shots:
                        raise ValueError("the quarantined fixture no longer has the expected source defect")
                    shots_by_fixture[fixture] = None
                    quarantined += 1
                    continue
                if home_on_target > home_shots or away_on_target > away_shots:
                    raise ValueError(f"{path} row {row_number}: shots on target exceed total shots")
                shots_by_fixture[fixture] = values

    if set(shots_by_fixture) != set(canonical_matches):
        raise ValueError("shot rows do not match the canonical completed-match cohort")
    matches = []
    for fixture, match in canonical_matches.items():
        values = shots_by_fixture[fixture]
        matches.append(MatchShots(match, *(values or (None, None, None, None))))
    matches.sort(key=lambda item: item.match.match_date)
    return ShotData(
        matches=tuple(matches),
        rows_read=loaded.rows_read,
        rows_loaded=loaded.rows_loaded,
        rows_without_corner_results=loaded.rows_without_corner_results,
        quarantined_shot_rows=quarantined,
    )


def _weighted_rate(
    observations: Iterable[ShotObservation],
    field: str,
    prediction_date: date,
) -> tuple[float, float]:
    weighted_sum = weighted_count = 0.0
    for observation in observations:
        if observation.match_date >= prediction_date:
            raise ValueError("historical shots must precede the prediction date")
        weight = time_weight(
            (prediction_date - observation.match_date).days,
            HALF_LIFE_DAYS,
        )
        weighted_sum += weight * getattr(observation, field)
        weighted_count += weight
    return weighted_sum, weighted_count


def shot_pressure_feature(
    history: Iterable[ShotObservation],
    team: str,
    opponent: str,
    venue: Venue,
    prediction_date: date,
) -> float:
    """Return log shot pressure relative to the venue-specific league rate."""

    observations = list(history)
    opposite: Venue = "away" if venue == "home" else "home"
    log_ratios = []
    for attacking_field, allowed_field in (
        ("shots_for", "shots_allowed"),
        ("shots_on_target_for", "shots_on_target_allowed"),
    ):
        league_sum, league_count = _weighted_rate(
            (item for item in observations if item.venue == venue),
            attacking_field,
            prediction_date,
        )
        if not league_count:
            raise ValueError("shot history has no venue-specific league observations")
        league_rate = league_sum / league_count
        attack_sum, attack_count = _weighted_rate(
            (item for item in observations if item.team == team and item.venue == venue),
            attacking_field,
            prediction_date,
        )
        allowed_sum, allowed_count = _weighted_rate(
            (item for item in observations if item.team == opponent and item.venue == opposite),
            allowed_field,
            prediction_date,
        )
        attack_rate = (
            attack_sum + SMOOTHING_MATCHES * league_rate
        ) / (attack_count + SMOOTHING_MATCHES)
        allowed_rate = (
            allowed_sum + SMOOTHING_MATCHES * league_rate
        ) / (allowed_count + SMOOTHING_MATCHES)
        log_ratios.extend((
            math.log(attack_rate / league_rate),
            math.log(allowed_rate / league_rate),
        ))
    return sum(log_ratios) / len(log_ratios)


def generate_predictions(
    matches: Iterable[MatchShots],
) -> dict[float, tuple[TeamCornerPrediction, ...]]:
    """Generate baseline and predeclared shot-adjusted predictions."""

    ordered = sorted(matches, key=lambda item: item.match.match_date)
    baseline = compare_models(item.match for item in ordered).time_weighted
    baseline_by_observation = {(item.match, item.venue): item for item in baseline}
    predictions: dict[float, list[TeamCornerPrediction]] = {
        BASELINE_STRENGTH: [],
        **{strength: [] for strength in SHOT_STRENGTHS},
    }
    history: list[ShotObservation] = []

    for prediction_date, date_group in groupby(
        ordered, key=lambda item: item.match.match_date,
    ):
        matches_on_date = list(date_group)
        for item in matches_on_date:
            match = item.match
            for team, opponent, venue in (
                (match.home_team, match.away_team, "home"),
                (match.away_team, match.home_team, "away"),
            ):
                baseline_prediction = baseline_by_observation.get((match, venue))
                if baseline_prediction is None:
                    continue
                feature = shot_pressure_feature(
                    history, team, opponent, venue, prediction_date,
                )
                predictions[BASELINE_STRENGTH].append(baseline_prediction)
                for strength in SHOT_STRENGTHS:
                    expected = baseline_prediction.expected_corners * math.exp(
                        strength * feature
                    )
                    predictions[strength].append(TeamCornerPrediction(
                        match=match,
                        team=team,
                        venue=venue,
                        expected_corners=expected,
                        actual_corners=baseline_prediction.actual_corners,
                        over_probabilities={
                            line: negative_binomial_over_probability(
                                expected, line, baseline_prediction.dispersion,
                            )
                            for line in TEAM_CORNER_LINES
                        },
                        dispersion=baseline_prediction.dispersion,
                    ))

        # Quarantined results can be predicted but never enter later shot history.
        for item in matches_on_date:
            if not item.has_valid_shots:
                continue
            assert item.home_shots is not None
            assert item.away_shots is not None
            assert item.home_shots_on_target is not None
            assert item.away_shots_on_target is not None
            match = item.match
            history.extend((
                ShotObservation(
                    prediction_date, match.home_team, "home",
                    item.home_shots, item.away_shots,
                    item.home_shots_on_target, item.away_shots_on_target,
                ),
                ShotObservation(
                    prediction_date, match.away_team, "away",
                    item.away_shots, item.home_shots,
                    item.away_shots_on_target, item.home_shots_on_target,
                ),
            ))

    frozen = {strength: tuple(values) for strength, values in predictions.items()}
    identity = [(item.match, item.venue) for item in frozen[BASELINE_STRENGTH]]
    if any(
        [(item.match, item.venue) for item in values] != identity
        for values in frozen.values()
    ):
        raise ValueError("all shot strengths must score identical observations")
    return frozen


def paired_block_intervals(
    baseline: tuple[TeamCornerPrediction, ...],
    candidate: tuple[TeamCornerPrediction, ...],
    *,
    samples: int = 2_000,
    seed: int = 7,
) -> dict[str, dict[str, float]]:
    """Bootstrap paired 28-day blocks for Brier, count NLL and MAE deltas."""

    blocks: dict[int, list[tuple[float, float, float]]] = defaultdict(list)
    for before, after in zip(baseline, candidate, strict=True):
        if (before.match, before.venue) != (after.match, after.venue):
            raise ValueError("predictions must describe identical observations")
        outcome = before.actual_corners
        brier_delta = sum(
            (after.over_probabilities[line] - (outcome > line)) ** 2
            - (before.over_probabilities[line] - (outcome > line)) ** 2
            for line in TEAM_CORNER_LINES
        ) / len(TEAM_CORNER_LINES)
        nll_delta = negative_binomial_negative_log_loss(
            outcome, after.expected_corners, after.dispersion,
        ) - negative_binomial_negative_log_loss(
            outcome, before.expected_corners, before.dispersion,
        )
        mae_delta = abs(outcome - after.expected_corners) - abs(
            outcome - before.expected_corners
        )
        blocks[before.match.match_date.toordinal() // 28].append(
            (brier_delta, nll_delta, mae_delta)
        )
    totals = [
        (len(values), *(sum(item[index] for item in values) for index in range(3)))
        for values in blocks.values()
    ]
    generator = random.Random(seed)
    draws = {"mean_brier_score": [], "negative_binomial_negative_log_loss": [], "mae": []}
    for _ in range(samples):
        selected = generator.choices(totals, k=len(totals))
        count = sum(item[0] for item in selected)
        for index, name in enumerate(draws, start=1):
            draws[name].append(sum(item[index] for item in selected) / count)
    return {
        name: {
            "lower_95": sorted(values)[int(0.025 * (samples - 1))],
            "upper_95": sorted(values)[int(0.975 * (samples - 1))],
            "fraction_below_zero": sum(value < 0 for value in values) / samples,
        }
        for name, values in draws.items()
    }


def _comparison(
    baseline: tuple[TeamCornerPrediction, ...],
    candidate: tuple[TeamCornerPrediction, ...],
) -> dict[str, object]:
    before = evaluate_predictions(baseline)
    after = evaluate_predictions(candidate)
    metrics = ("mae", "rmse", "negative_binomial_negative_log_loss", "mean_brier_score")
    return {
        "baseline": before,
        "candidate": after,
        "candidate_minus_baseline": {
            metric: after[metric] - before[metric] for metric in metrics
        },
        "paired_28_day_intervals": paired_block_intervals(baseline, candidate),
    }


def _season(prediction: TeamCornerPrediction) -> int:
    match_date = prediction.match.match_date
    return match_date.year - int(match_date.month < 7)


def run_experiment(matches: Iterable[MatchShots]) -> dict[str, object]:
    """Select shot strength on early seasons and freeze it for later evaluation."""

    predictions = generate_predictions(matches)
    selected = min(
        SHOT_STRENGTHS,
        key=lambda strength: evaluate_predictions(
            item for item in predictions[strength]
            if item.match.match_date < SELECTION_END
        )["mean_brier_score"],
    )
    baseline = predictions[BASELINE_STRENGTH]
    candidate = predictions[selected]
    tuning = lambda item: item.match.match_date < SELECTION_END
    validation = lambda item: SELECTION_END <= item.match.match_date < VALIDATION_END
    test = lambda item: item.match.match_date >= VALIDATION_END
    return {
        "settings": {
            "competition": "E1",
            "baseline_model": "fixed_180_day_team_corners",
            "half_life_days": HALF_LIFE_DAYS,
            "smoothing_matches": SMOOTHING_MATCHES,
            "candidate_strengths": SHOT_STRENGTHS,
            "selection_metric": "mean_brier_score",
            "selection_end_exclusive": SELECTION_END.isoformat(),
            "validation_end_exclusive": VALIDATION_END.isoformat(),
            "selected_shot_strength": selected,
            "later_seasons_previously_inspected": True,
        },
        "tuning": {
            str(strength): evaluate_predictions(
                item for item in values if tuning(item)
            )
            for strength, values in predictions.items()
        },
        "validation_2023_24": _comparison(
            tuple(item for item in baseline if validation(item)),
            tuple(item for item in candidate if validation(item)),
        ),
        "retrospective_test_2024_26": _comparison(
            tuple(item for item in baseline if test(item)),
            tuple(item for item in candidate if test(item)),
        ),
        "test_by_season": {
            str(year): _comparison(
                tuple(item for item in baseline if _season(item) == year),
                tuple(item for item in candidate if _season(item) == year),
            )
            for year in sorted({_season(item) for item in baseline if test(item)})
        },
        "test_by_venue": {
            venue: _comparison(
                tuple(item for item in baseline if test(item) and item.venue == venue),
                tuple(item for item in candidate if test(item) and item.venue == venue),
            )
            for venue in ("home", "away")
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_paths", nargs="+", type=Path)
    args = parser.parse_args()
    data = load_shot_data(args.csv_paths)
    result = run_experiment(data.matches)
    result["data_quality"] = {
        "rows_read": data.rows_read,
        "rows_loaded": data.rows_loaded,
        "rows_without_corner_results": data.rows_without_corner_results,
        "quarantined_shot_rows": data.quarantined_shot_rows,
    }
    result["source_files"] = [
        {"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in args.csv_paths
    ]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
