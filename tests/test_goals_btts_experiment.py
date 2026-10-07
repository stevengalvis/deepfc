from dataclasses import replace
from datetime import date, timedelta
import math

import pytest

from deepfc.match_data import Match
from experiments.goals_btts import (
    Forecast, GoalMatch, RateHistory, compare_models, dc_coefficients,
    dixon_coles_probabilities, evaluate, fit_rho, load_goals,
    paired_block_interval, poisson_probabilities,
)


def history():
    return [GoalMatch(Match(date(2017, 1, 1) + timedelta(days=i // 2),
                            "E1", "A" if i % 2 else "C", "B" if i % 2 else "D", 5, 4),
                      (0, 1, 3, 2, 0, 2)[i % 6], (0, 1, 0, 2, 1, 2)[i % 6])
            for i in range(160)]


def test_poisson_targets_and_complements():
    over, yes = poisson_probabilities(1.5, 1.0)
    assert over == pytest.approx(1 - math.exp(-2.5) * (1 + 2.5 + 2.5**2 / 2))
    assert yes == pytest.approx((1 - math.exp(-1.5)) * (1 - math.exp(-1)))
    assert poisson_probabilities(0, 0) == (0, 0)
    assert (1 - over) + over == 1
    assert (1 - yes) + yes == 1
    with pytest.raises(ValueError):
        poisson_probabilities(-1, 1)


@pytest.mark.parametrize("rho", [-0.2, 0, 0.2])
def test_dc_mass_and_ou_2_5_invariance(rho):
    home, away = 1.4, 1.1
    ordinary = poisson_probabilities(home, away)
    corrected = dixon_coles_probabilities(home, away, rho)
    assert corrected[0] == ordinary[0]
    assert corrected[1] == pytest.approx(ordinary[1] - rho * home * away * math.exp(-home-away))
    shifts = []
    for h, a in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        coefficient = dc_coefficients(home, away)[h * 2 + a]
        probability = math.exp(-home-away) * home**h * away**a
        shifts.append(probability * coefficient * rho)
    assert sum(shifts) == pytest.approx(0, abs=1e-15)
    with pytest.raises(ValueError):
        dixon_coles_probabilities(home, away, 1)


def test_negative_rho_increases_btts():
    assert dixon_coles_probabilities(1.4, 1.1, -.1)[1] > poisson_probabilities(1.4, 1.1)[1]


def test_all_models_share_fixture_cohort():
    values = compare_models(history(), evaluation_start=date(2017, 1, 1))
    assert len(values) == 10
    assert all(len(v) == 60 for v in values.values())
    assert all([p.match for p in v] == [p.match for p in values["coin_0_5"]]
               for v in values.values())


def test_same_date_and_future_results_do_not_change_predictions():
    matches = history()
    cutoff = matches[120].match.match_date
    before = compare_models(matches, evaluation_start=date(2017, 1, 1))
    changed = [replace(m, home_goals=9, away_goals=8)
               if m.match.match_date >= cutoff else m for m in matches]
    after = compare_models(changed, evaluation_start=date(2017, 1, 1))
    for name in before:
        first = [p for p in before[name] if p.match.match.match_date <= cutoff]
        second = [p for p in after[name] if p.match.match.match_date <= cutoff]
        assert [(p.probabilities, p.home_rate, p.away_rate, p.rho) for p in first] == [
            (p.probabilities, p.home_rate, p.away_rate, p.rho) for p in second]
    # Later dates can learn earlier changed results, but never the same date.
    assert before["expanding_event_rate"][-1].probabilities != after["expanding_event_rate"][-1].probabilities


def test_current_date_fixture_order_cannot_change_forecasts():
    matches = history()
    original = compare_models(matches, evaluation_start=date(2017, 1, 1))
    swapped = compare_models(list(reversed(matches)), evaluation_start=date(2017, 1, 1))
    key = lambda p: (p.match.match.match_date, p.match.match.home_team)
    for name in original:
        assert {key(p):p.probabilities for p in original[name]} == {
            key(p):p.probabilities for p in swapped[name]}


def test_time_decay_uses_earlier_effective_venue_counts():
    h = RateHistory(180)
    m = history()[0]
    h.advance(m.match.match_date)
    h.record(m)
    h.advance(m.match.match_date + timedelta(days=180))
    assert h.league_home.count == pytest.approx(.5)
    assert h.home[m.match.home_team].count == pytest.approx(.5)
    with pytest.raises(ValueError):
        h.advance(h.last_date)


def test_rho_likelihood_uses_past_only_and_valid_bounds():
    past = [(date(2017, 1, 1), -1.0)] * 60
    rho = fit_rho(past, date(2017, 2, 1), 2, 2, half_life=None)
    assert rho == -.25
    assert all(1 + c * rho > 0 for c in dc_coefficients(2, 2))
    assert fit_rho([], date(2017, 2, 1), 2, 2, half_life=None) == 0
    with pytest.raises(ValueError):
        fit_rho([(date(2017, 2, 1), -1)], date(2017, 2, 1), 2, 2, half_life=None)


def test_metrics_calibration_bins_and_block_interval():
    m = history()[0]
    predictions = [Forecast(m, (.25, .5)), Forecast(replace(m, home_goals=3, away_goals=2), (.75, .5))]
    metrics = evaluate(predictions)
    assert metrics["over_2_5"]["brier"] == .0625
    assert metrics["btts_yes"]["brier"] == .25
    assert metrics["over_2_5"]["calibration_bias"] == 0
    assert metrics["over_2_5"]["ece_10_equal_width"] == .25
    assert sum(b["n"] for b in metrics["over_2_5"]["calibration_bins"]) == 2
    interval = paired_block_interval(predictions, predictions, 0, samples=10)
    assert interval["delta_brier"] == interval["lower_95"] == interval["upper_95"] == 0
    with pytest.raises(ValueError):
        paired_block_interval(predictions, predictions[::-1], 0, samples=10)


def test_goal_csv_joins_existing_completion_cohort_and_rejects_duplicates(tmp_path):
    p = tmp_path/"E1_1718.csv"
    p.write_text("Div,Date,HomeTeam,AwayTeam,HC,AC,FTHG,FTAG\n"
                 "E1,01/08/2017,A,B,5,4,2,1\n"
                 "E1,02/08/2017,C,D,,,0,1\n")
    matches, quality = load_goals([p])
    assert len(matches) == 1
    assert matches[0].outcomes == (1, 1)
    assert quality["rows_read"] == 2 and quality["excluded_source_rows"] == 1
    with pytest.raises(ValueError, match="duplicate"):
        load_goals([p, p])
    p.write_text("Div,Date,HomeTeam,AwayTeam,HC,AC,FTHG,FTAG\nE1,01/08/2017,A,B,5,4,-1,1\n")
    with pytest.raises(ValueError, match="invalid goal"):
        load_goals([p])


def test_source_season_preserves_covid_delayed_july_fixtures(tmp_path):
    p = tmp_path/"E1_1920.csv"
    p.write_text("Div,Date,HomeTeam,AwayTeam,HC,AC,FTHG,FTAG\n"
                 "E1,22/07/2020,A,B,5,4,2,1\n")
    matches, _ = load_goals([p])
    assert matches[0].season == "1920"


def test_corner_counts_are_not_goal_model_features():
    matches = history()
    before = compare_models(matches, evaluation_start=date(2017, 1, 1))
    changed = [replace(m, match=replace(m.match, home_corners=30, away_corners=25)) for m in matches]
    after = compare_models(changed, evaluation_start=date(2017, 1, 1))
    assert {n:[p.probabilities for p in v] for n,v in before.items()} == {
        n:[p.probabilities for p in v] for n,v in after.items()}


@pytest.mark.parametrize("invalid", ["empty", "league", "duplicate"])
def test_invalid_history(invalid):
    values = history()
    if invalid == "empty":
        values = []
    elif invalid == "league":
        values[0] = replace(values[0], match=replace(values[0].match, competition="E0"))
    else:
        values.append(values[0])
    with pytest.raises(ValueError):
        compare_models(values)
