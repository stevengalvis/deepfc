from datetime import date,timedelta
from types import SimpleNamespace
import numpy as np
import pytest
from scipy.optimize._numdiff import approx_derivative
from deepfc.match_data import Match
from experiments.joint_strength import design,objective,fit,Fit,generate,gates
from experiments.time_decay import compare_models


def history():
    return [Match(date(2018,1,1)+timedelta(days=i),'E1','A' if i%2 else 'B','B' if i%2 else 'A',3+i%4,2+i%3) for i in range(60)]


@pytest.mark.parametrize('alpha',[0,.15])
def test_analytic_gradient_and_centering(alpha):
    teams,arrays=design(history(),date(2018,7,1))
    theta=np.linspace(-.1,.3,2+4*len(teams));theta[:2]=[1.5,1.2]
    val,grad=objective(theta,arrays,alpha)
    numeric=approx_derivative(lambda x:objective(x,arrays,alpha)[0],theta).ravel()
    assert np.allclose(grad,numeric,atol=1e-6)
    shifted=theta.copy();shifted[2:]+=10
    assert objective(shifted,arrays,alpha)[0]==pytest.approx(val)
    assert np.allclose(grad[2:].reshape(4,-1).sum(axis=1),0,atol=1e-10)


def test_objective_matches_nb_likelihood_up_to_constants():
    from deepfc.corner_distribution import negative_binomial_negative_log_loss
    _,arrays=design(history(),date(2018,7,1));y,w,v,a,d=arrays
    t=np.zeros(10);t[:2]=[1.5,1.2];u=t.copy();u[2]=.2
    def exact(theta):
        e=theta[2:].reshape(4,-1);e=e-e.mean(axis=1,keepdims=True)
        eta=theta[v]+e.ravel()[a]+e.ravel()[d]
        return sum(weight*negative_binomial_negative_log_loss(int(count),float(np.exp(pred)),.15) for count,weight,pred in zip(y,w,eta))+.5*np.sum(e**2)
    assert objective(u,arrays,.15)[0]-objective(t,arrays,.15)[0]==pytest.approx(exact(u)-exact(t),abs=1e-9)


@pytest.mark.parametrize('offset',[0,-1])
def test_rejects_same_or_future_history(offset):
    h=history()
    with pytest.raises(ValueError,match='strictly precede'):fit(h,h[-1].match_date+timedelta(days=offset),.15)


def test_fit_identifiability_and_unseen_effects():
    model=fit(history(),date(2018,7,1),.15)
    assert np.allclose(model.effects.sum(axis=1),0,atol=1e-12)
    assert model.diagnostics['gradient_max']<=1e-4
    assert model.predict('new','other','home')==pytest.approx(np.exp(model.intercept[0]))
    reversed_fit=fit(list(reversed(history())),date(2018,7,1),.15)
    assert model.predict('A','B','home')==pytest.approx(reversed_fit.predict('A','B','home'),rel=1e-5)


def test_failure_is_not_silently_substituted(monkeypatch):
    import experiments.joint_strength as joint
    def failed(*args):raise RuntimeError('forced failure')
    monkeypatch.setattr(joint,'solve_newton',failed)
    with pytest.raises(RuntimeError,match='forced failure'):fit(history(),date(2018,7,1),.15)


def test_same_day_and_future_outcomes_leave_forecasts_unchanged():
    h=history();m=Match(date(2018,7,1),'E1','A','B',4,3)
    original=h+[m];b=compare_models(original).time_weighted
    p,logs=generate(original,b)
    changed=h+[Match(m.match_date,'E1','A','B',40,30),Match(date(2018,7,2),'E1','A','B',50,60)]
    q,_=generate(changed,compare_models(changed).time_weighted)
    assert len(logs)==1 and len(p)==2
    assert [x.expected_corners for x in p]==pytest.approx([x.expected_corners for x in q[:2]])
    assert [(x.venue,x.dispersion) for x in b]==[(x.venue,x.dispersion) for x in p]


def test_reduced_hessian_matches_gradient_derivative(monkeypatch):
    import experiments.joint_strength as joint
    original=joint.solve_newton
    def checked(fun,hess,difference,x):
        analytic=hess(x)
        numeric=approx_derivative(lambda z:fun(z)[1],x)
        assert np.allclose(analytic,numeric,atol=1e-6)
        assert np.all(np.linalg.eigvalsh(analytic)>0)
        perturb=np.linspace(-.001,.001,len(x))
        assert difference(x,perturb)==pytest.approx(fun(x+perturb)[0]-fun(x)[0],abs=1e-10)
        return original(fun,hess,difference,x)
    monkeypatch.setattr(joint,'solve_newton',checked)
    fit(history(),date(2018,7,1),.15)


def test_deterministic_balanced_recovery():
    h=[Match(date(2018,1,1)+timedelta(days=i),'E1','A' if i%2 else 'B','B' if i%2 else 'A',6,4) for i in range(60)]
    m=fit(h,date(2018,7,1),.15)
    assert np.max(np.abs(m.effects))<1e-8
    assert m.predict('A','B','home')==pytest.approx(6,abs=1e-8)
    assert m.predict('B','A','away')==pytest.approx(4,abs=1e-8)
    assert m.diagnostics['independent_gradient_max']<1e-8
