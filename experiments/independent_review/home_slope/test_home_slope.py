from datetime import date,timedelta
from dataclasses import replace
import numpy as np
import pytest
from home_slope import transform,distribution,scalar_objective,fit_delta,fit_joint_before,stopping_reason,support
from experiments.market_strength import key
from tests.test_market_strength import prediction
from experiments.time_decay import compare_models
from tests.test_time_decay_experiment import match_history

def test_null_recovery_means_probabilities_and_count_nll():
    mu=np.array([2.,5.,8.,4.]);h=np.array([True,True,False,False]);a=np.array([0.,.1,.2,.3]);y=np.array([1,5,8,4])
    got=transform(mu,h,0);assert np.array_equal(got,mu)
    p,nll=distribution(mu,a,y);q,other=distribution(got,a,y)
    assert np.array_equal(p,q) and np.array_equal(nll,other)

def test_away_unchanged_and_home_pivot_has_two_directions():
    mu=np.array([2.,5.,8.,2.,5.,8.]);h=np.array([True]*3+[False]*3)
    for d in [-.5,.2,.5]:
        got=transform(mu,h,d);assert np.array_equal(got[~h],mu[~h]);assert got[1]==5
    got=transform(mu,h,.2);assert got[0]<mu[0] and got[2]>mu[2]

def test_coherent_decreasing_lines_and_bounds():
    mu=np.geomspace(.1,30,100);h=np.ones(100,dtype=bool);alpha=np.linspace(0,.5,100)
    for d in [-.5,0,.5]:
        got=transform(mu,h,d);p,nll=distribution(got,alpha,np.arange(100)%20)
        assert np.all((p>=0)&(p<=1)) and np.all(np.diff(p,axis=1)<=0) and np.isfinite(nll).all()
        assert np.all(np.diff(got)>0)
    for d in [-.50001,.50001,float('nan')]:
        with pytest.raises(ValueError):transform(mu,h,d)

def test_scalar_derivatives_against_scipy_likelihood():
    mu=np.array([2.,4.,6.,9.]);y=np.array([0,3,8,12]);alpha=np.array([0.,.1,.2,.3]);d=.13;eps=1e-5
    f,g,H=scalar_objective(d,mu,y,alpha)
    def direct(t):
        _,nll=distribution(mu*np.exp(t*np.log(mu/5)),alpha,y)
        return nll.sum()+8*t*t
    assert g==pytest.approx((direct(d+eps)-direct(d-eps))/(2*eps),abs=1e-8)
    assert H==pytest.approx((scalar_objective(d+eps,mu,y,alpha)[1]-scalar_objective(d-eps,mu,y,alpha)[1])/(2*eps),abs=1e-8)
    assert H>=16

def test_fits_null_and_boundary_and_stops_before_later():
    mu=np.array([2.,4.,6.,8.]);a=np.full(4,.1)
    fit=fit_delta(mu,mu,a);assert abs(fit['delta'])<1e-12 and abs(fit['gradient'])<=1e-8
    fit=fit_delta(np.array([10.]*100),np.array([100.]*100),np.full(100,.1))
    assert fit['delta']==.5 and fit['boundary'] and fit['gradient']<=0
    assert stopping_reason(fit,{'passes':True})=='stop_boundary_optimum'
    assert stopping_reason({'delta':-.01,'boundary':False},{'passes':True})=='stop_nonpositive_delta'
    assert stopping_reason({'delta':.1,'boundary':False},{'passes':False})=='stop_insufficient_oof_support'
    assert stopping_reason({'delta':.1,'boundary':False},{'passes':True})=='eligible_for_frozen_later_evaluation'

def test_fit_cutoff_excludes_same_date_and_future_outcomes():
    cutoff=date(2020,7,1);p=prediction(date(2020,6,1),actual=7);q=replace(p,venue='away',actual_corners=3)
    same=prediction(cutoff,actual=100);future=prediction(date(2021,1,1),actual=100)
    features={key(z.match):.3 for z in [p,q,same,future]}
    t,c=fit_joint_before([p,q],features,cutoff);other,cc=fit_joint_before([p,q,same,future],features,cutoff)
    assert np.array_equal(t,other) and c['training_n']==cc['training_n']==2
    assert c['latest_training_date']<'2020-07-01'

def test_baseline_same_date_outcomes_do_not_change_forecasts():
    history=match_history();before=compare_models(history).time_weighted
    latest=history[-1].match_date
    changed=[replace(m,home_corners=100,away_corners=100) if m.match_date==latest else m for m in history]
    after=compare_models(changed).time_weighted
    assert [p.expected_corners for p in before]==[p.expected_corners for p in after]
    assert [p.dispersion for p in before]==[p.dispersion for p in after]

def test_support_counts_both_sides_and_blocks():
    rows=[{'venue':'home','joint_mean':4. if i%2 else 6.,'date':str(date(2020,1,1)+timedelta(days=i))} for i in range(600)]
    s=support(rows);assert s['passes'] and s['below5']['n']==300 and s['above5']['n']==300
    assert not support(rows[:150])['passes']

def test_scalar_fit_positive_interior_and_negative_interior():
    mu=np.tile([2.,4.,6.,8.],100);a=np.full(len(mu),.1)
    positive=fit_delta(mu,np.tile([2,4,6,9],100),a)
    negative=fit_delta(mu,np.tile([3,4,6,7],100),a)
    assert 0<positive['delta']<.5 and not positive['boundary']
    assert -.5<negative['delta']<0 and not negative['boundary']
    assert abs(positive['independent_gradient'])<1e-8 and abs(negative['independent_gradient'])<1e-8
