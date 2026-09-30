"""Compare DeepFC with a pinned Zeno baseline and its fixed 180-day challenger.

Research only. Import Zeno from its separate checkout via PYTHONPATH. Reuse its
implementations rather than maintain a second copy of the production formulas.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date, datetime, timezone
import hashlib
import inspect
import json
import math
from pathlib import Path
import random
import subprocess

from deepfc.corner_distribution import negative_binomial_negative_log_loss
from deepfc.football_data_csv import load_football_data_csv
from deepfc.match_data import Match
from deepfc.team_corners import (
    TEAM_CORNER_LINES, TeamCornerPrediction, evaluate_predictions,
    walk_forward_prediction_comparison,
)
from modelfc.corner_forecasts import corner_line_probabilities, predict_corner_fixture
from modelfc.corner_recency_experiment import rolling_recency_rows
from modelfc.corners import negative_binomial_log_probability
from modelfc.matches import TeamCornerObservation, UpcomingFixture, Venue


ZENO_REFERENCE_SHA = "06cf7c0d84ca671c3e1a0d0ba57ab050b3f5164a"
MODEL_NAMES = ("deepfc", "zeno", "zeno_decay_180")
EVALUATION_START = date(2018, 7, 1)


def observations_from_matches(matches: list[Match]) -> list[TeamCornerObservation]:
    observations = []
    for match in matches:
        observations.extend((
            TeamCornerObservation(match.match_date, match.home_team, match.away_team,
                                  Venue.HOME, match.home_corners, match.away_corners),
            TeamCornerObservation(match.match_date, match.away_team, match.home_team,
                                  Venue.AWAY, match.away_corners, match.home_corners),
        ))
    return observations


def compare_predictions(
    matches: list[Match], evaluation_start: date = EVALUATION_START,
    *, min_history: int = 100, min_venue_history: int = 5,
) -> dict[str, list[TeamCornerPrediction]]:
    """Predict identical observations; gates affect scoring, never the history."""
    identities = [(m.match_date, m.home_team, m.away_team) for m in matches]
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate fixture; supply non-overlapping season files")
    if not matches or any(m.competition != "E1" for m in matches):
        raise ValueError("provide nonempty Championship (E1) history only")
    by_fixture = dict(zip(identities, matches))
    deepfc = {
        (p.match, p.venue): p
        for p in walk_forward_prediction_comparison(matches, evaluation_start).team_opponent
    }
    rows = rolling_recency_rows(
        observations_from_matches(matches), windows=(20,), half_life_days=(180.0,),
        min_history=min_history, min_venue_history=min_venue_history,
        smoothing_matches=5.0,
    )
    predictions = {name: [] for name in MODEL_NAMES}
    for row in rows:
        item = row.observation
        if item.match_date < evaluation_start:
            continue
        home, away = ((item.team, item.opponent) if item.venue is Venue.HOME
                      else (item.opponent, item.team))
        match = by_fixture[item.match_date, home, away]
        predictions["deepfc"].append(deepfc[match, item.venue.value])
        for name, mean in (("zeno", row.expanding_mean),
                           ("zeno_decay_180", dict(row.decay_means)[180.0])):
            predictions[name].append(TeamCornerPrediction(
                match=match, team=item.team, venue=item.venue.value,
                expected_corners=mean, actual_corners=item.corners_for,
                over_probabilities={
                    line: corner_line_probabilities(mean, line, row.dispersion_size).over
                    for line in TEAM_CORNER_LINES
                },
                dispersion=1.0 / row.dispersion_size,
            ))
    # Both venue gates must pass for a fixture to enter this common cohort.
    fixture_counts: dict[Match, int] = defaultdict(int)
    for prediction in predictions["zeno"]:
        fixture_counts[prediction.match] += 1
    if not fixture_counts or any(count != 2 for count in fixture_counts.values()):
        raise ValueError("expected two team observations per eligible fixture")
    return predictions


def verify_production_parity(
    matches: list[Match], predictions: list[TeamCornerPrediction],
    *, min_history: int = 100, min_venue_history: int = 5,
) -> dict[str, float | int]:
    """Check every baseline mean, spread and line against Zeno's actual entry point."""
    observations = observations_from_matches(matches)
    by_fixture: dict[Match, list[TeamCornerPrediction]] = defaultdict(list)
    for prediction in predictions:
        by_fixture[prediction.match].append(prediction)
    largest_difference = 0.0
    for match, team_predictions in by_fixture.items():
        forecast = predict_corner_fixture(
            observations, UpcomingFixture(match.match_date, match.home_team, match.away_team),
            TEAM_CORNER_LINES, TEAM_CORNER_LINES,
            min_history=min_history, min_venue_history=min_venue_history,
        )
        for prediction in team_predictions:
            team = forecast.home if prediction.venue == "home" else forecast.away
            pairs = [(prediction.expected_corners, team.expected_corners),
                     (prediction.dispersion, 1.0 / forecast.dispersion_size)]
            pairs.extend((prediction.over_probabilities[line.line], line.over)
                         for line in team.lines)
            for actual, expected in pairs:
                largest_difference = max(largest_difference, abs(actual - expected))
                if not math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10):
                    raise ValueError("research baseline differs from Zeno production")
    return {"fixtures_checked": len(by_fixture), "max_absolute_difference": largest_difference}


def count_loss(prediction: TeamCornerPrediction) -> float:
    """Use Zeno's stable NB log mass, including its finite-size Poisson fallback."""
    if prediction.dispersion == 0:
        return negative_binomial_negative_log_loss(
            prediction.actual_corners, prediction.expected_corners, 0.0,
        )
    return -negative_binomial_log_probability(
        prediction.actual_corners, prediction.expected_corners, 1.0 / prediction.dispersion,
    )


def summarize(predictions: list[TeamCornerPrediction]) -> dict:
    summary = evaluate_predictions(predictions)
    summary["negative_binomial_negative_log_loss"] = (
        sum(count_loss(p) for p in predictions) / len(predictions)
    )
    # Fixed reliability bins supplement average bias; empty bins remain explicit.
    for line, metrics in summary["lines"].items():
        values = [(p.over_probabilities[float(line)], int(p.actual_corners > float(line)))
                  for p in predictions]
        metrics["calibration_bins"] = []
        for bin_index in range(5):
            members = [(p, y) for p, y in values if min(int(p * 5), 4) == bin_index]
            metrics["calibration_bins"].append({
                "lower": bin_index / 5, "upper": (bin_index + 1) / 5,
                "count": len(members),
                "mean_probability": sum(p for p, _ in members) / len(members) if members else None,
                "observed_rate": sum(y for _, y in members) / len(members) if members else None,
            })
    return summary


def paired_block_bootstrap(
    baseline: list[TeamCornerPrediction], challenger: list[TeamCornerPrediction],
    *, samples: int = 2000, seed: int = 7,
) -> dict:
    """Resample paired 28-day blocks, retaining teams and lines within fixtures."""
    if samples < 1 or not baseline or len(baseline) != len(challenger):
        raise ValueError("positive samples and matching nonempty predictions required")
    blocks: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for before, after in zip(baseline, challenger):
        if (before.match, before.venue) != (after.match, after.venue):
            raise ValueError("bootstrap requires identical ordered observations")
        brier_delta = sum(
            (after.over_probabilities[line] - (after.actual_corners > line)) ** 2
            - (before.over_probabilities[line] - (before.actual_corners > line)) ** 2
            for line in TEAM_CORNER_LINES
        ) / len(TEAM_CORNER_LINES)
        blocks[before.match.match_date.toordinal() // 28].append(
            (brier_delta, count_loss(after) - count_loss(before))
        )
    totals = [(len(items), sum(x[0] for x in items), sum(x[1] for x in items))
              for items in blocks.values()]
    rng = random.Random(seed)
    sampled = [[], []]
    for _ in range(samples):
        selected = rng.choices(totals, k=len(totals))
        count = sum(item[0] for item in selected)
        for index in range(2):
            sampled[index].append(sum(item[index + 1] for item in selected) / count)
    result = {"samples": samples, "seed": seed, "block_days": 28, "blocks": len(totals)}
    for name, deltas in zip(("mean_brier_score", "count_nll"), sampled):
        ordered = sorted(deltas)
        result[name] = {"lower_95": ordered[int(.025 * (samples - 1))],
                        "upper_95": ordered[int(.975 * (samples - 1))],
                        "fraction_below_zero": sum(x < 0 for x in deltas) / samples}
    return result


def _git_revision(root: Path) -> str:
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def run_comparison(paths: list[Path], evaluation_start: date = EVALUATION_START) -> dict:
    zeno_root = Path(inspect.getfile(rolling_recency_rows)).resolve().parents[2]
    if _git_revision(zeno_root) != ZENO_REFERENCE_SHA:
        raise ValueError(f"checkout Zeno reference {ZENO_REFERENCE_SHA}")
    if subprocess.check_output(
        ["git", "-C", str(zeno_root), "status", "--porcelain", "--", "src"], text=True,
    ).strip():
        raise ValueError("Zeno reference source must be clean")
    matches, season_by_match, sources = [], {}, []
    quality = {"rows_read": 0, "rows_loaded": 0, "rows_without_corner_results": 0}
    for path in paths:
        loaded = load_football_data_csv([path])
        matches.extend(loaded.matches)
        # Source-file season labels correctly retain July 2020 in 2019/20.
        season_by_match.update({match: path.stem for match in loaded.matches})
        sources.append({"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        for field in quality:
            quality[field] += getattr(loaded, field)
    if any(m.match_date >= datetime.now(timezone.utc).date() for m in matches):
        raise ValueError("completed historical data must precede today's UTC date")
    predictions = compare_predictions(matches, evaluation_start)
    results = {}
    for name, rows in predictions.items():
        results[name] = {
            "overall": summarize(rows),
            "by_venue": {venue: summarize([p for p in rows if p.venue == venue])
                         for venue in ("home", "away")},
            "by_season": {season: summarize([p for p in rows if season_by_match[p.match] == season])
                          for season in sorted({season_by_match[p.match] for p in rows})},
        }
    evaluated = predictions["zeno"]
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "deepfc_revision": _git_revision(Path(__file__).resolve().parents[1]),
        "experiment_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "zeno_revision": ZENO_REFERENCE_SHA, "sources": sources, "data_quality": quality,
        "settings": {"evaluation_start": evaluation_start.isoformat(), "min_history": 100,
                     "min_venue_history": 5, "smoothing_matches": 5,
                     "half_life_days": 180, "lines": TEAM_CORNER_LINES,
                     "history": "all supplied strictly earlier dates",
                     "primary_metric": "mean_brier_score"},
        "coverage": {
            "first_scored_date": min(p.match.match_date for p in evaluated).isoformat(),
            "last_scored_date": max(p.match.match_date for p in evaluated).isoformat(),
            "scored_fixtures": len(evaluated) // 2,
            "candidate_fixtures": sum(m.match_date >= evaluation_start for m in matches),
        },
        "production_parity": verify_production_parity(matches, evaluated),
        "models": results,
        "paired_28_day_bootstrap": {
            f"{challenger}_minus_{baseline}": paired_block_bootstrap(
                predictions[baseline], predictions[challenger],
            )
            for baseline, challenger in (("zeno", "deepfc"), ("zeno", "zeno_decay_180"),
                                        ("deepfc", "zeno_decay_180"))
        },
        "interpretation": "Retrospective comparison of previously inspected seasons; not an untouched test or ROI estimate.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_paths", nargs="+", type=Path)
    parser.add_argument("--evaluation-start", type=date.fromisoformat, default=EVALUATION_START)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_comparison(args.csv_paths, args.evaluation_start)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({name: {key: values["overall"][key] for key in (
        "evaluated_team_observations", "mae", "negative_binomial_negative_log_loss", "mean_brier_score",
    )} for name, values in report["models"].items()}, indent=2))


if __name__ == "__main__":
    main()
