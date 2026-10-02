"""Variance-only planning from previously inspected forecasts; no model fitting."""
import csv,json,math,hashlib
from pathlib import Path
from collections import defaultdict
from datetime import date
import numpy as np
from scipy.stats import norm
SOURCE=Path('experiments/results/market_strength_diagnostic/predictions.csv')
OUT=Path('experiments/results/power_planning')

def cluster_stats(values,days,width):
    x=np.asarray(values,float);n=len(x);groups=defaultdict(list)
    for i,d in enumerate(days):groups[d.toordinal()//width].append(i)
    counts=np.array([len(ix) for ix in groups.values()]);sums=np.array([x[ix].sum() for ix in groups.values()]);g=len(counts)
    centered=sums-counts*x.mean()
    se=math.sqrt(g/(g-1)*sum(centered**2))/n
    rng=np.random.default_rng(7);ix=rng.integers(g,size=(10000,g))
    # Descriptive variability of estimated variance, not a guarantee under drift.
    ns=counts[ix].sum(axis=1);means=sums[ix].sum(axis=1)/ns
    ss=((sums[ix]-counts[ix]*means[:,None])**2).sum(axis=1)
    scales=np.sqrt(g/(g-1)*ss/ns)
    return {'n':n,'blocks':g,'se':se,'sigma_effective':se*math.sqrt(n),'sigma_resample_p025_p975':np.quantile(scales,[.025,.975]).tolist()}

def needed(sigma,gap,power,z=norm.ppf(.975)):
    return None if gap<=0 else math.ceil(((z+norm.ppf(power))*sigma/gap)**2)

def power(sigma,n,gap):return float(norm.cdf(gap*math.sqrt(n)/sigma-norm.ppf(.975)))

def run():
    rows=list(csv.DictReader(SOURCE.open()));fixtures=defaultdict(list)
    for r in rows:fixtures[r['date'],r['home'],r['away']].append(r)
    assert all(len(v)==2 and {r['venue'] for r in v}=={'home','away'} for v in fixtures.values())
    pairs=list(fixtures.values());days=[date.fromisoformat(v[0]['date']) for v in pairs]
    loss=[sum(float(r['brier_delta']) for r in v)/2 for v in pairs]
    blocks={str(w):cluster_stats(loss,days,w) for w in [14,28,56]}
    sig=blocks['28']['sigma_effective']
    cases={f'blocks_{w}':v['sigma_effective'] for w,v in blocks.items()}
    cases.update(variance_x2=sig*math.sqrt(2),variance_x4=sig*2)
    joint=json.loads(Path('experiments/results/joint_market_calibration/results.json').read_text())
    ci=joint['comparisons']['fixed180']['all']['diagnostic']['ci95']['brier_delta']
    cases['joint_candidate_CI_proxy']=(ci[1]-ci[0])/3.92*math.sqrt(len(pairs))
    scenarios=[]
    for name,sigma in cases.items():
        for margin in [0,.001]:
            for gain in [.0005,.001,.0015,.002,.003,.005]:
                scenarios.append({'variance_case':name,'margin':margin,'true_gain':gain,'n80':needed(sigma,gain-margin,.8),'n90':needed(sigma,gain-margin,.9),
                 'power_by_full_seasons_90pct_usable':{str(y):power(sigma,math.floor(552*.9*y),gain-margin) for y in [1,2,3,5,10]}})
    seasonal={}
    for year in ['2023','2024','2025']:
        ix=[i for i,v in enumerate(pairs) if v[0]['season']==year]
        seasonal[year]=cluster_stats([loss[i] for i in ix],[days[i] for i in ix],28)
    # Expected subgroup means are ratios; center by subgroup mean and
    # cluster influence per fixture, scaling in total eligible fixtures.
    def ratio_scale(field,predicate):
        vals=[[float(r[field]) for r in v if predicate(r)] for v in pairs]
        count=sum(map(len,vals));mean=sum(map(sum,vals))/count
        influence=np.array([sum(v)-len(v)*mean for v in vals])*len(pairs)/count
        return count,cluster_stats(influence,days,28)['sigma_effective']
    z_one=norm.ppf(1-.05/15);z_two=norm.ppf(1-.05/(2*15));secondary={}
    for venue in ['home','away']:
        for line in [3.5,4.5,5.5,6.5]:
            n,s=ratio_scale(f'over{line}_candidate_error',lambda r:r['venue']==venue)
            # At true calibration error0, two-sided equivalence pass requires
            # both tails; normal symmetry gives z_(1+power)/2.
            secondary[f'calibration/{venue}/{line}']={'observations':n,'sigma_effective':s,'epsilon':.02,
                'fixtures_80':math.ceil(((z_two+norm.ppf(.9))*s/.02)**2),'fixtures_90':math.ceil(((z_two+norm.ppf(.95))*s/.02)**2)}
    for label,predicate,field,margin in [('NLL',lambda r:True,'nll_delta',.005),
        ('Brier/home',lambda r:r['venue']=='home','brier_delta',.001),('Brier/away',lambda r:r['venue']=='away','brier_delta',.001),
        ('Brier/lt4',lambda r:r['band']=='lt4','brier_delta',.001),('Brier/ge6',lambda r:r['band']=='ge6','brier_delta',.001)]:
        n,s=ratio_scale(field,predicate);secondary[label]={'observations':n,'sigma_effective':s,'margin':margin,
            'fixtures_80':needed(s,margin,.8,z_one),'fixtures_90':needed(s,margin,.9,z_one)}
    result={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'fixture_n':len(pairs),'team_n':len(rows),
      'observed_mean_not_assumed_future_gain':float(np.mean(loss)),'blocks':blocks,'seasonal_variance':seasonal,'sigma_cases':cases,
      'scenarios':scenarios,'secondary_K15_at_zero_error_or_zero_harm':secondary,
      'notes':'Normal-approximation planning, conditional on frozen-model loss variability; no new fit or future power guarantee. Secondary per-check powers are not joint safety power.'}
    (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'blocks':blocks,'sigma_cases':cases,'secondary':secondary},indent=2))

if __name__=='__main__':run()
