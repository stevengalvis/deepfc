"""Verbatim function from ModelFC commit14e7fa9f237783854625982037b1feccd2781af6 forecasts.py.
Source SHA256:7b2fdc689d26a5b3e8425b882fb29f1fc09cabae088dfd9ac552217f7a4415ac
Only imports/type annotation context supplied locally; estimator body unchanged.
"""
from __future__ import annotations
import math
from typing import Iterable

def estimate_expected_goals(
    history: Iterable[Match],
    home_team: str,
    away_team: str,
    smoothing_matches: float = 5.0,
) -> tuple[float, float]:
    """Estimate goal rates from venue-specific attack and defence records.

    Team rates are shrunk toward the corresponding league scoring rate using
    ``smoothing_matches`` pseudo-matches.  League rates themselves use the
    same number of one-goal pseudo-matches, keeping estimates positive even in
    an unusually scoreless or very small history.
    """

    if (
        not isinstance(smoothing_matches, (int, float))
        or isinstance(smoothing_matches, bool)
        or not math.isfinite(smoothing_matches)
        or smoothing_matches <= 0
    ):
        raise ValueError("smoothing_matches must be a finite positive number")

    matches = list(history)
    match_count = len(matches)
    league_home_rate = (
        sum(match.home_goals for match in matches) + smoothing_matches
    ) / (match_count + smoothing_matches)
    league_away_rate = (
        sum(match.away_goals for match in matches) + smoothing_matches
    ) / (match_count + smoothing_matches)

    home_games = home_scored = home_conceded = 0
    away_games = away_scored = away_conceded = 0
    for match in matches:
        if match.home_team == home_team:
            home_games += 1
            home_scored += match.home_goals
            home_conceded += match.away_goals
        if match.away_team == away_team:
            away_games += 1
            away_scored += match.away_goals
            away_conceded += match.home_goals

    home_attack_rate = (home_scored + smoothing_matches * league_home_rate) / (
        home_games + smoothing_matches
    )
    home_defence_rate = (home_conceded + smoothing_matches * league_away_rate) / (
        home_games + smoothing_matches
    )
    away_attack_rate = (away_scored + smoothing_matches * league_away_rate) / (
        away_games + smoothing_matches
    )
    away_defence_rate = (away_conceded + smoothing_matches * league_home_rate) / (
        away_games + smoothing_matches
    )

    expected_home = home_attack_rate * away_defence_rate / league_home_rate
    expected_away = away_attack_rate * home_defence_rate / league_away_rate
    return expected_home, expected_away
