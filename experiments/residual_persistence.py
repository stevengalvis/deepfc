"""Frozen association diagnostic; never emits corrected model predictions."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import date
from itertools import groupby
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t

from experiments.distribution_blend import e1_inputs
from experiments.goal_total_extension import load_quotes
from experiments.joint_market_calibration import design
from experiments.market_strength import key

OUT = Path('experiments/results/residual_persistence')
SPEC = Path('experiments/residual_persistence_spec.md')


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def inputs(phase):
    quotes, _ = load_quotes()
    rows = []
    if phase == 'discovery':
        ps, features, seasons = e1_inputs()
        selected = json.loads(Path('experiments/results/distribution_blend/selection.json').read_text())
        folds = {f['source_season']: f for f in selected['folds']}
        for p in ps:
            year = seasons[p.match]
            if year not in folds or key(p.match) not in features:
                continue
            fold = folds[year]
            assert date.fromisoformat(fold['certificate']['latest_training_date']) < date(year, 7, 1) <= p.match.match_date
            s = features[key(p.match)] * (1 if p.venue == 'home' else -1)
            joint = float(p.expected_corners * np.exp(np.dot(design(p, s), fold['theta'])))
            rows.append(dict(league='E1', date=str(p.match.match_date), home=p.match.home_team, away=p.match.away_team,
                             venue=p.venue, season=year, actual=p.actual_corners, baseline_mean=p.expected_corners, joint_mean=joint))
    else:
        for r in csv.DictReader(Path('experiments/results/distribution_blend/predictions.csv').open()):
            rows.append(dict(league=r['league'], date=r['date'], home=r['home'], away=r['away'], venue=r['venue'],
                             season=int(r['season']), actual=int(r['actual']), baseline_mean=float(r['baseline_mean']),
                             joint_mean=float(r['component_mean'])))
    for r in rows:
        q, s = quotes[(r['league'], r['date'], r['home'], r['away'])]
        r['strength'] = s * (1 if r['venue'] == 'home' else -1)
        r['goal_probability'] = q
        r['team'] = r[r['venue']]
        r['opponent'] = r['away' if r['venue'] == 'home' else 'home']
    return rows


def past_features(rows):
    """Batch dates; both scoring and conceding histories are strictly past."""
    attack = defaultdict(list); concede = defaultdict(list)
    output = []; rejected = defaultdict(int)
    rows = sorted(rows, key=lambda r: (r['date'], r['league'], r['home'], r['away'], r['venue']))
    for when, batch in groupby(rows, key=lambda r: r['date']):
        batch = list(batch); ordinal = date.fromisoformat(when).toordinal()
        for r in batch:
            prefix = (r['league'], r['season'])
            ah = attack[(*prefix, r['team'])]; ch = concede[(*prefix, r['opponent'])]
            label = r['league'] + '/' + str(r['season'])
            if min(len(ah), len(ch)) < 20:
                rejected[label + '/fewer_than_20'] += 1; continue
            if any(ordinal - date.fromisoformat(h[-20]['date']).toordinal() > 180 for h in (ah, ch)):
                rejected[label + '/span_over_180_days'] += 1; continue
            row = dict(r)
            for channel, history in [('attack', ah), ('concession', ch)]:
                recent, older = history[-5:], history[-20:-5]
                row[channel + '_history_n'] = len(history)
                row[channel + '_earliest_date'] = older[0]['date']
                row[channel + '_latest_date'] = recent[-1]['date']
                assert all(h['date'] < when for h in recent + older)
                for label2, part in [('recent', recent), ('older', older)]:
                    row[channel + '_' + label2 + '_home_fraction'] = float(np.mean([h['venue'] == 'home' for h in part]))
                    for model in ['baseline', 'joint']:
                        row[model + '_' + channel + '_' + label2] = float(np.mean([h['actual'] - h[model + '_mean'] for h in part]))
                for model in ['baseline', 'joint']:
                    row[model + '_' + channel + '_change'] = row[model + '_' + channel + '_recent'] - row[model + '_' + channel + '_older']
            output.append(row)
        # No outcomes from this date can enter any feature above.
        for r in batch:
            prefix = (r['league'], r['season'])
            attack[(*prefix, r['team'])].append(r)
            concede[(*prefix, r['opponent'])].append(r)
    return output, dict(rejected)


def clustered_interval(X, residual, bread, beta, memberships, df, correction):
    scores = X * residual[:, None]
    meat = np.zeros((X.shape[1], X.shape[1]))
    counts = []
    for sign, groups in memberships:
        totals = defaultdict(lambda: np.zeros(X.shape[1]))
        for group, score in zip(groups, scores):
            # group can be two team memberships, but only one pair or block.
            for item in group: totals[item] += score
        matrix = np.array(list(totals.values()))
        meat += sign * matrix.T @ matrix
        counts.append(len(totals))
    covariance = correction * bread @ meat @ bread
    result = []
    for i in range(2):
        variance = float(covariance[i, i])
        if variance < 0:
            result.append({'ci95': None, 'negative_variance': variance}); continue
        se = math_sqrt(variance)
        radius = float(student_t.ppf(.975, df)) * se
        result.append({'se': se, 'ci95': [float(beta[i] - radius), float(beta[i] + radius)]})
    return {'group_counts': counts, 'df': df, 'effects': result}


def math_sqrt(v):
    return float(np.sqrt(max(0., v)))


def regression(rows, model, mode):
    n = len(rows)
    if n < 200: return {'status': 'insufficient n', 'n': n}
    suffix = 'recent' if mode == 'raw' else 'change'
    focus = np.array([[r[model + '_' + c + '_' + suffix] for c in ['attack', 'concession']] for r in rows])
    controls = [np.ones(n), np.array([r['venue'] == 'home' for r in rows], dtype=float)]
    for year in sorted({r['season'] for r in rows})[1:]: controls.append(np.array([r['season'] == year for r in rows], dtype=float))
    if mode != 'raw':
        for c in ['attack', 'concession']: controls.append(np.array([r[model + '_' + c + '_older'] for r in rows]))
        log_mu = np.log([r['baseline_mean'] / 5 for r in rows]); s = np.array([r['strength'] for r in rows])
        controls.extend([log_mu, log_mu**2, s, s**2, np.array([r['goal_probability'] - .5 for r in rows])])
        for c in ['attack', 'concession']:
            for period in ['recent', 'older']: controls.append(np.array([r[c + '_' + period + '_home_fraction'] for r in rows]))
    if mode == 'team_effects':
        for role in ['team', 'opponent']:
            for team in sorted({r[role] for r in rows})[1:]: controls.append(np.array([r[role] == team for r in rows], dtype=float))
    # SVD removes nuisance-only collinearity (e.g. venue intercept in venue subsets).
    C = np.array(controls).T
    U, singular, _ = np.linalg.svd(C, full_matrices=False)
    rank = int(np.sum(singular > singular[0] * 1e-10)); C = U[:, :rank]
    Z = focus - C @ (C.T @ focus)
    if np.linalg.matrix_rank(Z, tol=1e-9) < 2: return {'status': 'focus not identified', 'n': n}
    y = np.array([r['actual'] - r[model + '_mean'] for r in rows])
    X = np.column_stack([focus, C])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]; residual = y - X @ beta
    bread = np.linalg.inv(X.T @ X)
    base_error = y - C @ (C.T @ y)
    partial = 1 - float(residual @ residual / (base_error @ base_error))
    uncertainty = {}
    for width in [84, 168]:
        groups = [(date.fromisoformat(r['date']).toordinal() // width,) for r in rows]
        G = len(set(groups))
        uncertainty[str(width) + '_day'] = clustered_interval(X, residual, bread, beta, [(1, groups)], G - 1, G/(G-1)*(n-1)/(n-X.shape[1])) if G > 1 else None
    teams = [(r['team'], r['opponent']) for r in rows]
    pairs = [(tuple(sorted(x)),) for x in teams]; G = len(set(t for pair in teams for t in pair))
    uncertainty['dyadic_team'] = clustered_interval(X, residual, bread, beta, [(1, teams), (-1, pairs)], G - 1, G/(G-1)*(n-1)/(n-X.shape[1]))
    return {'status': 'ok', 'n': n, 'fixtures': len({(r['date'], r['home'], r['away']) for r in rows}),
            'design_rank': X.shape[1], 'attack_slope': float(beta[0]), 'concession_slope': float(beta[1]),
            'attack_feature_sd': float(np.std(focus[:, 0])), 'concession_feature_sd': float(np.std(focus[:, 1])),
            'partial_r_squared_in_sample': partial, 'mean_residual': float(y.mean()), 'residual_sd': float(y.std()), 'uncertainty': uncertainty}


def run(phase):
    if phase == 'validation':
        frozen = json.loads((OUT / 'discovery.json').read_text())
        assert frozen['code_sha256'] == digest(__file__) and frozen['spec_sha256'] == digest(SPEC)
    raw = inputs(phase); rows, rejected = past_features(raw)
    groups = defaultdict(list)
    for r in rows:
        league = r['league']
        era = 'through_May2023' if r['date'] <= '2023-05-31' else 'after_May2023'
        for label in [league, league + '/season=' + str(r['season']), league + '/venue=' + r['venue'], league + '/era=' + era]: groups[label].append(r)
    results = {label: {model: {mode: regression(part, model, mode) for mode in ['raw', 'controlled', 'team_effects']} for model in ['baseline', 'joint']} for label, part in groups.items()}
    out = {'phase': phase, 'code_sha256': digest(__file__), 'spec_sha256': digest(SPEC), 'input_n': len(raw), 'eligible_n': len(rows),
           'exclusions': rejected, 'groups': results, 'note': 'OLS association only; no corrected corner distribution or candidate forecasts.'}
    (OUT / (phase + '.json')).write_text(json.dumps(out, indent=2) + '\n')
    with (OUT / (phase + '_rows.csv')).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
    print(phase, len(raw), 'input,', len(rows), 'eligible')
    for label in ['E1', 'E0', 'E0/era=after_May2023']:
        if label in results:
            for model in ['baseline', 'joint']:
                for mode, x in results[label][model].items():
                    print(label, model, mode, x['n'], x.get('attack_slope'), x.get('concession_slope'), x.get('partial_r_squared_in_sample'), x.get('uncertainty', {}).get('84_day'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['discovery', 'validation'])
    run(parser.parse_args().phase)
