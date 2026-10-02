"""Single frozen joint venue attack/defence NB candidate; research only."""
from __future__ import annotations
import json, hashlib, sys
from pathlib import Path
from dataclasses import dataclass, replace
from itertools import groupby
import numpy as np
import scipy
from scipy.optimize import minimize
from scipy.special import expit
from scipy.linalg import helmert
from deepfc.football_data_csv import load_football_data_csv
from deepfc.corner_distribution import negative_binomial_over_probability
from deepfc.team_corners import TEAM_CORNER_LINES, evaluate_predictions
from experiments.time_decay import compare_models
from experiments.signal_strength import _comparison
from experiments.weakness_diagnostic import intervals

@dataclass
class Fit:
    teams: tuple
    intercept: np.ndarray
    effects: np.ndarray
    diagnostics: dict

    def predict(self, team, opponent, venue):
        v=0 if venue=='home' else 1
        index={t:i for i,t in enumerate(self.teams)}
        a=self.effects[v,index[team]] if team in index else 0.0
        d=self.effects[2+1-v,index[opponent]] if opponent in index else 0.0
        mean=float(np.exp(self.intercept[v]+a+d))
        if not np.isfinite(mean) or mean<=0:raise ValueError('invalid fitted mean')
        return mean


def design(history, when):
    if not history or any(m.match_date>=when for m in history):
        raise ValueError('nonempty history must strictly precede prediction date')
    teams=tuple(sorted({t for m in history for t in (m.home_team,m.away_team)}))
    index={t:i for i,t in enumerate(teams)};n=len(teams)
    y=[];w=[];venue=[];attack=[];defence=[]
    for m in history:
        for v,t,o,count in [(0,m.home_team,m.away_team,m.home_corners),(1,m.away_team,m.home_team,m.away_corners)]:
            y.append(count);w.append(2**(-(when-m.match_date).days/180))
            venue.append(v);attack.append(v*n+index[t]);defence.append((3-v)*n+index[o])
    return teams,tuple(np.asarray(x) for x in (y,w,venue,attack,defence))


def objective(theta, arrays, alpha):
    y,w,v,a,d=arrays;n=(len(theta)-2)//4
    effects=theta[2:].reshape(4,n);effects=effects-effects.mean(axis=1,keepdims=True)
    flat=effects.ravel();eta=theta[v]+flat[a]+flat[d]
    if alpha<=1e-12:
        mu=np.exp(eta);loss=mu-y*eta;deriv=mu-y
    else:
        shape=1/alpha;z=eta-np.log(shape)
        loss=(y+shape)*np.logaddexp(0,z)-y*eta
        deriv=(y+shape)*expit(z)-y
    weighted=w*deriv
    eg=(np.bincount(a,weights=weighted,minlength=4*n)+np.bincount(d,weights=weighted,minlength=4*n)).reshape(4,n)+effects
    eg-=eg.mean(axis=1,keepdims=True)
    grad=np.r_[np.bincount(v,weights=weighted,minlength=2),eg.ravel()]
    return float(np.dot(w,loss)+.5*np.sum(effects**2)),grad


def solve_newton(fun, hess, difference, initial):
    """Damped Newton with a score/curvature certificate, not a progress flag."""
    x=initial.copy()
    for iteration in range(100):
        value,gradient=fun(x);matrix=hess(x)
        if not np.isfinite(value) or not np.all(np.isfinite(matrix)):
            raise RuntimeError('nonfinite Newton objective/curvature')
        np.linalg.cholesky(matrix)  # Positive definite on identifiable coordinates.
        step=np.linalg.solve(matrix,-gradient)
        decrement=float(-gradient@step)
        residual=float(np.max(np.abs(matrix@step+gradient)))
        if (np.max(np.abs(gradient))<=1e-8 and np.max(np.abs(step))<=1e-8
                and 0<=decrement<=1e-12 and residual<=1e-10):
            return x,{'iterations':iteration,'success':True,'message':'independent score/curvature certified',
                'reduced_gradient_max':float(np.max(np.abs(gradient))),
                'newton_step_max':float(np.max(np.abs(step))),'newton_decrement_squared':decrement,
                'linear_solve_residual':residual}
        if decrement<=0 or not np.all(np.isfinite(step)):raise RuntimeError('invalid Newton direction')
        for backtrack in range(60):
            scale=2.0**(-backtrack)
            change=difference(x,scale*step)
            if np.isfinite(change) and change<=-1e-4*scale*decrement:
                x+=scale*step
                break
        else:raise RuntimeError('Newton line search failed')
    raise RuntimeError('Newton iteration limit; no fallback')


def fit(history, when, alpha):
    if not np.isfinite(alpha) or alpha<0:raise ValueError('invalid dispersion')
    teams,arrays=design(history,when);y,w,v,_,_=arrays
    n=len(teams)
    # Orthonormal contrasts eliminate the redundant four constant directions.
    basis=helmert(n,full=False).T
    transform=np.zeros((2+4*n,2+4*(n-1)));transform[:2,:2]=np.eye(2)
    for family in range(4):
        transform[2+family*n:2+(family+1)*n,2+family*(n-1):2+(family+1)*(n-1)]=basis
    initial=np.zeros(transform.shape[1])
    for venue in (0,1):
        mask=v==venue;initial[venue]=np.log(max(1e-6,float(np.dot(w[mask],y[mask])/w[mask].sum())))
    def reduced(x):
        value,gradient=objective(transform@x,arrays,alpha)
        return value,transform.T@gradient
    def hessian(x):
        theta=transform@x;_,_,venues,attack,defence=arrays
        eta=theta[venues]+theta[2+attack]+theta[2+defence]
        if alpha<=1e-12: curvature=w*np.exp(eta)
        else:
            probability=expit(eta+np.log(alpha))
            curvature=w*(y+1/alpha)*probability*(1-probability)
        # Each observation has exactly three unit entries in the raw design.
        columns=[venues,2+attack,2+defence]
        full=np.zeros((2+4*n,2+4*n))
        for left in columns:
            for right in columns:np.add.at(full,(left,right),curvature)
        full[2:,2:]+=np.eye(4*n)
        return transform.T@full@transform
    def difference(x, step):
        # Exact objective change, without subtracting two large summed losses.
        theta=transform@x; change=transform@step
        eta=theta[v]+theta[2+arrays[3]]+theta[2+arrays[4]]
        deta=change[v]+change[2+arrays[3]]+change[2+arrays[4]]
        if alpha<=1e-12:
            delta=np.exp(eta)*np.expm1(deta)-y*deta
        else:
            probability=expit(eta+np.log(alpha))
            delta=(y+1/alpha)*np.log1p(probability*np.expm1(deta))-y*deta
        return float(np.dot(w,delta)+np.dot(theta[2:],change[2:])+.5*np.dot(change[2:],change[2:]))
    x,certificate=solve_newton(reduced,hessian,difference,initial)
    theta=transform@x
    loss,grad=objective(theta,arrays,alpha);norm=float(np.max(np.abs(grad)))
    # Independent score formula, long-double accumulation in raw coordinates.
    eta=theta[v]+theta[2+arrays[3]]+theta[2+arrays[4]]
    mu=np.exp(eta.astype(np.longdouble))
    score=w.astype(np.longdouble)*(mu-y)/(1+alpha*mu)
    independent=np.zeros(len(theta),dtype=np.longdouble)
    for indices in [v,2+arrays[3],2+arrays[4]]:np.add.at(independent,indices,score)
    independent[2:]+=theta[2:]
    effects_gradient=independent[2:].reshape(4,n)
    effects_gradient-=effects_gradient.mean(axis=1,keepdims=True)
    agreement=float(np.max(np.abs(independent-grad)))
    independent_norm=float(np.max(np.abs(independent)))
    info={'date':str(when),'history_fixtures':len(history),'teams':len(teams),
          'objective':loss,'gradient_max':norm,'independent_gradient_max':independent_norm,
          'gradient_agreement':agreement,**certificate}
    if not np.isfinite(loss) or norm>1e-8 or independent_norm>1e-8 or agreement>1e-9:
        raise RuntimeError('fit certificate failure: '+json.dumps(info))
    from types import SimpleNamespace
    result=SimpleNamespace(x=theta)
    effects=result.x[2:].reshape(4,len(teams));effects=effects-effects.mean(axis=1,keepdims=True)
    return Fit(teams,result.x[:2],effects,info)


def generate(matches, baseline):
    by_day={day:list(group) for day,group in groupby(baseline,key=lambda p:p.match.match_date)}
    history=[];candidate=[];fits=[]
    for day,group in groupby(sorted(matches,key=lambda m:m.match_date),key=lambda m:m.match_date):
        if day in by_day:
            values=by_day[day];alpha=values[0].dispersion
            assert all(p.dispersion==alpha for p in values)
            model=fit(history,day,alpha);fits.append(model.diagnostics)
            for before in values:
                opponent=before.match.away_team if before.venue=='home' else before.match.home_team
                mean=model.predict(before.team,opponent,before.venue)
                candidate.append(replace(before,expected_corners=mean,over_probabilities={l:negative_binomial_over_probability(mean,l,alpha) for l in TEAM_CORNER_LINES}))
            if len(fits)%100==0:print(f'Completed {len(fits)} forecast-date fits through {day}',file=sys.stderr,flush=True)
        history.extend(group)
    assert [(p.match,p.venue,p.actual_corners,p.dispersion) for p in baseline]==[(p.match,p.venue,p.actual_corners,p.dispersion) for p in candidate]
    return tuple(candidate),fits


def comparison(before,after):
    result=_comparison(tuple(before),tuple(after))
    bias=lambda values:sum(p.actual_corners-p.expected_corners for p in values)/len(values)
    result['baseline']['bias']=bias(before);result['candidate']['bias']=bias(after)
    result['bias_intervals']=dict(zip(['baseline','candidate','candidate_minus_baseline'],intervals([
        (b.match.match_date,[b.actual_corners-b.expected_corners,a.actual_corners-a.expected_corners,b.expected_corners-a.expected_corners]) for b,a in zip(before,after,strict=True)])))
    return result


def gates(group,seasons):
    delta=group['overall']['candidate_minus_baseline'];ci=group['overall']['paired_28_day_intervals']
    result={'brier_material_improvement':delta['mean_brier_score']<=-.001,
            'brier_interval_below_zero':ci['mean_brier_score']['upper_95']<0,
            'each_later_season_improves':all(s['candidate_minus_baseline']['mean_brier_score']<0 for s in seasons),
            'nll_not_worse':delta['negative_binomial_negative_log_loss']<=0,
            'nll_upper_bound':ci['negative_binomial_negative_log_loss']['upper_95']<=.005,
            'venue_guardrail':all(v['candidate_minus_baseline']['mean_brier_score']<=.001 for v in group['venue'].values())}
    for label in ['lt4','ge6']:
        b=group['band'][label];result['halve_bias_'+label]=abs(b['candidate']['bias'])<=.5*abs(b['baseline']['bias'])
    return result


def run():
    from datetime import date
    paths=sorted(Path('data').glob('E1_*.csv'))
    manifest=json.loads(Path('experiments/results/shot_reconstruction/verified_data_manifest.json').read_text())
    digests={r['path']:r['sha256'] for r in manifest['files']}
    assert len(paths)==9
    for p in paths:assert hashlib.sha256(p.read_bytes()).hexdigest()==digests[str(p)]
    loaded=load_football_data_csv(paths);compared=compare_models(loaded.matches);baseline=compared.time_weighted
    candidate, fits=generate(loaded.matches,baseline)
    seasons={m:2000+int(p.stem.split('_')[1][:2]) for p in paths for m in load_football_data_csv([p]).matches}
    band=lambda p:'lt4' if p.expected_corners<4 else 'ge6' if p.expected_corners>=6 else '4to6'
    def sliced(predicate):
        pairs=[(b,a) for b,a in zip(baseline,candidate,strict=True) if predicate(b)]
        return comparison([b for b,a in pairs],[a for b,a in pairs])
    def cohort(predicate):
        return {'overall':sliced(predicate),'venue':{v:sliced(lambda p:predicate(p) and p.venue==v) for v in ['home','away']},
            'band':{label:sliced(lambda p:predicate(p) and band(p)==label) for label in ['lt4','4to6','ge6']}}
    periods={'development':lambda p:p.match.match_date<date(2023,7,1),
        'validation':lambda p:date(2023,7,1)<=p.match.match_date<date(2024,7,1),
        'test':lambda p:p.match.match_date>=date(2024,7,1),
        'combined_later':lambda p:p.match.match_date>=date(2023,7,1),'all':lambda p:True}
    out={'periods':{name:cohort(fn) for name,fn in periods.items()},
        'seasons':{str(s):sliced(lambda p:seasons[p.match]==s) for s in sorted({seasons[p.match] for p in baseline})},
        'retained_main':{name:evaluate_predictions(p for p in compared.deepfc if fn(p)) for name,fn in periods.items()},
        'fits':fits,'source_hashes':digests,'versions':{'numpy':np.__version__,'scipy':scipy.__version__,'python':sys.version},
        'spec_sha256':hashlib.sha256(Path('experiments/joint_strength_spec.md').read_bytes()).hexdigest(),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    out['gates']=gates(out['periods']['combined_later'],[out['seasons'][str(y)] for y in [2023,2024,2025]])
    out['test_only_gates']=gates(out['periods']['test'],[out['seasons'][str(y)] for y in [2024,2025]])
    out['decision']='research_only_pending_prospective' if all(out['gates'].values()) else 'reject_candidate'
    return out

if __name__=='__main__':
    try:print(json.dumps(run(),indent=2))
    except Exception as error:
        Path('experiments/results/joint_strength/failure.json').write_text(json.dumps({'error':str(error)},indent=2))
        raise
