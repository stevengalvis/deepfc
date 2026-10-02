"""Post-hoc diagnosis of a saved frozen candidate; never estimates coefficients."""
import csv
import hashlib
import json
import random
from collections import defaultdict
from datetime import date
from pathlib import Path
import numpy as np
from deepfc.corner_distribution import negative_binomial_negative_log_loss, negative_binomial_over_probability
from deepfc.football_data_csv import load_football_data_csv
from deepfc.team_corners import TEAM_CORNER_LINES, evaluate_predictions
from experiments.market_strength import CUTOFF, adjust, key, load_features
from experiments.time_decay import compare_models

OUT = Path('experiments/results/market_strength_diagnostic')

def band(mu):
    return 'lt4' if mu < 4 else '4to6' if mu < 6 else 'ge6'

def strength_bin(s):
    return 'strong_underdog' if s < -.25 else 'mild_underdog' if s < 0 else 'mild_favourite' if s < .25 else 'strong_favourite'

def bootstrap(rows, names):
    """Original equal-probability block resampling, jointly across columns."""
    blocks = defaultdict(list)
    for r in rows:
        blocks[date.fromisoformat(r['date']).toordinal() // 28].append([r[k] for k in names])
    sizes = np.array([len(v) for v in blocks.values()])
    totals = np.array([np.sum(v, axis=0) for v in blocks.values()])
    rng = random.Random(7)
    weights = np.array([np.bincount(rng.choices(range(len(sizes)), k=len(sizes)), minlength=len(sizes)) for _ in range(2000)])
    draws = (weights @ totals) / (weights @ sizes)[:, None]
    return draws, len(sizes)

def ci(values):
    values = np.sort(values)
    return [float(values[int(.025*(len(values)-1))]), float(values[int(.975*(len(values)-1))])]

def summarize(rows):
    names = [k for k,v in rows[0].items() if isinstance(v, (int,float)) and k != 'season']
    draws, blocks = bootstrap(rows, names)
    means = {k: float(np.mean([r[k] for r in rows])) for k in names}
    b, a = names.index('baseline_bias'), names.index('candidate_bias')
    return {'n':len(rows), 'blocks':blocks, 'means':means,
            'ci95':{k:ci(draws[:,i]) for i,k in enumerate(names)},
            'bias_gate_margin':abs(means['candidate_bias'])-.5*abs(means['baseline_bias']),
            'bias_gate_margin_ci95':ci(abs(draws[:,a])-.5*abs(draws[:,b]))}

def observation(b, a, s, season, beta):
    assert (b.match,b.venue,b.actual_corners,b.dispersion)==(a.match,a.venue,a.actual_corners,a.dispersion)
    mu=b.expected_corners; changed=a.expected_corners; y=b.actual_corners
    row={'date':str(b.match.match_date),'home':b.match.home_team,'away':b.match.away_team,
         'venue':b.venue,'season':season,'period':'validation' if b.match.match_date<date(2024,7,1) else 'test',
         'band':band(mu),'strength_bin':strength_bin(s),'strength':s,'actual':y,'baseline_mean':mu,'candidate_mean':changed,
         'baseline_bias':y-mu,'candidate_bias':y-changed,'bias_delta':mu-changed,
         'mean_shift':changed-mu,'linear_shift':beta*mu*s,'convexity_shift':changed-mu-beta*mu*s,
         'nll_derivative_at_beta':s*(changed-y)/(1+b.dispersion*changed),
         'mae_delta':abs(y-changed)-abs(y-mu),
         'nll_delta':negative_binomial_negative_log_loss(y,changed,b.dispersion)-negative_binomial_negative_log_loss(y,mu,b.dispersion)}
    losses=[]
    for line in TEAM_CORNER_LINES:
        pb=b.over_probabilities[line];pa=a.over_probabilities[line];hit=float(y>line)
        row[f'over{line}_baseline_error']=hit-pb;row[f'over{line}_candidate_error']=hit-pa
        losses.append((pa-hit)**2-(pb-hit)**2)
    row['brier_delta']=sum(losses)/len(losses)
    for name,line in [('low_tail',1.5),('high_tail',9.5)]:
        pb=negative_binomial_over_probability(mu,line,b.dispersion);pa=negative_binomial_over_probability(changed,line,b.dispersion)
        if name=='low_tail':pb=1-pb;pa=1-pa;hit=float(y<=1)
        else:hit=float(y>=10)
        row[name+'_observed']=hit;row[name+'_baseline_probability']=pb;row[name+'_candidate_probability']=pa
        row[name+'_baseline_error']=hit-pb;row[name+'_candidate_error']=hit-pa
        row[name+'_brier_delta']=(pa-hit)**2-(pb-hit)**2
    return row

def standardized(rows):
    """Pooled venue/strength-cell weights shared across seasons, common support."""
    result={}
    for label in ['lt4','4to6','ge6']:
        selected=[r for r in rows if r['band']==label]
        cells=defaultdict(list)
        for r in selected:cells[r['season'],r['venue'],r['strength_bin']].append(r)
        strata=sorted({(r['venue'],r['strength_bin']) for r in selected})
        common=[s for s in strata if all((y,*s) in cells for y in [2023,2024,2025])]
        counts={s:sum(len(cells[y,*s]) for y in [2023,2024,2025]) for s in common}
        total=sum(counts.values());weights={s:n/total for s,n in counts.items()}
        result[label]={'common_support_n':total,'total_n':len(selected),'common_cells':len(common),'seasons':{}}
        for year in [2023,2024,2025]:
            result[label]['seasons'][str(year)]={name:sum(weights[s]*np.mean([r[name] for r in cells[year,*s]]) for s in common) for name in ['baseline_bias','candidate_bias','mean_shift','strength','brier_delta']}
    return result

def run():
    original=json.loads(Path('experiments/results/market_strength/results.json').read_text())
    for p,k in [('experiments/market_strength.py','code_sha256'),('experiments/market_strength_spec.md','spec_sha256')]:
        assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==original[k]
    paths=[Path(p) for p in sorted(original['source_hashes'])]
    for p in paths:assert hashlib.sha256(p.read_bytes()).hexdigest()==original['source_hashes'][str(p)]
    seasons={m:2000+int(p.stem.split('_')[1][:2]) for p in paths for m in load_football_data_csv([p]).matches}
    features,excluded=load_features(paths);assert not excluded
    baseline=[p for p in compare_models(load_football_data_csv(paths).matches).time_weighted if p.match.match_date>=CUTOFF and key(p.match) in features]
    beta=original['beta'];candidate=[adjust(p,features[key(p.match)],beta) for p in baseline]
    for period in ['validation','test','combined_later']:
        for side,values in [('baseline',baseline),('candidate',candidate)]:
            subset=[p for p in values if period=='combined_later' or (p.match.match_date<date(2024,7,1))==(period=='validation')]
            metrics=evaluate_predictions(subset);expected=original['periods'][period]['overall'][side]
            for k in ['evaluated_team_observations','mean_predicted_corners','mean_actual_corners','mae','rmse','negative_binomial_negative_log_loss','mean_brier_score']:
                assert abs(metrics[k]-expected[k])<1e-12,(period,side,k)
    rows=[observation(b,a,features[key(b.match)]*(1 if b.venue=='home' else -1),seasons[b.match],beta) for b,a in zip(baseline,candidate,strict=True)]
    groups=defaultdict(list)
    for r in rows:
        for fields in [(),('period',),('season',),('venue',),('band',),('strength_bin',),('band','season'),('band','venue'),('band','strength_bin'),('band','season','venue')]:
            name='/'.join(f'{f}={r[f]}' for f in fields) or 'all'
            groups[name].append(r)
    result={'source_commit':'13116f9ab650f23275bdb28b645678fea7e192f3','saved_beta':beta,'coefficient_refitted':False,
            'checks':'All source/code/spec hashes and all saved period aggregate metrics match within 1e-12; pairing exact.',
            'groups':{k:summarize(v) for k,v in groups.items()},'composition_standardization':standardized(rows),
            'original_gates':original['gates'],'original_decision':original['decision']}
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'predictions.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['checks']);print(f'{len(rows)} observations; {len(groups)} slices; no coefficient fitted.')

if __name__=='__main__':run()
