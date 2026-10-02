"""One approved home slope experiment. Published modules are imported read-only."""
from pathlib import Path
from datetime import date
from collections import Counter
import hashlib,json,csv
import numpy as np
from scipy.special import expit
from scipy.optimize import brentq
from scipy.stats import nbinom,poisson
from experiments.joint_market_calibration import objective as joint_objective,design
from experiments.joint_strength import solve_newton
from experiments.market_strength import key,load_features
from experiments.time_decay import compare_models
from deepfc.football_data_csv import load_football_data_csv

FOLDS=tuple((date(y,7,1),date(y+1,7,1)) for y in [2020,2021,2022])
BOUNDS=(-.5,.5)
PRIOR_SD=.25
PIVOT=5.

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def transform(mu,home,delta):
    if not np.isfinite(delta) or not BOUNDS[0]<=delta<=BOUNDS[1]:raise ValueError('delta outside frozen bounds')
    mu=np.asarray(mu,dtype=float);home=np.asarray(home,dtype=bool)
    if not np.isfinite(mu).all() or np.any(mu<=0) or mu.shape!=home.shape:raise ValueError('invalid means or venue shape')
    result=mu.copy()
    if delta!=0:result[home]=mu[home]*np.exp(delta*np.log(mu[home]/PIVOT))
    if not np.isfinite(result).all() or np.any(result<=0):raise ValueError('invalid corrected means')
    return result

def distribution(mu,alpha,y=None):
    mu=np.asarray(mu,dtype=float);alpha=np.asarray(alpha,dtype=float)
    if np.any(mu<=0) or np.any(alpha<0) or not np.isfinite(mu).all() or not np.isfinite(alpha).all():raise ValueError('invalid distribution inputs')
    po=alpha<=1e-12;p=np.empty((len(mu),4));nll=np.empty(len(mu)) if y is not None else None
    p[po]=poisson.sf(np.arange(3,7)[None,:],mu[po,None])
    r=1/alpha[~po];q=r/(r+mu[~po]);p[~po]=nbinom.sf(np.arange(3,7)[None,:],r[:,None],q[:,None])
    if y is not None:
        y=np.asarray(y);nll[po]=-poisson.logpmf(y[po],mu[po]);nll[~po]=-nbinom.logpmf(y[~po],r,q)
    if not np.isfinite(p).all() or np.any(np.diff(p,axis=1)>0):raise ValueError('incoherent probabilities')
    return p,nll

def fit_joint_before(predictions,features,cutoff):
    train=[p for p in predictions if p.match.match_date<cutoff and key(p.match) in features]
    if not train:raise ValueError('no earlier training observations')
    s=[features[key(p.match)]*(1 if p.venue=='home' else -1) for p in train]
    X=np.array([design(p,t) for p,t in zip(train,s)]);mu=np.array([p.expected_corners for p in train]);y=np.array([p.actual_corners for p in train]);alpha=np.array([p.dispersion for p in train])
    def difference(theta,step):
        eta=np.log(mu)+X@theta;delta=X@step;po=alpha<=1e-12;changes=np.empty(len(y))
        changes[po]=np.exp(eta[po])*np.expm1(delta[po])-y[po]*delta[po]
        prob=expit(eta[~po]+np.log(alpha[~po]))
        changes[~po]=(y[~po]+1/alpha[~po])*np.log1p(prob*np.expm1(delta[~po]))-y[~po]*delta[~po]
        return float(changes.sum()+theta@step+.5*step@step)
    theta,cert=solve_newton(lambda t:joint_objective(t,X,mu,y,alpha)[:2],lambda t:joint_objective(t,X,mu,y,alpha)[2],difference,np.zeros(4))
    eta=np.log(mu.astype(np.longdouble))+X.astype(np.longdouble)@theta.astype(np.longdouble)
    m=np.exp(eta);a=alpha.astype(np.longdouble);a[a<=1e-12]=0
    grad=X.astype(np.longdouble).T@((m-y)/(1+a*m))+theta
    eigen=np.linalg.eigvalsh(joint_objective(theta,X,mu,y,alpha)[2])
    if not np.isfinite(theta).all() or np.max(abs(grad))>1e-8 or min(eigen)<=0:raise RuntimeError('joint fit certificate failed')
    cert.update(independent_gradient_max=float(max(abs(grad))),hessian_min_eigenvalue=float(min(eigen)),training_n=len(train),training_fixtures=len({key(p.match) for p in train}),latest_training_date=str(max(p.match.match_date for p in train)),cutoff=str(cutoff),theta=theta.tolist())
    return theta,cert

def scalar_objective(delta,mu,y,alpha):
    x=np.log(mu/PIVOT);m=mu*np.exp(delta*x);_,nll=distribution(m,alpha,y)
    score=np.sum(x*(m-y)/(1+alpha*m))+delta/PRIOR_SD**2
    hess=np.sum(x*x*m*(1+alpha*y)/(1+alpha*m)**2)+1/PRIOR_SD**2
    return float(nll.sum()+.5*(delta/PRIOR_SD)**2),float(score),float(hess)

def fit_delta(mu,y,alpha):
    mu=np.asarray(mu,dtype=float);y=np.asarray(y,dtype=float);alpha=np.asarray(alpha,dtype=float)
    left=scalar_objective(BOUNDS[0],mu,y,alpha)[1];right=scalar_objective(BOUNDS[1],mu,y,alpha)[1]
    boundary=False
    if left>=0:delta=BOUNDS[0];boundary=True
    elif right<=0:delta=BOUNDS[1];boundary=True
    else:delta=brentq(lambda d:scalar_objective(d,mu,y,alpha)[1],*BOUNDS,xtol=1e-14,rtol=1e-14,maxiter=200)
    value,score,hessian=scalar_objective(delta,mu,y,alpha)
    ld=np.longdouble;x=np.log(mu.astype(ld)/5);m=mu.astype(ld)*np.exp(ld(delta)*x)
    independent=float(np.sum(x*(m-y)/(1+alpha*m))+ld(16)*delta)
    if not np.isfinite([delta,value,score,hessian,independent]).all() or hessian<=0 or abs(score-independent)>1e-8:raise RuntimeError('scalar certificate failed')
    if not boundary and abs(independent)>1e-8:raise RuntimeError('scalar interior score failed')
    if boundary and not ((delta==BOUNDS[0] and score>=0) or (delta==BOUNDS[1] and score<=0)):raise RuntimeError('boundary KKT failed')
    return {'delta':float(delta),'objective':value,'gradient':score,'independent_gradient':independent,'hessian':hessian,'boundary':boundary,'score_at_zero':scalar_objective(0,mu,y,alpha)[1],'endpoint_scores':[left,right]}

def support(rows):
    home=[r for r in rows if r['venue']=='home'];counts={'home_n':len(home)}
    for name,mask in [('below5',lambda m:m<5),('above5',lambda m:m>5)]:
        rs=[r for r in home if mask(r['joint_mean'])]
        counts[name]={'n':len(rs),'blocks':len({date.fromisoformat(r['date']).toordinal()//28 for r in rs})}
    counts['passes']=len(home)>=500 and all(counts[k]['n']>=100 and counts[k]['blocks']>=15 for k in ['below5','above5'])
    return counts

def stopping_reason(certificate,counts):
    if not counts['passes']:return 'stop_insufficient_oof_support'
    if certificate['boundary']:return 'stop_boundary_optimum'
    if certificate['delta']<=0:return 'stop_nonpositive_delta'
    return 'eligible_for_frozen_later_evaluation'

def run_earlier(repo,data_root,out):
    repo=Path(repo);data_root=Path(data_root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    expected=json.loads((repo/'experiments/results/market_strength/results.json').read_text())['source_hashes']
    paths=[data_root/Path(p).name for p in sorted(expected) if int(Path(p).stem.split('_')[1][:2])<23]
    for p in paths:
        if sha(p)!=expected['data/'+p.name]:raise ValueError('source hash mismatch')
    finalfile=repo/'experiments/results/joint_market_calibration/results.json'
    manifest={'published_commit':'7e8ad0acdcea13f5778e107882c36e5d6922fbd3','code_sha256':sha(__file__),'plan_sha256':sha(out/'APPROVED_PLAN.md'),'final_joint_coefficients_sha256':sha(finalfile),'source_hashes':{p.name:sha(p) for p in paths},'bounds':list(BOUNDS),'prior_sd':PRIOR_SD,'pivot':PIVOT,'folds':[[str(a),str(b)] for a,b in FOLDS]}
    (out/'pre_fit_manifest.json').write_text(json.dumps(manifest,indent=2))
    result={'status':'started_earlier_only','later_scoring_executed':False,'folds':[]}
    rows=[]
    try:
        loaded=load_football_data_csv(paths);matches=[m for m in loaded.matches if m.match_date<date(2023,7,1)]
        baseline=compare_models(matches).time_weighted;features,excluded=load_features(paths)
        result['source_quality']={'rows_read':loaded.rows_read,'rows_loaded':loaded.rows_loaded,'excluded_quotes':excluded}
        for start,end in FOLDS:
            training=[p for p in baseline if p.match.match_date<start and key(p.match) in features]
            pairs=Counter(key(p.match) for p in training)
            if any(n!=2 for n in pairs.values()):raise RuntimeError('incomplete training pairs')
            if len(pairs)<200:
                result['status']='stop_insufficient_first_stage_support';result['failed_fold_start']=str(start);break
            theta,cert=fit_joint_before(baseline,features,start)
            selected=[p for p in baseline if start<=p.match.match_date<end and key(p.match) in features]
            pairs=Counter(key(p.match) for p in selected)
            if any(n!=2 for n in pairs.values()):raise RuntimeError('incomplete OOF pairs')
            current=[]
            for p in selected:
                s=features[key(p.match)]*(1 if p.venue=='home' else -1);mu=float(p.expected_corners*np.exp(np.dot(design(p,s),theta)))
                r={'date':str(p.match.match_date),'home':p.match.home_team,'away':p.match.away_team,'venue':p.venue,'actual':p.actual_corners,'alpha':p.dispersion,'baseline_mean':p.expected_corners,'strength':s,'joint_mean':mu,'fold_start':str(start),'fold_end':str(end)}
                rows.append(r);current.append(r)
            cert['oof_support']=support(current);cert['oof_team_n']=len(current);result['folds'].append(cert)
            print('Completed earlier fold',start,'training fixtures',len(training)//2,'OOF fixtures',len(selected)//2,flush=True)
        else:
            counts=support(rows);result['support']=counts
            if not counts['passes']:result['status']='stop_insufficient_oof_support'
            else:
                h=[r for r in rows if r['venue']=='home'];cert=fit_delta(np.array([r['joint_mean'] for r in h]),np.array([r['actual'] for r in h]),np.array([r['alpha'] for r in h]))
                result['scalar_fit']=cert;result['status']=stopping_reason(cert,counts)
    except Exception as error:
        result['status']='stop_numerical_or_integrity_failure';result['error']=repr(error)
    if rows:
        with (out/'oof_predictions.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        result['oof_predictions_sha256']=sha(out/'oof_predictions.csv')
    if sha(finalfile)!=manifest['final_joint_coefficients_sha256']:raise RuntimeError('published coefficients changed')
    (out/'earlier_results.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--repo',required=True);parser.add_argument('--data-root',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args();run_earlier(args.repo,args.data_root,args.out)
