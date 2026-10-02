from datetime import date
from dataclasses import replace
import numpy as np
import pytest
from experiments.joint_market_calibration import objective,fit,predict,design
from experiments.market_strength import key
from tests.test_market_strength import prediction
from deepfc.corner_distribution import negative_binomial_negative_log_loss

def test_objective_derivatives_against_independent_nb():
    X=np.array([[1,0,-.3,-.4],[0,1,.2,.3],[1,0,.4,.1],[0,1,-.1,-.2]])
    mu=np.array([3.,6.,7.,4.]);y=np.array([2,8,5,3]);a=np.array([0.,.1,.2,.15]);t=np.array([.02,-.03,-.1,.2]);e=1e-5
    f,g,h=objective(t,X,mu,y,a)
    direct=lambda v:sum(negative_binomial_negative_log_loss(int(z),float(m),float(alpha)) for z,m,alpha in zip(y,mu*np.exp(X@v),a))+.5*v@v
    for j in range(4):
        step=np.eye(4)[j]*e
        assert g[j]==pytest.approx((direct(t+step)-direct(t-step))/(2*e),abs=1e-8)
        assert h[:,j]==pytest.approx((objective(t+step,X,mu,y,a)[1]-objective(t-step,X,mu,y,a)[1])/(2*e),abs=1e-8)
    assert np.linalg.eigvalsh(h).min()>=1

def test_fit_excludes_future_and_prediction_guard():
    p=prediction(actual=7);q=replace(prediction(actual=3),venue='away');future=prediction(date(2025,1,1),actual=100)
    features={key(p.match):.3,key(q.match):.3,key(future.match):.8}
    t,c=fit([p,q],features);other,_=fit([p,q,future],features)
    assert t==pytest.approx(other,abs=0)
    assert c['independent_gradient_max']<=1e-8 and c['training_n']==2
    with pytest.raises(ValueError):predict(p,.3,t)
    z=predict(future,.8,np.zeros(4));assert z.expected_corners==future.expected_corners
    assert z.dispersion==future.dispersion and z.actual_corners==future.actual_corners

def test_joint_design_venue_and_strength_sign_are_explicit():
    p=prediction();assert design(p,.3)==pytest.approx([1,0,0,.3])
    assert design(replace(p,venue='away'),-.3)==pytest.approx([0,1,0,-.3])
