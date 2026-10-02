"""One frozen historical joint baseline/odds calibration; no model search."""
import hashlib
import json
from pathlib import Path
from datetime import date
from dataclasses import replace
from collections import defaultdict
import numpy as np
from scipy.special import expit
from deepfc.football_data_csv import load_football_data_csv
from deepfc.corner_distribution import negative_binomial_over_probability
from deepfc.team_corners import TEAM_CORNER_LINES,evaluate_predictions
from experiments.market_strength import CUTOFF,key,load_features,adjust
from experiments.time_decay import compare_models
from experiments.joint_strength import solve_newton,gates
from experiments.market_strength_diagnostic import observation,summarize

OUT=Path('experiments/results/joint_market_calibration')

def design(p,s):
    return [float(p.venue=='home'),float(p.venue=='away'),np.log(p.expected_corners/5),s]

def objective(theta,X,mu,y,alpha):
    eta=np.log(mu)+X@theta;pois=alpha<=1e-12
    loss=np.empty(len(y));score=np.empty(len(y));curv=np.empty(len(y))
    shape=1/alpha[~pois];z=eta[~pois]-np.log(shape);p=expit(z)
    loss[~pois]=(y[~pois]+shape)*np.logaddexp(0,z)-y[~pois]*eta[~pois]
    score[~pois]=(y[~pois]+shape)*p-y[~pois];curv[~pois]=(y[~pois]+shape)*p*(1-p)
    m=np.exp(eta[pois]);loss[pois]=m-y[pois]*eta[pois];score[pois]=m-y[pois];curv[pois]=m
    return float(loss.sum()+.5*theta@theta),X.T@score+theta,(X.T*curv)@X+np.eye(4)

def fit(predictions,features):
    train=[p for p in predictions if p.match.match_date<CUTOFF and key(p.match) in features]
    if not train:raise ValueError('no earlier eligible observations')
    s=[features[key(p.match)]*(1 if p.venue=='home' else -1) for p in train]
    X=np.array([design(p,t) for p,t in zip(train,s)]);mu=np.array([p.expected_corners for p in train]);y=np.array([p.actual_corners for p in train]);alpha=np.array([p.dispersion for p in train])
    def difference(theta,step):
        eta=np.log(mu)+X@theta;delta=X@step;pois=alpha<=1e-12;changes=np.empty(len(y))
        changes[pois]=np.exp(eta[pois])*np.expm1(delta[pois])-y[pois]*delta[pois]
        p=expit(eta[~pois]+np.log(alpha[~pois]))
        changes[~pois]=(y[~pois]+1/alpha[~pois])*np.log1p(p*np.expm1(delta[~pois]))-y[~pois]*delta[~pois]
        return float(changes.sum()+theta@step+.5*step@step)
    theta,cert=solve_newton(lambda t:objective(t,X,mu,y,alpha)[:2],lambda t:objective(t,X,mu,y,alpha)[2],difference,np.zeros(4))
    eta=np.log(mu.astype(np.longdouble))+X.astype(np.longdouble)@theta.astype(np.longdouble)
    m=np.exp(eta);a=alpha.astype(np.longdouble);a[a<=1e-12]=0
    grad=X.astype(np.longdouble).T@((m-y)/(1+a*m))+theta
    eigen=np.linalg.eigvalsh(objective(theta,X,mu,y,alpha)[2])
    assert np.isfinite(theta).all() and np.max(abs(grad))<=1e-8 and min(eigen)>0
    cert.update(independent_gradient_max=float(np.max(abs(grad))),hessian_min_eigenvalue=float(min(eigen)),training_n=len(train),latest_training_date=str(max(p.match.match_date for p in train)),cutoff=str(CUTOFF))
    return theta,cert

def predict(p,s,theta):
    if p.match.match_date<CUTOFF:raise ValueError('cannot score training period')
    mu=float(p.expected_corners*np.exp(np.dot(design(p,s),theta)))
    return replace(p,expected_corners=mu,over_probabilities={l:negative_binomial_over_probability(mu,l,p.dispersion) for l in TEAM_CORNER_LINES})

def run():
    old=json.loads(Path('experiments/results/market_strength/results.json').read_text())
    paths=[Path(p) for p in sorted(old['source_hashes'])]
    for p in paths:assert hashlib.sha256(p.read_bytes()).hexdigest()==old['source_hashes'][str(p)]
    seasons={m:2000+int(p.stem.split('_')[1][:2]) for p in paths for m in load_football_data_csv([p]).matches}
    features,excluded=load_features(paths)
    forecasts=compare_models(load_football_data_csv(paths).matches).time_weighted
    theta,cert=fit(forecasts,features)
    baseline=[p for p in forecasts if p.match.match_date>=CUTOFF and key(p.match) in features]
    signed=[features[key(p.match)]*(1 if p.venue=='home' else -1) for p in baseline]
    original=[adjust(p,features[key(p.match)],old['beta']) for p in baseline]
    new=[predict(p,s,theta) for p,s in zip(baseline,signed)]
    models={'fixed180':baseline,'original_odds':original,'joint':new}
    for period in ['validation','test','combined_later']:
        for name,oldname in [('fixed180','baseline'),('original_odds','candidate')]:
            subset=[p for p in models[name] if period=='combined_later' or (p.match.match_date<date(2024,7,1))==(period=='validation')]
            got=evaluate_predictions(subset);expected=old['periods'][period]['overall'][oldname]
            for k in ['mae','negative_binomial_negative_log_loss','mean_brier_score','evaluated_team_observations']:assert abs(got[k]-expected[k])<1e-12
    comparisons={}
    for ref in ['fixed180','original_odds']:
        grouped=defaultdict(list);indices=defaultdict(list)
        for i,(b,a,s) in enumerate(zip(models[ref],new,signed)):
            row=observation(b,a,s,seasons[b.match],0)
            for k in ['linear_shift','convexity_shift','nll_derivative_at_beta']:row.pop(k)
            row['band']='lt4' if baseline[i].expected_corners<4 else '4to6' if baseline[i].expected_corners<6 else 'ge6'
            for fields in [(),('period',),('season',),('venue',),('band',),('period','venue'),('period','band'),('season','band')]:
                label='/'.join(f'{f}={row[f]}' for f in fields) or 'all';grouped[label].append(row);indices[label].append(i)
        result={}
        for label,rows in grouped.items():
            summary=summarize(rows);ix=indices[label]
            metrics={name:evaluate_predictions(values[i] for i in ix) for name,values in models.items()}
            result[label]={'diagnostic':summary,'models':metrics}
        comparisons[ref]=result
    def compact(label):
        g=comparisons['fixed180'][label];d=g['diagnostic'];c={}
        for src,dest in [('brier_delta','mean_brier_score'),('nll_delta','negative_binomial_negative_log_loss'),('mae_delta','mae')]:c[dest]=src
        return {'baseline':dict(g['models']['fixed180'],bias=d['means']['baseline_bias']),
                'candidate':dict(g['models']['joint'],bias=d['means']['candidate_bias']),
                'candidate_minus_baseline':{dest:d['means'][src] for dest,src in c.items()},
                'paired_28_day_intervals':{dest:dict(zip(['lower_95','upper_95'],d['ci95'][src])) for dest,src in c.items()}}
    def check(period):
        prefix='' if period=='combined_later' else 'period=test/'
        group={'overall':compact('all' if not prefix else 'period=test'),'venue':{v:compact(prefix+'venue='+v) for v in ['home','away']},'band':{b:compact(prefix+'band='+b) for b in ['lt4','4to6','ge6']}}
        return gates(group,[compact('season='+str(y)) for y in ([2023,2024,2025] if not prefix else [2024,2025])])
    output={'theta':theta.tolist(),'coefficients':dict(zip(['a_home','a_away','gamma','beta'],[theta[0],theta[1],1+theta[2],theta[3]])),
            'fit_certificate':cert,'comparisons':comparisons,'gates':check('combined_later'),'test_only_gates':check('test'),
            'original_odds_gates_unchanged':old['gates'],'excluded_quotes':excluded,'source_hashes':old['source_hashes'],
            'spec_sha256':hashlib.sha256(Path('experiments/joint_market_calibration_spec.md').read_bytes()).hexdigest(),
            'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    output['decision']='research_only_pending_prospective_confirmation' if all(output['gates'].values()) else 'reject_under_frozen_gates'
    (OUT/'results.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:output[k] for k in ['coefficients','fit_certificate','gates','test_only_gates','decision']},indent=2))

if __name__=='__main__':run()
