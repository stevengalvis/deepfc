from datetime import date
import numpy as np
import pytest
from experiments.market_strength_diagnostic import band,strength_bin,bootstrap,ci,observation,standardized
from experiments.weakness_diagnostic import intervals
from experiments.market_strength import adjust
from tests.test_market_strength import prediction


def test_diagnostic_boundaries():
    assert [band(x) for x in [3.99,4,5.99,6]]==['lt4','4to6','4to6','ge6']
    assert [strength_bin(x) for x in [-.251,-.25,0,.25]]==['strong_underdog','mild_underdog','mild_favourite','strong_favourite']


def test_bootstrap_matches_existing_blocks_with_unequal_sizes():
    days=[date(2024,1,1),date(2024,1,1),date(2024,2,1),date(2024,3,1)]
    rows=[{'date':str(d),'x':float(i),'y':float(i*i)} for i,d in enumerate(days)]
    draws,n=bootstrap(rows,['x','y'])
    expected=intervals([(d,[r['x'],r['y']]) for d,r in zip(days,rows)])
    assert n==3
    assert np.array([ci(draws[:,0]),ci(draws[:,1])])==pytest.approx(np.array(expected))


def test_pairing_sign_and_convexity_identity():
    from dataclasses import replace
    from deepfc.corner_distribution import negative_binomial_over_probability
    from deepfc.team_corners import TEAM_CORNER_LINES
    b=prediction(date(2024,1,1),actual=7)
    b=replace(b,over_probabilities={l:negative_binomial_over_probability(5,l,b.dispersion) for l in TEAM_CORNER_LINES})
    a=adjust(b,.3,.2);r=observation(b,a,.3,2023,.2)
    assert r['bias_delta']==pytest.approx(-r['mean_shift'])
    assert r['mean_shift']==pytest.approx(r['linear_shift']+r['convexity_shift'])
    assert r['convexity_shift']>=0
    assert r['low_tail_observed']==0 and r['high_tail_observed']==0
    with pytest.raises(AssertionError):observation(b,replace(a,actual_corners=8),.3,2023,.2)


def test_standardization_removes_pure_composition_shift():
    rows=[]
    for bandname in ['lt4','4to6','ge6']:
        for year in [2023,2024,2025]:
            for v,value,n in [('home',1,year-2022),('away',-1,1)]:
                rows.extend([dict(band=bandname,season=year,venue=v,strength_bin='mild_favourite',baseline_bias=value,candidate_bias=value,mean_shift=0,strength=.1,brier_delta=0)]*n)
    result=standardized(rows)
    assert result['lt4']['seasons']['2023']['baseline_bias']==pytest.approx(result['lt4']['seasons']['2025']['baseline_bias'])
