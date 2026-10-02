"""Prespecified exploratory cuts of existing forecasts; no new candidate."""
import json,random,hashlib
from pathlib import Path
from collections import defaultdict
from itertools import groupby
from deepfc.football_data_csv import load_football_data_csv
from deepfc.team_corners import evaluate_predictions, TEAM_CORNER_LINES
from deepfc.corner_distribution import negative_binomial_over_probability
from experiments.time_decay import compare_models


SEASONS = {}
def season(m):return SEASONS[m]

def intervals(rows):
    blocks=defaultdict(list)
    for day,values in rows:blocks[day.toordinal()//28].append(values)
    totals=[(len(v),[sum(x[k] for x in v) for k in range(len(v[0]))]) for v in blocks.values()]
    rng=random.Random(7);draws=[[] for _ in totals[0][1]]
    for _ in range(2000):
        selected=rng.choices(totals,k=len(totals));n=sum(t[0] for t in selected)
        for k in range(len(draws)):draws[k].append(sum(t[1][k] for t in selected)/n)
    return [[sorted(v)[int(.025*(len(v)-1))],sorted(v)[int(.975*(len(v)-1))]] for v in draws]


def run():
    paths=sorted(Path('data').glob('E1_*.csv'))
    matches=load_football_data_csv(paths).matches
    SEASONS.clear()
    for path in paths:
        source_year=2000+int(path.stem.split('_')[1][:2])
        for match in load_football_data_csv([path]).matches:
            assert match not in SEASONS
            SEASONS[match]=source_year
    members=defaultdict(set)
    for m in matches:members[season(m)].update((m.home_team,m.away_team))
    meta={};counts=defaultdict(int)
    for day,group in groupby(matches,key=lambda m:m.match_date):
        group=list(group)
        for m in group:
            for team in (m.home_team,m.away_team):
                entrant='entrant' if team not in members[season(m)-1] else 'incumbent'
                phase='first10' if counts[season(m),team]<10 else 'later'
                meta[m,team]=(entrant,phase)
        for m in group:
            for team in (m.home_team,m.away_team):counts[season(m),team]+=1
    compared=compare_models(matches);groups=defaultdict(list)
    for retained,fixed in zip(compared.deepfc,compared.time_weighted,strict=True):
        assert (retained.match,retained.venue)==(fixed.match,fixed.venue)
        entrant,phase=meta[fixed.match,fixed.team]
        band='lt4' if fixed.expected_corners<4 else '4to6' if fixed.expected_corners<6 else 'ge6'
        keys=['all','season/'+str(season(fixed.match)),'venue/'+fixed.venue,'mean/'+band,
              'phase/'+phase,'membership/'+entrant,'transition/'+entrant+'/'+phase]
        for k in keys:groups[k].append((retained,fixed))
    output={}
    for name,pairs in groups.items():
        out={};bootstrap=[]
        for side,idx in [('retained',0),('fixed180',1)]:
            values=[p[idx] for p in pairs];metrics=evaluate_predictions(values)
            metrics['bias_actual_minus_predicted']=sum(p.actual_corners-p.expected_corners for p in values)/len(values)
            for label,threshold in [('low',1.5),('high',9.5)]:
                probability=lambda p:negative_binomial_over_probability(p.expected_corners,threshold,p.dispersion)
                probs=[1-probability(p) if label=='low' else probability(p) for p in values]
                hits=[p.actual_corners<=1 if label=='low' else p.actual_corners>=10 for p in values]
                metrics[label+'_tail']={'predicted':sum(probs)/len(probs),'observed':sum(hits)/len(hits)}
            out[side]=metrics
        for before,after in pairs:
            brier=lambda p:sum((p.over_probabilities[l]-(p.actual_corners>l))**2 for l in TEAM_CORNER_LINES)/4
            lo=1-negative_binomial_over_probability(after.expected_corners,1.5,after.dispersion)
            hi=negative_binomial_over_probability(after.expected_corners,9.5,after.dispersion)
            bootstrap.append((after.match.match_date,[after.actual_corners-after.expected_corners,brier(after)-brier(before),
                (after.actual_corners<=1)-lo,(after.actual_corners>=10)-hi]))
        out['intervals']=dict(zip(['fixed180_bias','fixed_minus_retained_brier','fixed_low_tail_observed_minus_predicted','fixed_high_tail_observed_minus_predicted'],intervals(bootstrap)))
        output[name]=out
    return {'groups':output,'sources':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
            'design_sha256':hashlib.sha256(Path('experiments/results/weakness_diagnostic/DESIGN.md').read_bytes()).hexdigest()}

if __name__=='__main__':print(json.dumps(run(),indent=2))
