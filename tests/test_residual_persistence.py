from datetime import date,timedelta
import numpy as np
from experiments.residual_persistence import past_features, regression


def fixtures(n=23):
    rows=[]
    for i in range(n):
        when=str(date(2024,1,1)+timedelta(days=3*i))
        for venue,team,opponent in [('home','A','B'),('away','B','A')]:
            rows.append(dict(league='E1',season=2023,date=when,home='A',away='B',venue=venue,team=team,opponent=opponent,
                             actual=i,baseline_mean=5.,joint_mean=4.,strength=.1,goal_probability=.5))
    return rows


def test_features_use_exact_past_windows_and_concession_direction():
    rows=fixtures();out,rejected=past_features(rows)
    assert len(out)==6 and sum(rejected.values())==40
    first=out[0]
    assert first['baseline_attack_recent']==12 # actual 15..19 minus 5
    assert first['baseline_attack_older']==2 # actual 0..14 minus 5
    assert first['baseline_attack_change']==10
    assert first['baseline_concession_recent']==12
    assert first['joint_attack_recent']==13
    assert first['attack_latest_date']<first['date']
    changed=[dict(r,actual=1000) if r['date']>=first['date'] else r for r in rows]
    again,_=past_features(changed)
    for k,v in first.items():
        if any(x in k for x in ['attack_','concession_']):assert again[0][k]==v


def test_same_date_batch_and_season_reset_and_history_span():
    rows=fixtures(20);same=[dict(rows[-2],actual=99),dict(rows[-1],actual=99)]
    out,_=past_features(rows+same)
    assert out==[] # same-date outcomes cannot supply twentieth past record
    rows=fixtures(21)
    for r in rows[-2:]:r['season']=2024
    assert past_features(rows)[0]==[]
    rows=fixtures(21)
    for r in rows[-2:]:r['date']='2025-01-01'
    assert past_features(rows)[0]==[]


def test_constant_model_bias_cancels_in_change():
    rows=fixtures();a,_=past_features(rows)
    b,_=past_features([dict(r,baseline_mean=r['baseline_mean']+7) for r in rows])
    for x,y in zip(a,b):
        for c in ['attack','concession']:
            assert x['baseline_'+c+'_change']==y['baseline_'+c+'_change']


def test_regression_identifies_known_incremental_effect_and_small_n():
    rng=np.random.default_rng(7);rows=[]
    for i in range(800):
        a,c,old_a,old_c=rng.normal(size=4)
        r=dict(date=str(date(2021,1,1)+timedelta(days=i)),season=2021+i//365,venue='home' if i%2 else 'away',
               home='A'+str(i%20),away='B'+str(i%19),team='A'+str(i%20),opponent='B'+str(i%19),baseline_mean=5.,
               joint_mean=5.,actual=5+.4*a+.2*c+.7*old_a, strength=0.,goal_probability=.5)
        for ch,v,old in [('attack',a,old_a),('concession',c,old_c)]:
            r['joint_'+ch+'_change']=v;r['joint_'+ch+'_older']=old;r['joint_'+ch+'_recent']=v+old
            for p in ['recent','older']:r[ch+'_'+p+'_home_fraction']=.5
        rows.append(r)
    fit=regression(rows,'joint','controlled')
    assert abs(fit['attack_slope']-.4)<1e-10
    assert abs(fit['concession_slope']-.2)<1e-10
    assert fit['partial_r_squared_in_sample']>.999
    assert regression(rows[:100],'joint','controlled')['status']=='insufficient n'


def test_concession_history_uses_opponents_previous_scorers():
    rows=[]
    for i in range(20):
        template=dict(league='E1',season=2023,date=str(date(2024,1,1)+timedelta(days=i)),venue='home',baseline_mean=5.,joint_mean=4.,strength=.1,goal_probability=.5)
        rows.extend([dict(template,home='A',away='X',team='A',opponent='X',actual=i),
                     dict(template,home='Y',away='B',team='Y',opponent='B',actual=40+i)])
    rows.append(dict(template,date='2024-02-01',home='A',away='B',team='A',opponent='B',actual=2))
    out,_=past_features(rows)
    assert len(out)==1
    assert out[0]['baseline_attack_recent']==12
    assert out[0]['baseline_concession_recent']==52
