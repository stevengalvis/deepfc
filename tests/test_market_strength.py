from datetime import date
from dataclasses import replace
from types import SimpleNamespace
import numpy as np
import pytest
from experiments.market_strength import strength,objective,fit_beta,adjust,load_features
from deepfc.match_data import Match
from deepfc.team_corners import TeamCornerPrediction


def prediction(day=date(2022,1,1),actual=5,venue='home'):
    m=Match(day,'E1','A','B',actual,actual)
    return TeamCornerPrediction(m,'A' if venue=='home' else 'B',venue,5.,actual,{},.15)


def test_normalization_draw_and_sign():
    assert strength({'AvgH':'2','AvgD':'4','AvgA':'4'})==pytest.approx(.25)
    assert strength({'AvgH':'4','AvgD':'4','AvgA':'2'})==pytest.approx(-.25)
    assert strength({'AvgH':'3','AvgD':'2','AvgA':'3'})==0


@pytest.mark.parametrize('bad',['0','1','-2','nan','inf',''])
def test_invalid_quote_not_replaced_by_closing(bad):
    with pytest.raises(ValueError):strength({'AvgH':bad,'AvgD':'3','AvgA':'4','AvgCH':'2'})


def test_gradient_curvature_independent_likelihood():
    from deepfc.corner_distribution import negative_binomial_negative_log_loss
    mu=np.array([3.,5.,7.]);y=np.array([2.,4.,9.]);a=np.array([0.,.15,.2]);s=np.array([-.4,.2,.4]);b=.3;eps=1e-5
    f,g,h=objective(b,mu,y,a,s)
    assert g==pytest.approx((objective(b+eps,mu,y,a,s)[0]-objective(b-eps,mu,y,a,s)[0])/(2*eps),abs=1e-8)
    assert h==pytest.approx((objective(b+eps,mu,y,a,s)[1]-objective(b-eps,mu,y,a,s)[1])/(2*eps),abs=1e-8)
    direct=lambda z:sum(negative_binomial_negative_log_loss(int(v),float(m*np.exp(z*t)),float(d)) for m,v,d,t in zip(mu,y,a,s))+.5*z*z
    assert objective(b,mu,y,a,s)[0]-objective(0,mu,y,a,s)[0]==pytest.approx(direct(b)-direct(0),abs=1e-10)


def test_future_outcomes_cannot_change_coefficient():
    p=prediction(actual=7);f=prediction(date(2025,1,1),actual=100)
    features={(p.match.match_date,'A','B'):.4,(f.match.match_date,'A','B'):.9}
    b,c=fit_beta([p],features);other,_=fit_beta([p,f],features)
    assert b==other and c['latest_training_date']=='2022-01-01'
    assert abs(c['score'])<=1e-8 and c['curvature']>0


def test_neutral_fit_and_inference_guard():
    p=prediction();b,_=fit_beta([p],{(p.match.match_date,'A','B'):.3})
    assert b==pytest.approx(0,abs=1e-12)
    with pytest.raises(ValueError,match='earlier'):adjust(p,.3,b)
    later=prediction(date(2024,1,1));home=adjust(later,.3,.2);away=adjust(replace(later,venue='away'),.3,.2)
    assert home.expected_corners*away.expected_corners==pytest.approx(25)
    assert home.dispersion==later.dispersion and home.actual_corners==later.actual_corners


def test_loader_ignores_old_schema_and_excludes_invalid(tmp_path):
    old=tmp_path/'E1_1819.csv';old.write_text('irrelevant')
    new=tmp_path/'E1_1920.csv';new.write_text('Div,Date,HomeTeam,AwayTeam,AvgH,AvgD,AvgA,AvgCH\nE1,01/08/2019,A,B,0,3,4,2\nE1,02/08/2019,C,D,2,4,4,1.5\n')
    features,bad=load_features([old,new]);assert len(features)==1 and len(bad)==1
