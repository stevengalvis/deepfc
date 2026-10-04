"""Bounded private goals evaluation. Separate prepare and score phases."""
import argparse
import csv
from dataclasses import dataclass
from datetime import date, datetime
import hashlib
from itertools import groupby
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import poisson
from experiments.vendor_modelfc_goal_estimator import estimate_expected_goals

OUT = Path('experiments/results/goals_plain_poisson')
START = date(2023, 7, 1)
END = date(2026, 7, 1)
AWARD = ('E1', date(2019, 4, 27), 'Bolton', 'Brentford')


@dataclass(frozen=True)
class Match:
    match_date: date
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (OUT/name).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def parse_date(text):
    if len(text) not in (8, 10):
        raise ValueError('unsupported date')
    return datetime.strptime(text, '%d/%m/%y' if len(text)==8 else '%d/%m/%Y').date()


def load(paths, league):
    matches, quarantine, seen = [], [], set()
    for path in paths:
        with Path(path).open(encoding='utf-8-sig', newline='') as stream:
            for row in csv.DictReader(stream):
                assert None not in row and all(v is not None for v in row.values())
                assert row['Div'] == league
                d = parse_date(row['Date'])
                h, a = row['HomeTeam'].strip(), row['AwayTeam'].strip()
                identity = (league, d, h, a)
                assert h and a and h != a and identity not in seen
                seen.add(identity)
                if identity == AWARD:
                    quarantine.append([league, str(d), h, a])
                    continue
                # Missing both shot counts is an administrative/unplayed audit
                # flag for these specific source files, never silently accepted.
                assert row.get('HS', '').strip() and row.get('AS', '').strip(), identity
                assert row['FTHG'].isdigit() and row['FTAG'].isdigit()
                hg, ag = int(row['FTHG']), int(row['FTAG'])
                assert row['FTR'] == ('H' if hg>ag else 'A' if ag>hg else 'D')
                matches.append(Match(d,h,a,hg,ag))
    assert len(quarantine) == (1 if league=='E1' else 0)
    return sorted(matches, key=lambda m:(m.match_date,m.home_team,m.away_team)), quarantine


def probabilities(home, away):
    assert math.isfinite(home) and math.isfinite(away) and min(home,away)>=0
    total = home+away
    btts = (-math.expm1(-home))*(-math.expm1(-away))
    over = float(poisson.sf(2,total))
    settlement = [float(poisson.cdf(1,total)), float(poisson.pmf(2,total)), over]
    assert all(math.isfinite(p) and 0<=p<=1 for p in [btts,over]+settlement)
    assert abs(sum(settlement)-1)<1e-12
    return [btts,over], settlement


def forecast(matches, league):
    history, rows, excluded = [], [], []
    counts = np.zeros(2, dtype=int)
    for day, group in groupby(matches, key=lambda m:m.match_date):
        today = list(group)
        if START <= day < END:
            for m in today:
                nh = sum(p.home_team==m.home_team for p in history)
                na = sum(p.away_team==m.away_team for p in history)
                identity = dict(league=league,date=str(day),home=m.home_team,away=m.away_team)
                if len(history)<100 or min(nh,na)<5:
                    excluded.append(dict(**identity,history_n=len(history),home_venue_n=nh,away_venue_n=na))
                    continue
                assert all(p.match_date<day for p in history)
                means = estimate_expected_goals(history,m.home_team,m.away_team,5.)
                p, settlement = probabilities(*means)
                rows.append(dict(**identity,means=list(means),poisson=p,
                    baseline=((counts+1)/(len(history)+2)).tolist(),settlement=settlement,
                    outcomes=[int(m.home_goals>0 and m.away_goals>0),int(m.home_goals+m.away_goals>=3)],
                    settlement_outcome=0 if m.home_goals+m.away_goals<2 else 1 if m.home_goals+m.away_goals==2 else 2,
                    history_n=len(history),home_venue_n=nh,away_venue_n=na))
        for m in today:
            counts += [int(m.home_goals>0 and m.away_goals>0),int(m.home_goals+m.away_goals>=3)]
        history.extend(today)
    return rows, excluded


def verify():
    frozen=json.loads((OUT/'FREEZE.json').read_text())
    assert all(digest(p)==h for p,h in frozen['hashes'].items())
    approval=json.loads((OUT/'REVIEW_APPROVAL.json').read_text())
    assert approval['approved'] and approval['freeze_sha256']==digest(OUT/'FREEZE.json')
    return frozen


def prepare():
    frozen=verify(); allrows=[]; audit={}
    for league, paths in frozen['sources'].items():
        matches, quarantine=load(paths,league)
        rows,excluded=forecast(matches,league)
        expected=1656 if league=='E1' else 1140
        assert len(rows)+len(excluded)==expected
        audit[league]=dict(played_history_rows=len(matches),quarantine=quarantine,
            eligible=len(rows),excluded=excluded,raw_evaluation=expected)
        allrows.extend(rows)
    save('predictions.json',allrows)
    save('audit.json',audit)
    save('PREDICTION_FREEZE.json',dict(predictions_sha256=digest(OUT/'predictions.json'),
        audit_sha256=digest(OUT/'audit.json'),freeze_sha256=digest(OUT/'FREEZE.json')))
    print(json.dumps({k:{j:v for j,v in a.items() if j!='excluded'} for k,a in audit.items()}))


def binary_logloss(p,y):
    q=p if y else 1-p
    return -math.log(q) if q else math.inf


def intervals(rows, delta):
    groups={}
    for row,d in zip(rows,delta):
        b=date.fromisoformat(row['date']).toordinal()//28
        groups.setdefault(b,[]).append(d)
    blocks=[np.array(v) for _,v in sorted(groups.items())]
    sums=np.array([b.sum(axis=0) for b in blocks]); sizes=np.array([len(b) for b in blocks])
    weights=np.random.default_rng(20261003).multinomial(len(blocks),np.full(len(blocks),1/len(blocks)),size=10000)
    samples=(weights@sums)/(weights@sizes)[:,None]
    return dict(blocks=len(blocks),replicates=10000,seed=20261003,
                mean=np.mean(delta,axis=0).tolist(),ci95=np.quantile(samples,[.025,.975],axis=0).T.tolist())


def summarize(rows):
    assert rows
    y=np.array([r['outcomes'] for r in rows]); result={'n':len(rows),'models':{}}
    for model in ['baseline','poisson']:
        p=np.array([r[model] for r in rows]); markets={}
        for j,name in enumerate(['btts','over2.5']):
            losses=[binary_logloss(a,b) for a,b in zip(p[:,j],y[:,j])]
            bins=[]
            for k in range(5):
                ix=np.minimum((p[:,j]*5).astype(int),4)==k
                bins.append(dict(bin=k,n=int(sum(ix)),predicted=float(np.mean(p[ix,j])) if ix.any() else None,
                                 observed=float(np.mean(y[ix,j])) if ix.any() else None))
            markets[name]=dict(brier=float(np.mean((p[:,j]-y[:,j])**2)),
                logloss=float(np.mean(losses)) if all(math.isfinite(v) for v in losses) else 'Infinity',
                impossible_events=sum(not math.isfinite(v) for v in losses),mean_probability=float(np.mean(p[:,j])),
                event_rate=float(np.mean(y[:,j])),calibration_gap=float(np.mean(p[:,j]-y[:,j])),bins=bins)
        result['models'][model]=dict(primary_brier=float(np.mean((p-y)**2)),markets=markets)
    difference=(np.array([r['poisson'] for r in rows])-y)**2-(np.array([r['baseline'] for r in rows])-y)**2
    result['paired_brier']=intervals(rows,np.column_stack([difference.mean(axis=1),difference]))
    result['paired_brier']['order']=['primary','btts','over2.5']
    settlement=np.array([r['settlement'] for r in rows]); events=np.array([r['settlement_outcome'] for r in rows])
    result['total2.0']=dict(order=['under_win','push','over_win'],mean_probabilities=settlement.mean(axis=0).tolist(),
        counts=[int(sum(events==i)) for i in range(3)],observed_frequencies=[float(np.mean(events==i)) for i in range(3)])
    return result


def score():
    verify(); f=json.loads((OUT/'PREDICTION_FREEZE.json').read_text())
    assert f['freeze_sha256']==digest(OUT/'FREEZE.json')
    assert f['predictions_sha256']==digest(OUT/'predictions.json') and f['audit_sha256']==digest(OUT/'audit.json')
    rows=json.loads((OUT/'predictions.json').read_text()); results={}
    for league in ['E1','E0']:
        selected=[r for r in rows if r['league']==league]
        results[league]=dict(all=summarize(selected),seasons={str(year):summarize([r for r in selected if date(year,7,1)<=date.fromisoformat(r['date'])<date(year+1,7,1)]) for year in [2023,2024,2025]})
    save('results.json',results)
    print(json.dumps({k:v['all']['paired_brier'] for k,v in results.items()},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','score'])
    prepare() if parser.parse_args().phase=='prepare' else score()
