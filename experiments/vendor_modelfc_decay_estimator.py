"""Verbatim functions from ModelFC14e7fa9f237783854625982037b1feccd2781af6."""
from __future__ import annotations
from datetime import date
from typing import Iterable
import math
from experiments.vendor_modelfc_goal_estimator import estimate_expected_goals

def exponential_time_weight(
    match_date: date,
    reference_date: date,
    half_life_days: float = 180.0,
) -> float:
    """Return a match's exponential weight relative to a later date.

    A match exactly one half-life old receives weight 0.5.  Callers must pass
    a strictly earlier match date so this helper cannot silently enable
    target-date or future leakage.
    """

    if (
        not isinstance(half_life_days, (int, float))
        or isinstance(half_life_days, bool)
        or not math.isfinite(half_life_days)
        or half_life_days <= 0
    ):
        raise ValueError("half_life_days must be a finite positive number")
    age_days = (reference_date - match_date).days
    if age_days <= 0:
        raise ValueError("match_date must be strictly earlier than reference_date")
    return math.exp2(-age_days / half_life_days)

def estimate_decay_expected_goals(
    history: Iterable[Match],
    home_team: str,
    away_team: str,
    reference_date: date,
    half_life_days: float = 180.0,
    smoothing_matches: float = 5.0,
) -> tuple[float, float]:
    """Estimate venue-specific rates with exponential recency weighting."""

    # Reuse the established smoothing validation without changing that model.
    estimate_expected_goals([], "home", "away", smoothing_matches)
    weighted_matches = [
        (
            match,
            exponential_time_weight(
                match.match_date, reference_date, half_life_days
            ),
        )
        for match in history
    ]
    total_weight = sum(weight for _, weight in weighted_matches)
    league_home_rate = (
        sum(weight * match.home_goals for match, weight in weighted_matches)
        + smoothing_matches
    ) / (total_weight + smoothing_matches)
    league_away_rate = (
        sum(weight * match.away_goals for match, weight in weighted_matches)
        + smoothing_matches
    ) / (total_weight + smoothing_matches)

    home_weight = home_scored = home_conceded = 0.0
    away_weight = away_scored = away_conceded = 0.0
    for match, weight in weighted_matches:
        if match.home_team == home_team:
            home_weight += weight
            home_scored += weight * match.home_goals
            home_conceded += weight * match.away_goals
        if match.away_team == away_team:
            away_weight += weight
            away_scored += weight * match.away_goals
            away_conceded += weight * match.home_goals

    home_attack_rate = (home_scored + smoothing_matches * league_home_rate) / (
        home_weight + smoothing_matches
    )
    home_defence_rate = (home_conceded + smoothing_matches * league_away_rate) / (
        home_weight + smoothing_matches
    )
    away_attack_rate = (away_scored + smoothing_matches * league_away_rate) / (
        away_weight + smoothing_matches
    )
    away_defence_rate = (away_conceded + smoothing_matches * league_home_rate) / (
        away_weight + smoothing_matches
    )
    return (
        home_attack_rate * away_defence_rate / league_home_rate,
        away_attack_rate * home_defence_rate / league_away_rate,
    )
