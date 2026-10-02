import json,hashlib
from pathlib import Path
import numpy as np
from scipy.stats import nbinom
import argparse
parser=argparse.ArgumentParser(description='Check saved slices from reconstructed arrays')
parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[3])
parser.add_argument('--arrays-dir',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
R=args.repo;out={}
for league in ['E1','E0']:
 a=np.load(args.arrays_dir/('deepfc-review-'+league+'.npz'));y=a['y'];b=a['mu'];alpha=a['alpha'];r=1/alpha;selected=a['selected'];season=a['seasons'];v=a['venue'];dt=a['dates'];s=a['s'];c=json.loads((R/'experiments/results/joint_market_calibration/results.json').read_text())
 model={n:a['mean_'+n] for n in ['fixed180','original','joint']}
 if league=='E1':groups=c['comparisons']['fixed180'];key='diagnostic';metric_key='means'
 else:groups=json.loads((R/'experiments/results/e0_transfer/results.json').read_text())['comparisons']['joint_vs_fixed180']['groups'];key='paired';metric_key='means'
 errs=[]
 for label,g in groups.items():
  ix=selected.copy()
  if label!='all':
   for term in label.split('/'):
    k,value=term.split('=')
    if k=='season':ix&=season==int(value)
    elif k=='venue':ix&=v==value
    elif k=='band':ix&={'lt4':b<4,'4to6':(b>=4)&(b<6),'ge6':b>=6}[value]
    elif k=='era':ix&=(season<2023 if value=='pre2023' else season>=2023)
    elif k=='period':ix&=(season==2023 if value=='validation' else season>=2024)
  for n,m in model.items():
   p=r/(r+m);prob=nbinom.sf(np.arange(3,7)[None,:],r[:,None],p[:,None]);sc=((prob-(y[:,None]>np.arange(3,7)))**2).mean(axis=1)
   vals={'mean_brier_score':sc[ix].mean(),'mae':abs(y-m)[ix].mean(),'negative_binomial_negative_log_loss':-nbinom.logpmf(y,r,p)[ix].mean(),'mean_predicted_corners':m[ix].mean(),'mean_actual_corners':y[ix].mean()}
   saved=g['models']['original_odds' if n=='original' and league=='E1' else n]
   for metric,val in vals.items():errs.append(abs(val-saved[metric]))
  for name,func in [('low_tail',lambda m:nbinom.cdf(1,r,r/(r+m))),('high_tail',lambda m:nbinom.sf(9,r,r/(r+m)))]:
   for model_name,prefix in [('fixed180','baseline'),('joint','candidate')]:
    val=func(model[model_name])[ix].mean();errs.append(abs(val-g[key][metric_key][name+'_'+prefix+'_probability']))
 assert max(errs)<1e-12
 out[league]={'groups_checked':len(groups),'max_metric_or_tail_error':max(errs)}
 if league=='E1':
  train=~selected;X=np.column_stack([v=='home',v=='away',np.log(b/5),s]);theta=np.array(c['theta']);m=model['joint'];grad=X[train].T@((m-y)/(1+alpha*m))[train]+theta;H=(X[train].T*((y+r)*m*r/(m+r)**2)[train])@X[train]+np.eye(4)
  beta=json.loads((R/'experiments/results/market_strength/results.json').read_text())['beta'];om=model['original'];og=(s*(om-y)/(1+alpha*om))[train].sum()+beta
  out['certificates']={'joint_gradient_max':float(max(abs(grad))),'joint_hessian_min_eigenvalue':float(min(np.linalg.eigvalsh(H))),'original_gradient':float(og)}
 # Both date and fixture pairs stay together in independent bootstrap.
 for era,ix in [('later',selected & (season>=2023))]:
  probs=nbinom.sf(np.arange(3,7)[None,:],r[:,None],(r/(r+model['joint']))[:,None]);out[league]['later_joint_over_errors']=((y[:,None]>np.arange(3,7))-probs)[ix].mean(axis=0).tolist()
checks=[]
for folder in ['market_strength','joint_market_calibration','e0_transfer']:
 for line in (R/f'experiments/results/{folder}/frozen_hashes.txt').read_text().splitlines():
  digest,path=line.split(maxsplit=1);p=R/path
  checks.append({'path':path,'matches':p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==digest})
out['frozen_hash_checks']=checks
print(json.dumps(out,indent=2));args.output.write_text(json.dumps(out,indent=2))
