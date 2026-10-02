from datetime import date
import math
import numpy as np
import pytest
from deepfc.corner_distribution import negative_binomial_negative_log_loss as nll, poisson_over_probability
from experiments.conditional_dispersion import objective, fit, metrics, paired, logalpha_bounds, LOW, HIGH


def test_full_nb_likelihood_gradients_and_hessian():
    y=np.array([0,1,3,6,12]);mu=np.array([2.,3.,5.,7.,8.]);z=np.linspace(-.5,.5,5);t=np.array([-2.,.13])
    value,g,H=objective(t,y,mu,z)
    alpha=np.exp(t[0]+t[1]*z)
    expected=sum(nll(int(v),float(m),float(a)) for v,m,a in zip(y,mu,alpha))+.5*(t[1]/.25)**2
    assert value==pytest.approx(expected,abs=1e-11)
    for i in range(2):
        step=np.eye(2)[i]*1e-5
        assert g[i]==pytest.approx(float((objective(t+step,y,mu,z,derivatives=False)-objective(t-step,y,mu,z,derivatives=False))/(2e-5)),abs=1e-7)
        assert H[:,i]==pytest.approx((objective(t+step,y,mu,z)[1]-objective(t-step,y,mu,z)[1])/(2e-5),abs=1e-7)
    assert objective([t[0],0],y,mu,z)[0]==objective([t[0]],y,mu,z,False)[0]


def test_distribution_normalization_mean_and_near_poisson():
    for alpha in [1e-4,.1,1.]:
        masses=[math.exp(-nll(y,5.,alpha)) for y in range(400)]
        assert sum(masses)==pytest.approx(1.,abs=1e-10)
        assert sum(i*p for i,p in enumerate(masses))==pytest.approx(5.,abs=1e-9)
        if alpha==1e-4:
            assert sum(masses[5:])==pytest.approx(poisson_over_probability(5.,4.5),abs=1e-4)
        y=np.arange(20);mu=np.full(20,5.);z=np.zeros(20)
        assert objective([math.log(alpha)],y,mu,z,False)[0]==pytest.approx(sum(nll(int(v),5.,alpha) for v in y),abs=1e-8)


def synthetic_rows():
    rng=np.random.default_rng(14)
    return [dict(league='E1',season=2021,date='2022-01-01',actual=int(y),mean=5.,z=float(z)) for y,z in zip(rng.negative_binomial(8,8/13,size=1200),rng.uniform(-.5,.5,1200))]


def test_fit_convergence_bounds_and_training_chronology():
    rows=synthetic_rows();base=fit(rows,date(2022,7,1))
    changed=rows+[dict(rows[0],date='2023-01-01',season=2022,actual=1000),dict(rows[0],league='E0',actual=1000)]
    other=fit(changed,date(2022,7,1))
    assert base['B']==other['B'] and base['C']==other['C']
    assert base['training_n']==1200 and base['B_certificate']['certified']
    assert all(c['certified'] for c in base['C_start_certificates'])
    assert min(logalpha_bounds(base['C']))>LOW and max(logalpha_bounds(base['C']))<HIGH
    assert base['objective_spread_per_observation']<=1e-8


def test_metrics_preserve_mean_mae_bias_and_valid_ordered_probabilities():
    r=dict(league='E1',date='2024-01-01',home='A',away='B',venue='home',season=2023,actual=7,mean=5.,current_alpha=.1,baseline_mean=6.,z=.2)
    out=metrics(r,{'B':[-2.,0.],'C':[-2.,.1]})
    for metric in ['mean','mae','bias','squared_error']:
        assert out['A_'+metric]==out['B_'+metric]==out['C_'+metric]
    for arm in ['A','B','C']:
        probabilities=[out[arm+'_'+str(l)+'_probability'] for l in [3.5,4.5,5.5,6.5]]
        assert 1>=probabilities[0]>=probabilities[1]>=probabilities[2]>=probabilities[3]>=0
    paired([r,dict(r,venue='away')])
    with pytest.raises(ValueError):paired([r])
    with pytest.raises(ValueError):paired([r,r])


def test_paired_calibration_bootstrap_identity():
    from experiments.conditional_dispersion import summarize
    rows=[]
    for d,y in [('2024-01-01',0),('2024-03-01',10)]:
        for venue in ['home','away']:
            r=dict(league='E1',date=d,home='A',away='B',venue=venue,season=2023,actual=y,mean=5.,current_alpha=.1,baseline_mean=5.,z=.1)
            rows.append(metrics(r,{'B':[math.log(.1),0.],'C':[math.log(.1),0.]}))
    out=summarize(rows)
    assert out['n_fixtures']==2
    for value in out['absolute_calibration_error_changes'].values():
        assert abs(value['point'])<1e-14
        assert max(abs(v) for v in value['ci95'])<1e-14
