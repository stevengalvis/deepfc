import csv,json,math,random,hashlib
from pathlib import Path
from datetime import datetime,date
from collections import Counter
import numpy as np
from scipy.stats import nbinom
import argparse
parser=argparse.ArgumentParser(description='Reproduce frozen audit arithmetic without fitting any candidate')
parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[3])
parser.add_argument('--data-root',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args()
ROOT=args.repo
args.output_dir.mkdir(parents=True,exist_ok=True)
C=json.loads((ROOT/'experiments/results/joint_market_calibration/results.json').read_text())
O=json.loads((ROOT/'experiments/results/market_strength/results.json').read_text())
E=json.loads((ROOT/'experiments/results/e0_transfer/results.json').read_text())
output={}
def bootstrap(dates,loss,width,draws):
 ids=dates//width;unique=list(dict.fromkeys(ids));tot=np.array([loss[ids==i].sum() for i in unique]);size=np.array([(ids==i).sum() for i in unique]);rng=random.Random(7)
 vals=[]
 for _ in range(draws):
  ix=rng.choices(range(len(unique)),k=len(unique));vals.append(tot[ix].sum()/size[ix].sum())
 return {'blocks':len(unique),'ci':np.sort(vals)[[int(.025*(draws-1)),int(.975*(draws-1))]].tolist()}
for league in ['E1','E0']:
 rows=[];invalid=0;missing=0
 for p in sorted((args.data_root/league).glob('*.csv')):
  season=2000+int(p.stem.split('_')[1][:2]) if league=='E1' else int(p.stem[:4])
  for r in csv.DictReader(p.open(encoding='utf-8-sig')):
   if not r.get('HC','').strip() or not r.get('AC','').strip():missing+=1;continue
   d=None
   for fmt in ['%d/%m/%Y','%d/%m/%y']:
    try:d=datetime.strptime(r['Date'],fmt).date();break
    except ValueError:pass
   assert d and r['Div']==league
   s=None
   if season>=2019:
    try:
     odds=np.array([float(r[k]) for k in ['AvgH','AvgD','AvgA']]);assert np.isfinite(odds).all() and (odds>1).all();pr=(1/odds)/sum(1/odds);s=pr[0]-pr[2]
    except (ValueError,KeyError,AssertionError):invalid+=1
   rows.append((d.toordinal(),r['HomeTeam'].strip(),r['AwayTeam'].strip(),int(r['HC']),int(r['AC']),season,s))
 rows.sort(key=lambda r:r[0]);assert len({r[:3] for r in rows})==len(rows)
 # Independent vectorized fixed180 implementation: one strict-earlier date mask, venue sums, 5-match smoothing.
 dates=np.array([r[0] for r in rows]);home=np.array([r[1] for r in rows]);away=np.array([r[2] for r in rows]);counts=np.array([r[3:5] for r in rows]);records=[]
 for i,r in enumerate(rows):
  if r[5]<2019:continue
  ix=np.flatnonzero(dates<r[0]);past=counts[ix];n=past.size
  if n<100:continue
  hm=home[ix]==r[1];am=away[ix]==r[2]
  if min(hm.sum(),am.sum())<5:continue
  if r[6] is None:continue
  w=2.**(-(r[0]-dates[ix])/180);alpha=max(0.,(past.flatten().var(ddof=1)-past.mean())/past.mean()**2)
  for v in [0,1]:
   teammask=hm if v==0 else am;oppmask=am if v==0 else hm
   rate=(w@past[:,v]+5)/(w.sum()+5)
   attack=(w[teammask]@past[teammask,v]+5*rate)/(w[teammask].sum()+5)
   allowed=(w[oppmask]@past[oppmask,v]+5*rate)/(w[oppmask].sum()+5)
   records.append({'date':r[0],'home':r[1],'away':r[2],'venue':['home','away'][v],'season':r[5],'actual':r[3+v],'alpha':alpha,'s':r[6]*(1 if v==0 else -1),'mu':attack*allowed/rate})
 assert all(n==2 for n in Counter((r['date'],r['home'],r['away']) for r in records).values())
 def array(k):return np.array([r[k] for r in records])
 mu=array('mu');s=array('s');y=array('actual');alpha=array('alpha');dt=array('date');seasons=array('season');v=array('venue');c=C['coefficients']
 means={'fixed180':mu,'original':mu*np.exp(O['beta']*s),'joint':5*np.exp(np.where(v=='home',c['a_home'],c['a_away'])+c['gamma']*np.log(mu/5)+c['beta']*s)}
 if league=='E1':
  train=dt<date(2023,7,1).toordinal();X=np.column_stack([v=='home',v=='away',np.log(mu/5),s]);theta=np.array(C['theta']);score=X[train].astype(np.longdouble).T@((means['joint'][train]-y[train])/(1+alpha[train]*means['joint'][train]))+theta
  output['training_certificate']={'n':int(train.sum()),'latest':str(date.fromordinal(int(max(dt[train])))),'gradient_at_saved_theta':float(max(abs(score)))}
  selected=~train
 else:selected=np.ones(len(y),dtype=bool)
 scores={};metrics={};lines=np.array([3.5,4.5,5.5,6.5]);shape=1/alpha
 for name,m in means.items():
  prob=nbinom.sf(np.floor(lines)[None,:],shape[:,None],(shape/(shape+m))[:,None]);brier=((prob-(y[:,None]>lines))**2).mean(axis=1);nll=-nbinom.logpmf(y,shape,shape/(shape+m));mae=abs(y-m)
  scores[name]=brier;metrics[name]={'brier':float(brier[selected].mean()),'nll':float(nll[selected].mean()),'mae':float(mae[selected].mean()),'bias':float((y-m)[selected].mean()),'observed_over':(y[:,None]>lines)[selected].mean(axis=0).tolist(),'predicted_over':prob[selected].mean(axis=0).tolist()}
  if league=='E0':target=E['comparisons']['joint_vs_fixed180']['groups']['all']['models'][name]
  else:target=C['comparisons']['fixed180']['all']['models']['original_odds' if name=='original' else name]
  for metric,saved in [('brier','mean_brier_score'),('nll','negative_binomial_negative_log_loss'),('mae','mae')]:assert abs(metrics[name][metric]-target[saved])<1e-12,(league,name,metric)
 report={'raw_corner_fixtures':len(rows),'missing_corners':missing,'invalid_quotes':invalid,'scored_teams':int(selected.sum()),'metrics':metrics,'ci':bootstrap(dt[selected],(scores['joint']-scores['fixed180'])[selected],28,2000 if league=='E1' else 10000)}
 if league=='E0':
  saved=list(csv.DictReader((ROOT/'experiments/results/e0_transfer/predictions.csv').open()));assert len(saved)==len(records)
  maxerr=0
  for i,(r,t) in enumerate(zip(records,saved)):
   assert (str(date.fromordinal(r['date'])),r['home'],r['away'],r['venue'],str(r['actual']))==(t['date'],t['home'],t['away'],t['venue'],t['actual'])
   for a,b in [('mu','fixed180_mean'),('alpha','dispersion'),('s','signed_strength')]:maxerr=max(maxerr,abs(r[a]-float(t[b])))
   for name in means:maxerr=max(maxerr,abs(means[name][i]-float(t[name+'_mean'])))
  report['max_saved_row_difference']=maxerr
  late=seasons>=2023;report['post_training']={n:float(sc[late].mean()) for n,sc in scores.items()};report['post_training_ci']=bootstrap(dt[late],(scores['joint']-scores['fixed180'])[late],28,10000)
  report['sensitivity']={str(w):bootstrap(dt,scores['joint']-scores['fixed180'],w,10000) for w in [14,56]}
 else:
  oldrows=list(csv.DictReader((ROOT/'experiments/results/market_strength_diagnostic/predictions.csv').open()));evalrecords=[(i,r) for i,r in enumerate(records) if selected[i]];assert len(oldrows)==len(evalrecords)
  report['max_saved_baseline_difference']=max(abs(r['mu']-float(t['baseline_mean'])) for (_,r),t in zip(evalrecords,oldrows))
  report['bands']={}
  for band,bm in [('lt4',mu<4),('ge6',mu>=6)]:
   z=selected&bm;report['bands'][band]={'n':int(z.sum()),'bias':{n:float((y-m)[z].mean()) for n,m in means.items()}}
 # Persist reviewer derived records, not model source or repository artifacts.
 np.savez(args.output_dir/('deepfc-review-'+league+'.npz'),dates=dt,y=y,mu=mu,s=s,alpha=alpha,venue=v,seasons=seasons,selected=selected,**{'mean_'+n:m for n,m in means.items()},**{'brier_'+n:sc for n,sc in scores.items()})
 output[league]=report
 print(league,json.dumps(report,indent=2),flush=True)
(args.output_dir/'results.json').write_text(json.dumps(output,indent=2))
print('TRAINING',output['training_certificate'])
