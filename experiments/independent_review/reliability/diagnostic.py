from pathlib import Path
import json,csv,hashlib,sys,platform
import numpy as np
from scipy.stats import nbinom,rankdata
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
NBOOT=20000
EDGES=np.linspace(0,1,6)
manifest={'commit':'7e8ad0acdcea13f5778e107882c36e5d6922fbd3','python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__,'inputs':{}}
for f in ['protocol.txt','deepfc-review-E1.npz','deepfc-review-E0.npz']:
 manifest['inputs'][f]=hashlib.sha256((ROOT/f).read_bytes()).hexdigest()
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2))
curves=[];overall=[];decomp=[];allresults={}
def aggregate(values,ids,weights):
 sums=np.zeros((weights.shape[1],values.shape[1]));np.add.at(sums,ids,values)
 return weights@sums

def boot_context(dates,width):
 blocks,ids=np.unique(dates//width,return_inverse=True);g=len(blocks)
 # Multinomial block counts implement equal-probability sampling of g blocks with replacement.
 weights=np.random.default_rng(7).multinomial(g,np.full(g,1/g),size=NBOOT)
 return blocks,ids,weights

def ci(vals,adjusted=False):
 good=vals[np.isfinite(vals)]
 if len(good)<.99*len(vals):return None
 q=.05/(2*16) if adjusted else .025
 return np.quantile(good,[q,1-q]).tolist()

for cohort,league,later in [('E1_later','E1',True),('E0_post_training','E0',True),('E0_full_history','E0',False)]:
 data=np.load(ROOT/f'deepfc-review-{league}.npz');ix=data['selected'].copy()
 if later:ix &= data['seasons']>=2023
 dates=data['dates'][ix];venue=data['venue'][ix];y=data['y'][ix];alpha=data['alpha'][ix];r=1/alpha
 assert len(y)%2==0 and np.array_equal(venue[::2],np.repeat('home',len(y)//2)) and np.array_equal(venue[1::2],np.repeat('away',len(y)//2))
 models={name:nbinom.sf(np.arange(3,7)[None,:],r[:,None],(r/(r+data['mean_'+name][ix]))[:,None]) for name in ['fixed180','joint']}
 blocks,ids,weights=boot_context(dates,28)
 context={'n_team':len(y),'n_fixtures':len(y)//2,'blocks':len(blocks),'dates':[int(dates.min()),int(dates.max())]};allresults[cohort]=context
 columns=[];metadata=[]
 for v in ['home','away']:
  vm=venue==v
  for l in range(4):
   obs=(y>l+3).astype(float)
   for name,ps in models.items():
    p=ps[:,l];bins=np.minimum((p*5).astype(int),4)
    for b in [-1,0,1,2,3,4]:
     z=vm if b==-1 else vm&(bins==b)
     columns.extend([z.astype(float),np.where(z,p,0),np.where(z,obs,0),np.where(z,obs-p,0)])
     metadata.append((v,l+3.5,name,b,z,p,obs))
    yy=obs[vm];pp=p[vm];bb=bins[vm];unc=yy.mean()*(1-yy.mean());rel=res=rem=0.
    for b in range(5):
     z=bb==b
     if not z.any():continue
     weight=z.mean();pb=pp[z].mean();yb=yy[z].mean();rel+=weight*(pb-yb)**2;res+=weight*(yb-yy.mean())**2
     rem+=weight*((pp[z]-pb)**2-2*(pp[z]-pb)*(yy[z]-yb)).mean()
    bs=((pp-yy)**2).mean();assert abs(bs-(unc-res+rel+rem))<1e-12
    ranks=rankdata(pp);n1=yy.sum();n0=len(yy)-n1;auc=(ranks[yy==1].sum()-n1*(n1+1)/2)/(n1*n0)
    decomp.append({'cohort':cohort,'venue':v,'line':l+3.5,'model':name,'brier':float(bs),'uncertainty':float(unc),'reliability_binned':float(rel),'resolution_binned':float(res),'within_bin_remainder':float(rem),'coarsened_brier':float(unc-res+rel),'auc':float(auc)})
 totals=aggregate(np.column_stack(columns),ids,weights)
 for j,(v,line,name,b,z,p,obs) in enumerate(metadata):
  n=int(z.sum());blockn=len(np.unique(ids[z]));t=totals[:,4*j:4*j+4]
  with np.errstate(invalid='ignore',divide='ignore'):draws=t[:,1:]/t[:,0,None]
  entry={'cohort':cohort,'venue':v,'line':line,'model':name,'bin':'all' if b==-1 else f'{b/5:.1f}-{(b+1)/5:.1f}','n':n,'fixtures':n,'blocks':blockn,'mean_predicted':float(p[z].mean()) if n else None,'observed_rate':float(obs[z].mean()) if n else None,'error_observed_minus_predicted':float((obs-p)[z].mean()) if n else None,'predicted_ci95':ci(draws[:,0]),'observed_ci95':ci(draws[:,1]),'error_ci95':ci(draws[:,2]),'undefined_fraction':float(np.mean(t[:,0]==0)),'sparse':n<100 or blockn<10}
  if b==-1:
   entry['joint_primary_family_ci']=ci(draws[:,2],True) if name=='joint' and later else None
   overall.append(entry)
  else:curves.append(entry)
 # CITL sensitivity reuses complete cohorts at different block widths.
 for width in [14,56]:
  _,wid,w=boot_context(dates,width);col=[];meta=[]
  for v in ['home','away']:
   vm=venue==v
   for l in range(4):
    for name,ps in models.items():col.extend([vm.astype(float),np.where(vm,(y>l+3)-ps[:,l],0)]);meta.append((v,l+3.5,name))
  t=aggregate(np.column_stack(col),wid,w)
  for j,(v,line,name) in enumerate(meta):
   row=next(x for x in overall if (x['cohort'],x['venue'],x['line'],x['model'])==(cohort,v,line,name));row[f'error_ci95_{width}day']=ci(t[:,2*j+1]/t[:,2*j])
 # 2x4 curves; error intervals plotted around observed rates at fixed mean prediction.
 fig,axes=plt.subplots(2,4,figsize=(16,8),sharex=True,sharey=True)
 for vi,v in enumerate(['home','away']):
  for li,line in enumerate([3.5,4.5,5.5,6.5]):
   ax=axes[vi,li];ax.plot([0,1],[0,1],color='#999999',lw=1,ls='--')
   for name,color,marker in [('fixed180','#667085','s'),('joint','#087f8c','o')]:
    rs=[x for x in curves if (x['cohort'],x['venue'],x['line'],x['model'])==(cohort,v,line,name) and x['n']]
    ax.plot([x['mean_predicted'] for x in rs],[x['observed_rate'] for x in rs],color=color,alpha=.45,lw=1)
    for row in rs:
     px=row['mean_predicted'];oy=row['observed_rate'];interval=row['error_ci95'];sparse=row['sparse']
     if interval:
      lo,hi=np.array(interval)+px;ax.vlines(px,lo,hi,color=color,lw=1,alpha=.35 if sparse else .85)
     ax.scatter(px,oy,s=32,marker=marker,edgecolor=color,facecolor='white' if sparse else color,zorder=3)
     ax.annotate(str(row['n']),(px,oy),xytext=(3,5 if name=='joint' else -11),textcoords='offset points',fontsize=7,color=color)
   ax.set_title(f'{v.title()} · over {line}');ax.set_xlim(0,1);ax.set_ylim(0,1);ax.grid(alpha=.15)
   if li==0:ax.set_ylabel('Observed event rate')
   if vi==1:ax.set_xlabel('Mean predicted probability')
 fig.suptitle(cohort.replace('_',' ')+' — fixed180 gray squares; joint teal circles',fontsize=15)
 fig.text(.5,.012,'Labels: observations. Hollow: sparse (<100 observations or <10 blocks). Bars: pointwise 95% calendar-block intervals for observed−predicted, translated by mean prediction.\nFive fixed 20-point bins; model-specific memberships. Historical exploratory evidence; no refitting.',ha='center',fontsize=9)
 fig.tight_layout(rect=[0,.065,1,.95]);fig.savefig(ROOT/f'{cohort}_reliability.png',dpi=160);fig.savefig(ROOT/f'{cohort}_reliability.pdf');plt.close(fig)
 print(cohort,'complete',flush=True)

out={'contexts':allresults,'overall':overall,'curves':curves,'decomposition':decomp}
(ROOT/'results.json').write_text(json.dumps(out,indent=2,allow_nan=False))
for name,rows in [('overall',overall),('reliability_bins',curves),('brier_decomposition',decomp)]:
 fields=list(dict.fromkeys(k for row in rows for k in row))
 with (ROOT/(name+'.csv')).open('w') as f:
  writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
(ROOT/'execution.json').write_text(json.dumps({'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'bootstrap_draws':NBOOT,'seed':7,'decomposition_identity_max_error':max(abs(x['brier']-(x['uncertainty']-x['resolution_binned']+x['reliability_binned']+x['within_bin_remainder'])) for x in decomp)},indent=2))
