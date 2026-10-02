"""One frozen normalized pre-closing market-strength feature; research only."""
import csv,json,hashlib,sys,math
from pathlib import Path
from dataclasses import replace
from datetime import date
import numpy as np
import scipy
from scipy.optimize import root_scalar
from scipy.special import expit
from deepfc.football_data_csv import load_football_data_csv,_parse_date
from deepfc.corner_distribution import negative_binomial_over_probability
from deepfc.team_corners import evaluate_predictions,TEAM_CORNER_LINES
from experiments.time_decay import compare_models
from experiments.joint_strength import comparison,gates

CUTOFF=date(2023,7,1)
def key(match):return match.match_date,match.home_team,match.away_team

def strength(row):
    odds=[float(row[k]) for k in ['AvgH','AvgD','AvgA']]
    if any(not math.isfinite(x) or x<=1 for x in odds):raise ValueError('finite odds >1 required')
    inv=[1/x for x in odds];p=[x/sum(inv) for x in inv]
    return p[0]-p[2]


def load_features(paths):
    features={};excluded=[];seen=set()
    for path in paths:
        year=2000+int(path.stem.split('_')[1][:2])
        if year<2019:continue
        for number,row in enumerate(csv.DictReader(path.open(encoding='utf-8-sig')),2):
            identity=(_parse_date(row['Date']),row['HomeTeam'].strip(),row['AwayTeam'].strip())
            if row['Div']!='E1' or identity in seen:raise ValueError('wrong league or duplicate fixture')
            seen.add(identity)
            try:features[identity]=strength(row)
            except (KeyError,ValueError,TypeError) as error:excluded.append({'path':str(path),'row':number,'fixture':[str(x) for x in identity],'reason':str(error)})
    return features,excluded


def objective(beta,mu,y,alpha,s):
    eta=np.log(mu)+beta*s
    poisson=alpha<=1e-12
    loss=np.empty(len(y));score=np.empty(len(y));curvature=np.empty(len(y))
    shape=1/alpha[~poisson];z=eta[~poisson]-np.log(shape);p=expit(z)
    loss[~poisson]=(y[~poisson]+shape)*np.logaddexp(0,z)-y[~poisson]*eta[~poisson]
    score[~poisson]=(y[~poisson]+shape)*p-y[~poisson]
    curvature[~poisson]=(y[~poisson]+shape)*p*(1-p)
    pred=np.exp(eta[poisson]);loss[poisson]=pred-y[poisson]*eta[poisson]
    score[poisson]=pred-y[poisson];curvature[poisson]=pred
    return float(sum(loss)+beta**2/2),float(score@s+beta),float(curvature@(s*s)+1)


def fit_beta(predictions,features):
    training=[p for p in predictions if p.match.match_date<CUTOFF and key(p.match) in features]
    if not training:raise ValueError('no eligible earlier training observations')
    arrays=tuple(np.asarray(x,dtype=float) for x in [
        [p.expected_corners for p in training],[p.actual_corners for p in training],
        [p.dispersion for p in training],[features[key(p.match)]*(1 if p.venue=='home' else -1) for p in training]])
    score=lambda b:objective(b,*arrays)[1]
    for limit in [1,2,4,8,16,32,64]:
        if score(-limit)<=0<=score(limit):break
    else:raise RuntimeError('score could not be bracketed')
    result=root_scalar(score,bracket=(-limit,limit),method='brentq',xtol=1e-12,rtol=1e-12,maxiter=200)
    value,gradient,curvature=objective(result.root,*arrays)
    if not result.converged or not math.isfinite(result.root) or abs(gradient)>1e-8 or curvature<=0:raise RuntimeError('coefficient numerical certificate failed')
    return float(result.root),{'training_observations':len(training),'latest_training_date':str(max(p.match.match_date for p in training)),
        'fit_cutoff':str(CUTOFF),'score':gradient,'curvature':curvature,'objective_omitting_constants':value,
        'iterations':result.iterations,'converged':bool(result.converged),'bracket_limit':limit}


def adjust(p,s,beta):
    if p.match.match_date<CUTOFF:raise ValueError('frozen coefficient cannot score earlier training dates')
    mean=p.expected_corners*math.exp(beta*s*(1 if p.venue=='home' else -1))
    return replace(p,expected_corners=mean,over_probabilities={l:negative_binomial_over_probability(mean,l,p.dispersion) for l in TEAM_CORNER_LINES})


def run():
    paths=sorted(Path('data').glob('E1_*.csv'));assert len(paths)==9
    digests={r['path']:r['sha256'] for r in json.loads(Path('experiments/results/shot_reconstruction/verified_data_manifest.json').read_text())['files']}
    for p in paths:assert hashlib.sha256(p.read_bytes()).hexdigest()==digests[str(p)]
    loaded=load_football_data_csv(paths);compared=compare_models(loaded.matches)
    features,excluded=load_features(paths)
    beta,certificate=fit_beta(compared.time_weighted,features)
    eligible=lambda p:p.match.match_date>=CUTOFF and key(p.match) in features
    baseline=tuple(p for p in compared.time_weighted if eligible(p))
    retained=tuple(p for p in compared.deepfc if eligible(p))
    candidate=tuple(adjust(p,features[key(p.match)],beta) for p in baseline)
    identity=lambda values:[(p.match,p.venue,p.actual_corners,p.dispersion) for p in values]
    assert identity(baseline)==identity(candidate)
    seasons={m:2000+int(p.stem.split('_')[1][:2]) for p in paths for m in load_football_data_csv([p]).matches}
    band=lambda p:'lt4' if p.expected_corners<4 else 'ge6' if p.expected_corners>=6 else '4to6'
    def sliced(predicate):
        pairs=[(b,a) for b,a in zip(baseline,candidate,strict=True) if predicate(b)]
        return comparison([b for b,a in pairs],[a for b,a in pairs])
    def cohort(predicate):
        return {'overall':sliced(predicate),'venue':{v:sliced(lambda p:predicate(p) and p.venue==v) for v in ['home','away']},
            'band':{label:sliced(lambda p:predicate(p) and band(p)==label) for label in ['lt4','4to6','ge6']}}
    periods={'validation':lambda p:p.match.match_date<date(2024,7,1),'test':lambda p:p.match.match_date>=date(2024,7,1),'combined_later':lambda p:True}
    out={'beta':beta,'coefficient_certificate':certificate,'periods':{name:cohort(fn) for name,fn in periods.items()},
        'seasons':{str(s):sliced(lambda p:seasons[p.match]==s) for s in [2023,2024,2025]},
        'retained_main':{name:evaluate_predictions(p for p in retained if fn(p)) for name,fn in periods.items()},
        'baseline_training_checkpoint':evaluate_predictions(p for p in compared.time_weighted if p.match.match_date<CUTOFF and key(p.match) in features),
        'data_quality':{'rows_read':loaded.rows_read,'corner_rows':loaded.rows_loaded,'valid_odds_fixtures':len(features),'excluded_quotes':excluded,
            'later_baseline_observations_before_odds_filter':sum(p.match.match_date>=CUTOFF for p in compared.time_weighted),'paired_evaluation_observations':len(baseline)},
        'source_hashes':digests,'versions':{'numpy':np.__version__,'scipy':scipy.__version__,'python':sys.version},
        'spec_sha256':hashlib.sha256(Path('experiments/market_strength_spec.md').read_bytes()).hexdigest(),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    out['gates']=gates(out['periods']['combined_later'],list(out['seasons'].values()))
    out['test_only_gates']=gates(out['periods']['test'],[out['seasons'][str(y)] for y in [2024,2025]])
    out['decision']='research_only_pending_timestamp_matched_validation' if all(out['gates'].values()) else 'reject_candidate_under_frozen_gates'
    return out

if __name__=='__main__':print(json.dumps(run(),indent=2))
