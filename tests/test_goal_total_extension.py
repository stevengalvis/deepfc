from dataclasses import replace
from datetime import date
import numpy as np
import pytest
from deepfc.corner_distribution import negative_binomial_negative_log_loss
from experiments.goal_total_extension import goal_probability, objective, fit, feature_key, extended_design, metrics
from experiments.joint_market_calibration import objective as original_objective
from tests.test_market_strength import prediction


def test_goal_probability_normalizes_and_ignores_closing_quotes():
    row={'Avg>2.5':'2', 'Avg<2.5':'3', 'AvgC>2.5':'1.1', 'AvgC<2.5':'100'}
    assert goal_probability(row)==pytest.approx(.6)
    assert goal_probability({'Avg>2.5':'2','Avg<2.5':'2'})==.5
    with pytest.raises(KeyError):goal_probability({'AvgC>2.5':2,'AvgC<2.5':2})


@pytest.mark.parametrize('bad',['',None,'NaN','inf','1','0','-2'])
def test_invalid_pair_never_falls_back(bad):
    with pytest.raises((ValueError,TypeError)):
        goal_probability({'Avg>2.5':bad,'Avg<2.5':2,'B365>2.5':2,'AvgC>2.5':2})


def test_feature_shared_across_venues_and_centered():
    p=prediction(date(2020,1,1))
    h=extended_design(p,(.6,.2));a=extended_design(replace(p,venue='away'),(.6,.2))
    assert h[-1]==a[-1]==pytest.approx(.1)
    assert h[-2]==-a[-2]


def test_nb_gradient_hessian_and_nested_objective():
    rng=np.random.default_rng(4);X=rng.normal(size=(10,5));mu=np.full(10,5.);y=np.arange(10);alpha=np.array([0,.1]*5);t=np.arange(5)*.02
    loss,g,H=objective(t,X,mu,y,alpha)
    eps=1e-5
    for j in range(5):
        step=np.eye(5)[j]*eps
        assert g[j]==pytest.approx((objective(t+step,X,mu,y,alpha)[0]-objective(t-step,X,mu,y,alpha)[0])/(2*eps),abs=1e-7)
        assert H[:,j]==pytest.approx((objective(t+step,X,mu,y,alpha)[1]-objective(t-step,X,mu,y,alpha)[1])/(2*eps),abs=1e-7)
    delta=np.ones(5)*.01
    exact=lambda t:sum(negative_binomial_negative_log_loss(int(v),float(m),float(a)) for v,m,a in zip(y,mu*np.exp(X@t),alpha))+.5*t@t
    assert objective(t+delta,X,mu,y,alpha)[0]-loss==pytest.approx(exact(t+delta)-exact(t),abs=1e-10)
    t[-1]=0
    assert objective(t,X,mu,y,alpha)[0]==pytest.approx(original_objective(t[:4],X[:,:4],mu,y,alpha)[0])


def test_fit_excludes_future_and_epl_and_does_not_change_center():
    p=prediction(date(2020,1,1),actual=7);future=prediction(date(2022,1,1),actual=100)
    epl=replace(p,match=replace(p.match,competition='E0'))
    quotes={feature_key(x):(.6,.2) for x in [p,future,epl]}
    theta,cert=fit([p,future,epl],quotes,date(2021,7,1))
    other,_=fit([p,replace(future,actual_corners=0),replace(epl,actual_corners=0)],quotes,date(2021,7,1))
    assert np.array_equal(theta,other) and cert['training_n']==1 and cert['latest_training_date']=='2020-01-01'
    with pytest.raises(ValueError):fit([future,epl],quotes,date(2021,7,1))


def test_identical_means_give_zero_deltas():
    row=dict(date='2024-01-01',home='A',away='B',baseline_mean=5.,joint_mean=5.,dispersion=.1,actual=4)
    out=metrics(row,5.)
    assert all(v==0 for k,v in out.items() if k.startswith('goal_minus_'))
    assert 0 <= out['goal_low_tail_probability'] <= 1
    assert 0 <= out['goal_high_tail_probability'] <= 1
