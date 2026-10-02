"""One temporal-OOF selected convex distribution mixture. No league tuning."""
import argparse,csv,json,hashlib,math
from pathlib import Path
from datetime import date
from collections import defaultdict
import numpy as np
from deepfc.football_data_csv import load_football_data_csv
from deepfc.corner_distribution import negative_binomial_negative_log_loss as nll,negative_binomial_over_probability as over
from experiments.time_decay import compare_models
from experiments.market_strength import key,load_features
from experiments.joint_market_calibration import fit,design
from experiments.e0_transfer import summary
OUT=Path('experiments/results/distribution_blend')

def mix_nll(y,b,c,alpha,w):
    if not 0<=w<=1:raise ValueError('mixture weight outside [0,1]')
    lb=nll(y,b,alpha);lc=nll(y,c,alpha)
    if w==0:return lb
    if w==1:return lc
    return float(-np.logaddexp(math.log1p(-w)-lb,math.log(w)-lc))

def choose_weight(pb,pc,y):
    d=np.asarray(pc)-pb;den=float(np.sum(d*d))
    return 0. if den==0 else float(np.clip(np.sum(d*(np.asarray(y)-pb))/den,0,1))

def prior_fit(predictions,features,cutoff):
    training=[p for p in predictions if p.match.match_date<cutoff]
    theta,cert=fit(training,features)
    assert date.fromisoformat(cert['latest_training_date'])<cutoff
    cert['effective_fold_cutoff']=str(cutoff)
    return theta,cert

def e1_inputs():
    saved=json.loads(Path('experiments/results/market_strength/results.json').read_text())
    paths=[Path(p) for p in sorted(saved['source_hashes'])]
    for p in paths:assert hashlib.sha256(p.read_bytes()).hexdigest()==saved['source_hashes'][str(p)]
    seasons={m:2000+int(p.stem.split('_')[1][:2]) for p in paths for m in load_football_data_csv([p]).matches}
    features,excluded=load_features(paths);assert not excluded
    forecasts=compare_models(load_football_data_csv(paths).matches).time_weighted
    return forecasts,features,seasons

def select():
    ps,features,seasons=e1_inputs();pb=[];pc=[];y=[];folds=[]
    for year in [2021,2022]:
        theta,cert=prior_fit(ps,features,date(year,7,1))
        held=[p for p in ps if seasons[p.match]==year and key(p.match) in features]
        assert all(p.match.match_date>=date(year,7,1) for p in held)
        for p in held:
            s=features[key(p.match)]*(1 if p.venue=='home' else -1);mu=float(p.expected_corners*np.exp(np.dot(design(p,s),theta)))
            for l in [3.5,4.5,5.5,6.5]:pb.append(over(p.expected_corners,l,p.dispersion));pc.append(over(mu,l,p.dispersion));y.append(float(p.actual_corners>l))
        folds.append({'source_season':year,'theta':theta.tolist(),'certificate':cert,'heldout_team_n':len(held)})
    weight=choose_weight(np.array(pb),np.array(pc),np.array(y))
    result={'weight':weight,'folds':folds,'selection_event_n':len(y),'selection_objective':'mean four-line Brier; analytic bounded minimizer',
        'denominator':float(np.sum((np.array(pc)-pb)**2)),
        'spec_sha256':hashlib.sha256(Path('experiments/distribution_blend_spec.md').read_bytes()).hexdigest(),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (OUT/'selection.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

def row_metrics(r,w):
    b=r['baseline_mean'];c=r['component_mean'];a=r['dispersion'];y=r['actual'];m=(1-w)*b+w*c
    row=dict(r);row['blend_mean']=m
    for name,mu in [('baseline',b),('component',c),('blend',m)]:
        row[name+'_bias']=y-mu;row[name+'_mae']=abs(y-mu)
        row[name+'_nll']=mix_nll(y,b,c,a,w) if name=='blend' else nll(y,mu,a)
        losses=[]
        for label,l in [('3.5',3.5),('4.5',4.5),('5.5',5.5),('6.5',6.5),('low_tail',1.5),('high_tail',9.5)]:
            p=(1-w)*over(b,l,a)+w*over(c,l,a) if name=='blend' else over(mu,l,a)
            hit=float(y>l)
            if label=='low_tail':p=1-p;hit=1-hit
            row[label+'_observed']=hit;row[name+'_'+label+'_probability']=p;row[name+'_'+label+'_error']=hit-p
            row[name+'_'+label+'_brier']=(hit-p)**2
            if l in [3.5,4.5,5.5,6.5]:losses.append((hit-p)**2)
        row[name+'_brier']=sum(losses)/4
    for ref in ['baseline','component']:
        for metric in ['brier','nll','mae','bias']:row['blend_minus_'+ref+'_'+metric]=row['blend_'+metric]-row[ref+'_'+metric]
    return row

def evaluate():
    sel=json.loads((OUT/'selection.json').read_text());assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==sel['code_sha256']
    assert hashlib.sha256(Path('experiments/distribution_blend_spec.md').read_bytes()).hexdigest()==sel['spec_sha256']
    w=sel['weight'];ps,features,seasons=e1_inputs();joint=json.loads(Path('experiments/results/joint_market_calibration/results.json').read_text());theta=np.array(joint['theta']);base=[]
    for p in ps:
        if p.match.match_date<date(2023,7,1) or key(p.match) not in features:continue
        s=features[key(p.match)]*(1 if p.venue=='home' else -1)
        base.append(dict(league='E1',date=str(p.match.match_date),home=p.match.home_team,away=p.match.away_team,venue=p.venue,season=seasons[p.match],actual=p.actual_corners,dispersion=p.dispersion,baseline_mean=p.expected_corners,component_mean=float(p.expected_corners*np.exp(np.dot(design(p,s),theta)))))
    for r in csv.DictReader(Path('experiments/results/e0_transfer/predictions.csv').open()):
        base.append(dict(league='E0',date=r['date'],home=r['home'],away=r['away'],venue=r['venue'],season=int(r['season']),actual=int(r['actual']),dispersion=float(r['dispersion']),baseline_mean=float(r['fixed180_mean']),component_mean=float(r['joint_mean'])))
    groups=defaultdict(list);rows=[]
    for r in base:
        r['band']='lt4' if r['baseline_mean']<4 else '4to6' if r['baseline_mean']<6 else 'ge6';r['era']='pre2023' if r['season']<2023 else '2023onward'
        row=row_metrics(r,w);rows.append(row)
        for fields in [('league',),('league','season'),('league','venue'),('league','band'),('league','era'),('league','season','band')]:groups['/'.join(f'{f}={row[f]}' for f in fields)].append(row)
    result={'weight':w,'selection_sha256':hashlib.sha256((OUT/'selection.json').read_bytes()).hexdigest(),'groups':{k:summary(v) for k,v in groups.items()},
        'sensitivity':{league:{str(d):summary(groups['league='+league],d) for d in [14,56]} for league in ['E1','E0']}}
    e0=json.loads(Path('experiments/results/e0_transfer/results.json').read_text())
    for league,expected in [('E1',joint['comparisons']['fixed180']['all']['models']),('E0',e0['comparisons']['joint_vs_fixed180']['groups']['all']['models'])]:
        got=result['groups']['league='+league]['means']
        for name,oldname in [('baseline','fixed180'),('component','joint')]:
            for metric,oldmetric in [('brier','mean_brier_score'),('nll','negative_binomial_negative_log_loss'),('mae','mae')]:assert abs(got[name+'_'+metric]-expected[oldname][oldmetric])<1e-12
    result['checks']='E1/E0 baseline and component Brier/NLL/MAE reproduce saved checkpoints within1e-12.'
    result['decision']='descriptive_exploratory_tradeoff_not_promotion'
    (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    with (OUT/'predictions.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    print('Weight',w,result['checks'])
    for league in ['E1','E0']:print(league,{k:v for k,v in result['groups']['league='+league]['means'].items() if k in ['baseline_brier','component_brier','blend_brier','blend_nll','blend_mae']})
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['select','evaluate']);args=parser.parse_args()
    select() if args.phase=='select' else evaluate()
