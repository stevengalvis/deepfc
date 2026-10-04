"""One new market, frozen plain rates: each team's goals over1.5."""
import argparse
from itertools import groupby
import json
import math
from pathlib import Path
import numpy as np
from scipy.stats import poisson
from experiments import goals_plain_poisson as old

OUT=Path('experiments/results/team_goals_over15')


def save(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2,allow_nan=False)


def probabilities(means):
    assert len(means)==2 and all(math.isfinite(m) and m>=0 for m in means)
    p=poisson.sf(1,np.array(means)).tolist()
    assert all(math.isfinite(v) and 0<=v<=1 for v in p)
    return p


def prepare_rows(matches,league,reference):
    refs={(r['date'],r['home'],r['away']):r for r in reference};assert len(refs)==len(reference)
    history=[];counts=np.zeros(2,dtype=int);rows=[];excluded=[]
    for day,group in groupby(matches,key=lambda m:m.match_date):
        today=list(group)
        if old.START<=day<old.END:
            for m in today:
                key=(str(day),m.home_team,m.away_team)
                nh=sum(h.home_team==m.home_team for h in history);na=sum(h.away_team==m.away_team for h in history)
                if len(history)<100 or min(nh,na)<5:
                    assert key not in refs
                    excluded.append(dict(league=league,date=str(day),home=m.home_team,away=m.away_team,history_n=len(history),home_venue_n=nh,away_venue_n=na));continue
                r=refs[key];assert (len(history),nh,na)==(r['history_n'],r['home_venue_n'],r['away_venue_n'])
                assert all(h.match_date<day for h in history)
                # Verify pinned estimator reuse without selecting or fitting another model.
                assert list(old.estimate_expected_goals(history,m.home_team,m.away_team,5.))==r['means']
                rows.append(dict(league=league,date=str(day),home=m.home_team,away=m.away_team,
                    means=r['means'],history_n=len(history),home_venue_n=nh,away_venue_n=na,
                    poisson=probabilities(r['means']),baseline=((counts+1)/(len(history)+2)).tolist(),
                    outcomes=[int(m.home_goals>=2),int(m.away_goals>=2)]))
        for m in today:counts += [int(m.home_goals>=2),int(m.away_goals>=2)]
        history.extend(today)
    assert [(r['date'],r['home'],r['away']) for r in rows]==[(r['date'],r['home'],r['away']) for r in reference]
    return rows,excluded


def verify():
    f=json.loads((OUT/'FREEZE.json').read_text());assert all(old.digest(p)==h for p,h in f['hashes'].items())
    a=json.loads((OUT/'REVIEW_APPROVAL.json').read_text());assert a['approved'] and a['freeze_sha256']==old.digest(OUT/'FREEZE.json')
    return f


def prepare():
    f=verify();refs=json.loads((old.OUT/'predictions.json').read_text());audit=json.loads((old.OUT/'audit.json').read_text());rows=[]
    for league,paths in f['sources'].items():
        matches,q=old.load(paths,league);r,ex=prepare_rows(matches,league,[v for v in refs if v['league']==league])
        assert ex==audit[league]['excluded'] and q==audit[league]['quarantine']
        rows.extend(r);print(league,len(r),'eligible',len(ex),'excluded',flush=True)
    save('predictions.json',rows)
    save('PREDICTION_FREEZE.json',dict(predictions_sha256=old.digest(OUT/'predictions.json'),freeze_sha256=old.digest(OUT/'FREEZE.json')))


def summarize(rows):
    y=np.array([r['outcomes'] for r in rows]);output={'n_fixtures':len(rows),'n_events':2*len(rows),'models':{}}
    for name in ['baseline','poisson']:
        p=np.array([r[name] for r in rows]);venues={}
        for j,venue in enumerate(['home','away']):
            losses=[old.binary_logloss(a,b) for a,b in zip(p[:,j],y[:,j])];bins=[]
            for k in range(5):
                ix=np.minimum((p[:,j]*5).astype(int),4)==k
                bins.append(dict(bin=k,n=int(sum(ix)),predicted=float(np.mean(p[ix,j])) if ix.any() else None,observed=float(np.mean(y[ix,j])) if ix.any() else None))
            venues[venue]=dict(n=len(rows),events=int(sum(y[:,j])),brier=float(np.mean((p[:,j]-y[:,j])**2)),
                logloss=float(np.mean(losses)) if all(math.isfinite(v) for v in losses) else 'Infinity',
                impossible_events=sum(not math.isfinite(v) for v in losses),mean_probability=float(p[:,j].mean()),
                event_rate=float(y[:,j].mean()),calibration_gap=float(np.mean(p[:,j]-y[:,j])),bins=bins)
        output['models'][name]=dict(primary_brier=float(np.mean((p-y)**2)),venues=venues)
    d=(np.array([r['poisson'] for r in rows])-y)**2-(np.array([r['baseline'] for r in rows])-y)**2
    output['paired_brier']=old.intervals(rows,np.column_stack([d.mean(axis=1),d]))
    output['paired_brier']['order']=['equal_venue_primary','home','away']
    b=output['models']['baseline']['primary_brier'];p=output['models']['poisson']['primary_brier']
    output['relative_brier_improvement']=(b-p)/b
    return output


def score():
    verify();f=json.loads((OUT/'PREDICTION_FREEZE.json').read_text());assert f['freeze_sha256']==old.digest(OUT/'FREEZE.json') and f['predictions_sha256']==old.digest(OUT/'predictions.json')
    rows=json.loads((OUT/'predictions.json').read_text());results={}
    for league in ['E0','E1']:
        rs=[r for r in rows if r['league']==league]
        results[league]=dict(role='primary' if league=='E0' else 'secondary',all=summarize(rs),seasons={str(y):summarize([r for r in rs if f'{y}-07-01'<=r['date']<f'{y+1}-07-01']) for y in [2023,2024,2025]})
    save('results.json',results);print(json.dumps({k:v['all']['paired_brier'] for k,v in results.items()},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','score']);prepare() if p.parse_args().phase=='prepare' else score()
