import math
from dataclasses import replace
from datetime import date
import numpy as np
import pytest
from experiments.distribution_blend import mix_nll,choose_weight,row_metrics,prior_fit
from deepfc.corner_distribution import negative_binomial_negative_log_loss as nll
from tests.test_market_strength import prediction
from experiments.market_strength import key

def test_mixture_normalized_endpoints_and_probability_coherence():
    for w in [0,.3,1]:
        masses=[math.exp(-mix_nll(y,3.,7.,.15,w)) for y in range(200)]
        assert sum(masses)==pytest.approx(1,abs=1e-12)
        r=dict(date='2024-01-01',home='A',away='B',baseline_mean=3.,component_mean=7.,dispersion=.15,actual=5)
        out=row_metrics(r,w)
        for l in [3.5,4.5,5.5,6.5]:assert out['blend_'+str(l)+'_probability']==pytest.approx(sum(masses[int(l)+1:]),abs=1e-12)
        assert out['blend_mean']==pytest.approx(sum(i*p for i,p in enumerate(masses)))
    assert mix_nll(5,3,7,.15,0)==nll(5,3,.15)
    assert mix_nll(5,3,7,.15,1)==nll(5,7,.15)

def test_analytic_weight_endpoints_and_degenerate_tie():
    b=np.array([.2,.8]);c=np.array([.8,.2])
    assert choose_weight(b,c,b)==0 and choose_weight(b,c,c)==1
    assert choose_weight(b,c,(b+c)/2)==pytest.approx(.5)
    assert choose_weight(b,b,c)==0

def test_fold_fit_excludes_heldout_and_future_outcomes():
    p=prediction(date(2020,1,1),actual=7);q=prediction(date(2022,1,1),actual=100)
    features={key(p.match):.2,key(q.match):.3}
    t,c=prior_fit([p,q],features,date(2021,7,1));u,_=prior_fit([p,replace(q,actual_corners=0)],features,date(2021,7,1))
    assert np.array_equal(t,u) and c['latest_training_date']=='2020-01-01'
