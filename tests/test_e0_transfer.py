from dataclasses import replace
import pytest
from tests.test_time_decay_experiment import match_history
from experiments.time_decay import compare_models
from experiments.e0_transfer import transform

def test_explicit_e0_baseline_matches_unchanged_e1_arithmetic():
    history=match_history();a=compare_models(history).time_weighted
    e0=[replace(m,competition='E0') for m in history];b=compare_models(e0,competition='E0').time_weighted
    assert len(a)==len(b)>0
    for x,y in zip(a,b):
        assert x.expected_corners==y.expected_corners and x.dispersion==y.dispersion
        assert x.over_probabilities==y.over_probabilities and y.match.competition=='E0'
    with pytest.raises(ValueError):compare_models(e0)
    with pytest.raises(ValueError):compare_models(e0+[history[0]],competition='E0')

def test_transfer_formula_and_same_date_history_isolation():
    history=[replace(m,competition='E0') for m in match_history()]
    before=compare_models(history,competition='E0').time_weighted
    altered=history[:-1]+[replace(history[-1],home_corners=100,away_corners=100)]
    after=compare_models(altered,competition='E0').time_weighted
    assert [p.expected_corners for p in before]==[p.expected_corners for p in after]
    p=before[-1];c={'a_home':0.,'a_away':0.,'gamma':1.,'beta':.1}
    q=transform(p,.3,c)
    import math
    assert q.expected_corners==pytest.approx(p.expected_corners*math.exp(.03))
    assert q.dispersion==p.dispersion and q.actual_corners==p.actual_corners
