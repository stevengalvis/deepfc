"""Isolated Championship goals/BTTS research; no provider or production code."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from dataclasses import dataclass
from datetime import date
import hashlib
from itertools import groupby
import json
import math
from pathlib import Path
import random
from typing import Iterable

from deepfc.football_data_csv import _parse_date, load_football_data_csv
from deepfc.match_data import Match
from deepfc.team_corners import smoothed_average
from deepfc.total_corners import DEFAULT_EVALUATION_START
from experiments.time_decay import HALF_LIFE_DAYS, time_weight


HOLDOUT_START = date(2024, 7, 1)
PRIOR_MATCHES = 5
MIN_HISTORY = 100
MIN_RHO_HISTORY = 50
RHO_LIMIT = 0.25
TARGETS = ("over_2_5", "btts_yes")
BASE_MODELS = ("venue_poisson", "team_arithmetic", "team_multiplicative", "team_decay_180")


@dataclass(frozen=True)
class GoalMatch:
    """Canonical existing Match identity with experimental full-time goals."""

    match: Match
    home_goals: int
    away_goals: int
    season: str | None = None

    def __post_init__(self) -> None:
        for value in (self.home_goals, self.away_goals):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("goals must be non-negative integers")

    @property
    def outcomes(self) -> tuple[int, int]:
        return (int(self.home_goals + self.away_goals >= 3),
                int(self.home_goals > 0 and self.away_goals > 0))


@dataclass(frozen=True)
class Forecast:
    match: GoalMatch
    probabilities: tuple[float, float]
    home_rate: float | None = None
    away_rate: float | None = None
    rho: float | None = None


def load_goals(paths: Iterable[Path]) -> tuple[tuple[GoalMatch, ...], dict]:
    """Join goals onto the existing DeepFC completed-match cohort.

    The shared corner adapter excludes rows without both corner results.
    This excludes the ambiguous Bolton-Brentford 2019-04-27 source row;
    its 0-1 goal fields are not assumed to be an observed played result.
    Raw CSVs are never edited. Corner counts are not model features.
    """
    paths = list(paths)
    loaded = load_football_data_csv(paths)
    goals = {}
    manifest = []
    for path in paths:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            required = {"Date", "Div", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}
            if not required <= set(reader.fieldnames or ()):
                raise ValueError(f"{path}: missing goal/identity fields")
            rows = 0
            for number, row in enumerate(reader, 2):
                rows += 1
                if None in row or row["Div"] != "E1":
                    raise ValueError(f"{path} row {number}: malformed/non-E1 fixture")
                key = (_parse_date(row["Date"]), row["Div"],
                       row["HomeTeam"].strip(), row["AwayTeam"].strip())
                if key in goals:
                    raise ValueError("duplicate fixture; use non-overlapping season files")
                values = []
                for field in ("FTHG", "FTAG"):
                    try:
                        value = float(row[field])
                        if not math.isfinite(value) or not value.is_integer() or value < 0:
                            raise ValueError
                        values.append(int(value))
                    except (TypeError, ValueError):
                        raise ValueError(f"{path} row {number}: invalid goal result") from None
                goals[key] = (*values, path.stem.removeprefix("E1_"))
        manifest.append({"filename": path.name, "rows": rows,
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    joined = tuple(GoalMatch(m, *goals[(m.match_date, m.competition, m.home_team, m.away_team)])
                   for m in loaded.matches)
    return joined, {"rows_read": loaded.rows_read, "rows_loaded": len(joined),
                    "rows_without_corner_results": loaded.rows_without_corner_results,
                    "excluded_source_rows": len(goals) - len(joined), "files": manifest}


def poisson_probabilities(home_rate: float, away_rate: float) -> tuple[float, float]:
    if any(not math.isfinite(x) or x < 0 for x in (home_rate, away_rate)):
        raise ValueError("rates must be finite and non-negative")
    total = home_rate + away_rate
    over = 1 - math.exp(-total) * (1 + total + total * total / 2)
    btts = -math.expm1(-home_rate) * -math.expm1(-away_rate)
    return (min(1.0, max(0.0, over)), min(1.0, max(0.0, btts)))


def dc_coefficients(home_rate: float, away_rate: float) -> tuple[float, ...]:
    """Coefficients of rho for cells 0-0, 0-1, 1-0 and 1-1."""
    return (-home_rate * away_rate, home_rate, away_rate, -1.0)


def dixon_coles_probabilities(home_rate: float, away_rate: float,
                             rho: float) -> tuple[float, float]:
    over, btts = poisson_probabilities(home_rate, away_rate)
    if not math.isfinite(rho) or any(1 + c * rho <= 0
                                   for c in dc_coefficients(home_rate, away_rate)):
        raise ValueError("rho produces a non-positive score-cell multiplier")
    # DC only redistributes mass between cells whose total is <= 2.
    # O/U 2.5 is therefore EXACTLY invariant for unchanged rates.
    btts -= rho * home_rate * away_rate * math.exp(-home_rate - away_rate)
    if not 0 <= btts <= 1:
        raise ValueError("invalid corrected probability")
    return over, btts


@dataclass
class GoalHistory:
    count: float = 0
    scored: float = 0
    conceded: float = 0

    def decay(self, weight: float) -> None:
        self.count *= weight
        self.scored *= weight
        self.conceded *= weight

    def record(self, scored: int, conceded: int) -> None:
        self.count += 1
        self.scored += scored
        self.conceded += conceded


class RateHistory:
    """Venue-role histories using DeepFC's existing five-match smoothing."""

    def __init__(self, half_life: int | None = None):
        self.half_life = half_life
        self.last_date = None
        self.home = defaultdict(GoalHistory)
        self.away = defaultdict(GoalHistory)
        self.league_home = GoalHistory()
        self.league_away = GoalHistory()

    def advance(self, day: date) -> None:
        if self.last_date is not None:
            age = (day - self.last_date).days
            if age <= 0:
                raise ValueError("dates must advance strictly")
            weight = 1.0 if self.half_life is None else time_weight(age, self.half_life)
            for history in [self.league_home, self.league_away,
                            *self.home.values(), *self.away.values()]:
                history.decay(weight)
        self.last_date = day

    def rates(self, match: GoalMatch, formula: str) -> tuple[float, float]:
        def rate(team, opponent, league):
            average = max(1e-9, league.scored / league.count)
            if formula == "venue":
                return average
            attack = smoothed_average(team.scored, team.count, average, PRIOR_MATCHES)
            defence = smoothed_average(opponent.conceded, opponent.count, average, PRIOR_MATCHES)
            if formula == "arithmetic":
                return (attack + defence) / 2
            return attack * defence / average
        home = self.home.get(match.match.home_team, GoalHistory())
        away = self.away.get(match.match.away_team, GoalHistory())
        return (rate(home, away, self.league_home),
                rate(away, home, self.league_away))

    def record(self, match: GoalMatch) -> None:
        self.home[match.match.home_team].record(match.home_goals, match.away_goals)
        self.away[match.match.away_team].record(match.away_goals, match.home_goals)
        self.league_home.record(match.home_goals, match.away_goals)
        self.league_away.record(match.away_goals, match.home_goals)


def fit_rho(history: list[tuple[date, float]], prediction_date: date,
            home_rate: float, away_rate: float, *, half_life: int | None) -> float:
    """Conditional DC likelihood on strictly earlier prequential forecasts.

    This is not a joint team-strength/DC maximum-likelihood refit. No scored
    fixture's result participates in its own intensity or rho estimation.
    """
    if any(day >= prediction_date for day, _ in history):
        raise ValueError("rho history must precede the prediction date")
    if len(history) < MIN_RHO_HISTORY:
        return 0.0
    low, high = -RHO_LIMIT, RHO_LIMIT
    for c in [*(c for _, c in history), *dc_coefficients(home_rate, away_rate)]:
        if c > 0:
            low = max(low, -0.95 / c)
        elif c < 0:
            high = min(high, -0.95 / c)
    weighted = [(c, 1.0 if half_life is None else time_weight(
        (prediction_date - day).days, half_life)) for day, c in history]

    def derivative(rho):
        return sum(weight * c / (1 + c * rho) for c, weight in weighted)

    if derivative(low) <= 0:
        return low
    if derivative(high) >= 0:
        return high
    for _ in range(45):
        midpoint = (low + high) / 2
        if derivative(midpoint) > 0:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2


def compare_models(matches: Iterable[GoalMatch], *,
                   evaluation_start: date = DEFAULT_EVALUATION_START) -> dict[str, tuple[Forecast, ...]]:
    ordered = sorted(matches, key=lambda m: m.match.match_date)
    if not ordered or any(m.match.competition != "E1" for m in ordered):
        raise ValueError("provide nonempty E1 history")
    keys = [(m.match.match_date, m.match.home_team, m.match.away_team) for m in ordered]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate fixture")
    equal, decayed = RateHistory(), RateHistory(HALF_LIFE_DAYS)
    dc_history = {name: [] for name in BASE_MODELS}
    models = {name: [] for name in ["coin_0_5", "expanding_event_rate",
                                   *BASE_MODELS, *(n + "_dc" for n in BASE_MODELS)]}
    counts = [0, 0]
    count = 0
    for day, group in groupby(ordered, key=lambda m: m.match.match_date):
        on_date = list(group)
        equal.advance(day)
        decayed.advance(day)
        pending = []
        if count >= MIN_HISTORY:
            rates_on_date = [
                {
                    "venue_poisson": equal.rates(match, "venue"),
                    "team_arithmetic": equal.rates(match, "arithmetic"),
                    "team_multiplicative": equal.rates(match, "multiplicative"),
                    "team_decay_180": decayed.rates(match, "multiplicative"),
                }
                for match in on_date
            ]
            rhos = {}
            if day >= evaluation_start:
                for name in BASE_MODELS:
                    # One league-level rho per model/date. The known fixture
                    # rates bound all today's cells; no today's results enter.
                    rhos[name] = fit_rho(
                        dc_history[name], day,
                        max(rates[name][0] for rates in rates_on_date),
                        max(rates[name][1] for rates in rates_on_date),
                        half_life=HALF_LIFE_DAYS if name == "team_decay_180" else None)
            for match, rates in zip(on_date, rates_on_date):
                if day >= evaluation_start:
                    models["coin_0_5"].append(Forecast(match, (0.5, 0.5)))
                    models["expanding_event_rate"].append(Forecast(
                        match, tuple((n + 1) / (count + 2) for n in counts)))
                for name, (home, away) in rates.items():
                    if day >= evaluation_start:
                        rho = rhos[name]
                        models[name].append(Forecast(match, poisson_probabilities(home, away), home, away))
                        models[name + "_dc"].append(Forecast(
                            match, dixon_coles_probabilities(home, away, rho), home, away, rho))
                    if match.home_goals <= 1 and match.away_goals <= 1:
                        c = dc_coefficients(home, away)[match.home_goals * 2 + match.away_goals]
                        pending.append((name, day, c))
        # Predict ALL fixtures on a date before adding ANY same-date results.
        for name, observed_day, c in pending:
            dc_history[name].append((observed_day, c))
        for match in on_date:
            equal.record(match)
            decayed.record(match)
            count += 1
            counts = [a + b for a, b in zip(counts, match.outcomes)]
    return {name: tuple(values) for name, values in models.items()}


def evaluate(predictions: Iterable[Forecast]) -> dict:
    predictions = list(predictions)
    if not predictions:
        raise ValueError("no predictions")
    result = {"n": len(predictions), "first_date": predictions[0].match.match.match_date.isoformat(),
              "last_date": predictions[-1].match.match.match_date.isoformat()}
    for index, target in enumerate(TARGETS):
        values = [(p.probabilities[index], p.match.outcomes[index]) for p in predictions]
        bins = []
        for bucket in range(10):
            entries = [(p, y) for p, y in values if min(9, int(p * 10)) == bucket]
            bins.append({"lower": bucket / 10, "upper": (bucket + 1) / 10, "n": len(entries),
                         "mean_predicted": sum(p for p, _ in entries) / len(entries) if entries else None,
                         "observed_rate": sum(y for _, y in entries) / len(entries) if entries else None})
        mean = sum(p for p, _ in values) / len(values)
        actual = sum(y for _, y in values) / len(values)
        result[target] = {"brier": sum((p - y) ** 2 for p, y in values) / len(values),
                          "mean_predicted": mean, "observed_rate": actual,
                          "calibration_bias": mean - actual,
                          "ece_10_equal_width": sum(b["n"] * abs(b["mean_predicted"] - b["observed_rate"])
                                                    for b in bins if b["n"]) / len(values),
                          "calibration_bins": bins}
    rhos = [p.rho for p in predictions if p.rho is not None]
    if rhos:
        result["rho"] = {"mean": sum(rhos) / len(rhos), "min": min(rhos), "max": max(rhos)}
    return result


def paired_block_interval(before: Iterable[Forecast], after: Iterable[Forecast], target: int,
                          *, samples: int = 2000, seed: int = 7) -> dict:
    before, after = list(before), list(after)
    if not before or len(before) != len(after) or samples <= 0 or target not in (0, 1):
        raise ValueError("matching nonempty forecasts, positive samples and valid target required")
    blocks = defaultdict(list)
    for a, b in zip(before, after):
        if a.match != b.match:
            raise ValueError("forecasts must share the same ordered fixtures")
        outcome = a.match.outcomes[target]
        delta = (b.probabilities[target] - outcome) ** 2 - (a.probabilities[target] - outcome) ** 2
        blocks[a.match.match.match_date.toordinal() // 28].append(delta)
    totals = [(len(v), sum(v)) for v in blocks.values()]
    rng = random.Random(seed)
    differences = []
    for _ in range(samples):
        chosen = rng.choices(totals, k=len(totals))
        differences.append(sum(s for _, s in chosen) / sum(n for n, _ in chosen))
    differences.sort()
    return {"delta_brier": sum(s for _, s in totals) / sum(n for n, _ in totals),
            "lower_95": differences[int(.025 * (samples - 1))],
            "upper_95": differences[int(.975 * (samples - 1))],
            "blocks": len(totals), "samples": samples,
            "fraction_below_zero": sum(d < 0 for d in differences) / samples}


def run_experiment(paths: Iterable[Path]) -> dict:
    matches, quality = load_goals(paths)
    compared = compare_models(matches)
    windows = {
        "all_scored": lambda p: True,
        "development_2018_2024": lambda p: p.match.match.match_date < HOLDOUT_START,
        "latest_two_seasons_2024_2026": lambda p: p.match.match.match_date >= HOLDOUT_START,
    }
    metrics, intervals = {}, {}
    for window, eligible in windows.items():
        selected = {n: tuple(p for p in v if eligible(p)) for n, v in compared.items()}
        metrics[window] = {n: evaluate(v) for n, v in selected.items()}
        if window == "development_2018_2024":
            continue
        pairs = [("team_decay_180", "expanding_event_rate"),
                 ("team_arithmetic", "expanding_event_rate"),
                 ("team_multiplicative", "expanding_event_rate"),
                 ("team_decay_180", "team_arithmetic"),
                 ("team_decay_180", "team_multiplicative"),
                 *((n + "_dc", n) for n in BASE_MODELS)]
        intervals[window] = {a + "_minus_" + b: {
            target: paired_block_interval(selected[b], selected[a], index)
            for index, target in enumerate(TARGETS)} for a, b in pairs}
    seasonal = {}
    for season in range(2018, 2026):
        seasonal[str(season) + "-" + str(season + 1)] = {}
        for name, values in compared.items():
            # Source season, not July boundaries: COVID delayed 2019-20
            # Championship fixtures into July 2020.
            code = f"{season % 100:02d}{(season + 1) % 100:02d}"
            selected = [p for p in values if p.match.season == code]
            summary = evaluate(selected)
            seasonal[str(season) + "-" + str(season + 1)][name] = {
                "n": summary["n"], **{t: {k: v for k, v in summary[t].items() if k != "calibration_bins"}
                                        for t in TARGETS}}
    return {"settings": {"competition": "E1", "evaluation_start": DEFAULT_EVALUATION_START.isoformat(),
                         "latest_two_season_start": HOLDOUT_START.isoformat(), "half_life_days": HALF_LIFE_DAYS,
                         "prior_matches": PRIOR_MATCHES, "minimum_history": MIN_HISTORY,
                         "minimum_low_score_rho_history": MIN_RHO_HISTORY, "rho_limit": RHO_LIMIT,
                         "dc_fit": "earlier prequential low-score conditional likelihood; NOT joint rate/DC refit",
                         "same_date_results_excluded": True, "hyperparameter_search": False,
                         "latest_two_seasons_are_pseudo_holdout": True},
            "data_quality": quality, "metrics": metrics,
            "paired_28_day_block_intervals": intervals, "seasonal_metrics": seasonal}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_paths", nargs="+", type=Path)
    args = parser.parse_args()
    print(json.dumps(run_experiment(args.csv_paths), indent=2))


if __name__ == "__main__":
    main()
