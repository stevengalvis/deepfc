"""Frozen E0 transfer: no coefficient estimation or model selection."""
import csv,json,hashlib,random
from collections import defaultdict
from dataclasses import replace
from datetime import date
from pathlib import Path
import numpy as np
from deepfc.football_data_csv import load_football_data_csv,_parse_date
from deepfc.corner_distribution import negative_binomial_over_probability
from deepfc.team_corners import TEAM_CORNER_LINES,evaluate_predictions
from experiments.time_decay import compare_models
from experiments.market_strength import strength,key
from experiments.market_strength_diagnostic import observation
OUT=Path('experiments/results/e0_transfer')

def transform(p,s,c):
    if p.match.competition!='E0':raise ValueError('E0 transfer only')
    mu=float(5*np.exp(c['a_'+p.venue]+c['gamma']*np.log(p.expected_corners/5)+c['beta']*s))
    return replace(p,expected_corners=mu,over_probabilities={l:negative_binomial_over_probability(mu,l,p.dispersion) for l in TEAM_CORNER_LINES})

def summary(rows,width=28):
    names=[k for k,v in rows[0].items() if isinstance(v,(int,float)) and k!='season']
    blocks=defaultdict(list)
    for r in rows:blocks[date.fromisoformat(r['date']).toordinal()//width].append([r[k] for k in names])
    sizes=np.array([len(v) for v in blocks.values()]);totals=np.array([np.sum(v,axis=0) for v in blocks.values()]);n=len(sizes)
    rng=random.Random(7);w=np.array([np.bincount(rng.choices(range(n),k=n),minlength=n) for _ in range(10000)])
    draws=np.sort((w@totals)/(w@sizes)[:,None],axis=0)
    return {'n_team':len(rows),'n_fixtures':len({(r['date'],r['home'],r['away']) for r in rows}),'blocks':n,
      'means':{k:float(np.mean([r[k] for r in rows])) for k in names},
      'ci95':{k:[float(draws[249,i]),float(draws[9749,i])] for i,k in enumerate(names)}}

def run():
    inv=json.loads(Path('experiments/results/e0_feasibility/inventory.json').read_text());root=Path('/workspace/shot-data-mirror-liam');paths=[];seasons={};features={};excluded=[]
    for f in inv['files']:
        path=root/f['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==f['sha256'];paths.append(path)
        year=int(f['season'][:4])
        for m in load_football_data_csv([path]).matches:seasons[m]=year
        if year<2019:continue
        for r in csv.DictReader(path.open(encoding='utf-8-sig')):
            k=(_parse_date(r['Date']),r['HomeTeam'].strip(),r['AwayTeam'].strip())
            assert r['Div']=='E0' and k not in features
            try:features[k]=strength(r)
            except (ValueError,KeyError,TypeError):excluded.append([str(v) for v in k])
    saved={name:Path(f'experiments/results/{folder}/results.json') for name,folder in [('original','market_strength'),('joint','joint_market_calibration')]}
    old=json.loads(saved['original'].read_text());joint=json.loads(saved['joint'].read_text())
    coeff={'original':{'a_home':0.,'a_away':0.,'gamma':1.,'beta':old['beta']},'joint':joint['coefficients']}
    full=compare_models(load_football_data_csv(paths).matches,competition='E0',evaluation_start=date(2019,7,1)).time_weighted
    b=[p for p in full if key(p.match) in features];s=[features[key(p.match)]*(1 if p.venue=='home' else -1) for p in b]
    models={'fixed180':b,**{name:[transform(p,t,c) for p,t in zip(b,s)] for name,c in coeff.items()}}
    identity=lambda ps:[(p.match,p.venue,p.actual_corners,p.dispersion) for p in ps]
    assert all(identity(ps)==identity(b) for ps in models.values())
    output={'coefficients':coeff,'coefficient_file_hashes':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in saved.items()},'source_files':inv['files'],
      'eligible_team_observations_before_quotes':len(full),'eligible_after_quotes':len(b),'excluded_quotes':excluded,'comparisons':{}}
    for ref,target in [('fixed180','joint'),('fixed180','original'),('original','joint')]:
        grouped=defaultdict(list);indices=defaultdict(list)
        for i,(before,after) in enumerate(zip(models[ref],models[target])):
            row=observation(before,after,s[i],seasons[before.match],0)
            for k in ['linear_shift','convexity_shift','nll_derivative_at_beta']:row.pop(k)
            row['band']='lt4' if b[i].expected_corners<4 else '4to6' if b[i].expected_corners<6 else 'ge6'
            row['era']='pre2023' if row['season']<2023 else '2023onward'
            for fields in [(),('season',),('venue',),('band',),('season','band'),('era',)]:
                label='/'.join(f'{f}={row[f]}' for f in fields) or 'all';grouped[label].append(row);indices[label].append(i)
        results={}
        for label,rows in grouped.items():
            results[label]={'paired':summary(rows),'models':{name:evaluate_predictions(ps[i] for i in indices[label]) for name,ps in models.items()}}
        output['comparisons'][target+'_vs_'+ref]={'groups':results,'overall_sensitivity':{str(w):summary(grouped['all'],w) for w in [14,56]}}
    with (OUT/'predictions.csv').open('w',newline='') as f:
        writer=csv.writer(f,lineterminator='\n');writer.writerow(['date','home','away','venue','season','actual','dispersion','signed_strength','fixed180_mean','original_mean','joint_mean'])
        for i,p in enumerate(b):writer.writerow([str(p.match.match_date),p.match.home_team,p.match.away_team,p.venue,seasons[p.match],p.actual_corners,p.dispersion,s[i],p.expected_corners,models['original'][i].expected_corners,models['joint'][i].expected_corners])
    output['decision']='historical_transfer_description_only_no_promotion'
    output['execution_hashes']={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['experiments/e0_transfer.py','experiments/e0_transfer_spec.md','experiments/time_decay.py']}
    (OUT/'results.json').write_text(json.dumps(output,indent=2)+'\n')
    print('Complete:',len(b),'team observations; no coefficients fitted.')
    for name,c in output['comparisons'].items():print(name,{k:v for k,v in c['groups']['all']['paired']['means'].items() if k in ['brier_delta','nll_delta','mae_delta']})
if __name__=='__main__':run()
