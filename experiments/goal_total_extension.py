"""One predeclared goal-total probability extension; no feature/penalty search."""
import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
from scipy.special import expit

from deepfc.football_data_csv import _parse_date
from experiments.distribution_blend import e1_inputs, row_metrics
from experiments.e0_transfer import summary
from experiments.joint_market_calibration import design, fit as fit_joint
from experiments.joint_strength import solve_newton
from experiments.market_strength import key, strength

OUT = Path('experiments/results/goal_total_extension')
SPEC = Path('experiments/goal_total_extension_spec.md')
CUTOFF = date(2023, 7, 1)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def goal_probability(row):
    # Explicit whitelist: never substitute closing, max or bookmaker fields.
    over, under = (float(row[k]) for k in ('Avg>2.5', 'Avg<2.5'))
    if not all(math.isfinite(x) and x > 1 for x in (over, under)):
        raise ValueError('finite decimal odds >1 required')
    return (1 / over) / (1 / over + 1 / under)


def sources():
    e1 = json.loads(Path('experiments/results/market_strength/results.json').read_text())
    for p, sha in sorted(e1['source_hashes'].items()):
        yield 'E1', 2000 + int(Path(p).stem.split('_')[1][:2]), Path(p), sha
    inv = json.loads(Path('experiments/results/e0_feasibility/inventory.json').read_text())
    for f in inv['files']:
        yield 'E0', int(f['season'][:4]), Path('/workspace/shot-data-mirror-liam') / f['path'], f['sha256']


def load_quotes():
    quotes = {}
    records = []
    for league, year, path, sha in sources():
        assert digest(path) == sha, path
        reader = csv.DictReader(path.open(encoding='utf-8-sig'))
        fields = reader.fieldnames
        rows = list(reader)
        valid = []; invalid = []; seen = set()
        cols = ['Avg>2.5', 'Avg<2.5'] if year >= 2019 else ['BbAv>2.5', 'BbAv<2.5']
        for number, row in enumerate(rows, 2):
            identity = (league, str(_parse_date(row['Date'])), row['HomeTeam'].strip(), row['AwayTeam'].strip())
            assert row['Div'] == league and identity not in seen
            seen.add(identity)
            try:
                if year < 2019:
                    # Audit historical schema, but never feed it to the model.
                    p = goal_probability(dict(zip(['Avg>2.5', 'Avg<2.5'], [row[k] for k in cols])))
                else:
                    p = goal_probability(row)
                    s = strength(row)
                    assert identity not in quotes
                    quotes[identity] = (p, s)
                valid.append(p)
            except (KeyError, TypeError, ValueError) as error:
                invalid.append({'row': number, 'fixture': identity, 'reason': str(error)})
        records.append({'league': league, 'season': year, 'path': str(path), 'sha256': sha,
                        'rows': len(rows), 'columns': cols, 'columns_present': all(k in fields for k in cols),
                        'closing_columns_present': all(k in fields for k in ['AvgC>2.5', 'AvgC<2.5']),
                        'usable_pairs_and_1x2_if_2019plus': len(valid), 'invalid': invalid,
                        'probability_min': min(valid) if valid else None, 'probability_max': max(valid) if valid else None,
                        'use': 'feature' if year >= 2019 else 'corner warmup only'})
    return quotes, records


def audit():
    _, records = load_quotes()
    result = {'files': records, 'source_documentation': 'https://football-data.co.uk/data.php',
              'documentation_checked': '2026-10-02',
              'schema': 'BbAv Betbrain before 2019; Avg Oddsportal from 2019. Only 2019+ Avg fields modeled; AvgC never used.',
              'continuity_limit': 'Provider excludes Pinnacle from market averages from 2025-07-23 after stale public API odds; bookmaker pool is not constant.',
              'timing_limit': 'Documented pre-closing snapshots, not exact quote timestamps or a verified fixed pre-kickoff horizon.',
              'provenance': 'Existing pinned mirror files. E1 matches archived primary hashes; E0 lacks independent primary-hash verification.'}
    (OUT / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    for r in records:
        print(r['league'], r['season'], r['columns'], r['usable_pairs_and_1x2_if_2019plus'], '/', r['rows'])


def objective(theta, X, mu, y, alpha):
    eta = np.log(mu) + X @ theta
    pois = alpha <= 1e-12
    loss = np.empty(len(y)); score = np.empty(len(y)); curvature = np.empty(len(y))
    shape = 1 / alpha[~pois]; z = eta[~pois] - np.log(shape); p = expit(z)
    loss[~pois] = (y[~pois] + shape) * np.logaddexp(0, z) - y[~pois] * eta[~pois]
    score[~pois] = (y[~pois] + shape) * p - y[~pois]
    curvature[~pois] = (y[~pois] + shape) * p * (1 - p)
    m = np.exp(eta[pois]); loss[pois] = m - y[pois] * eta[pois]
    score[pois] = m - y[pois]; curvature[pois] = m
    return float(loss.sum() + .5 * theta @ theta), X.T @ score + theta, (X.T * curvature) @ X + np.eye(len(theta))


def feature_key(p):
    return (p.match.competition, str(p.match.match_date), p.match.home_team, p.match.away_team)


def extended_design(p, q):
    probability, s = q
    return design(p, s * (1 if p.venue == 'home' else -1)) + [probability - .5]


def fit(predictions, quotes, cutoff):
    train = [p for p in predictions if p.match.competition == 'E1' and p.match.match_date < cutoff and feature_key(p) in quotes]
    if not train:
        raise ValueError('no early Championship training data')
    X = np.array([extended_design(p, quotes[feature_key(p)]) for p in train])
    mu, y, alpha = (np.array([getattr(p, attr) for p in train]) for attr in ('expected_corners', 'actual_corners', 'dispersion'))
    def difference(theta, step):
        eta = np.log(mu) + X @ theta; delta = X @ step; pois = alpha <= 1e-12
        change = np.empty(len(y))
        change[pois] = np.exp(eta[pois]) * np.expm1(delta[pois]) - y[pois] * delta[pois]
        p = expit(eta[~pois] + np.log(alpha[~pois]))
        change[~pois] = (y[~pois] + 1 / alpha[~pois]) * np.log1p(p * np.expm1(delta[~pois])) - y[~pois] * delta[~pois]
        return float(change.sum() + theta @ step + .5 * step @ step)
    theta, cert = solve_newton(lambda t: objective(t, X, mu, y, alpha)[:2],
                              lambda t: objective(t, X, mu, y, alpha)[2], difference, np.zeros(5))
    xld = X.astype(np.longdouble)
    m = np.exp(np.log(mu.astype(np.longdouble)) + xld @ theta.astype(np.longdouble))
    a = alpha.astype(np.longdouble); a[a <= 1e-12] = 0
    gradient = xld.T @ ((m - y) / (1 + a * m)) + theta
    eig = np.linalg.eigvalsh(objective(theta, X, mu, y, alpha)[2])
    assert np.isfinite(theta).all() and max(abs(gradient)) < 1e-8 and min(eig) > 0
    cert.update(independent_gradient_max=float(max(abs(gradient))), hessian_min_eigenvalue=float(min(eig)),
                training_n=len(train), latest_training_date=str(max(p.match.match_date for p in train)), cutoff=str(cutoff))
    return theta, cert


def metrics(row, goal_mean):
    # Reuse independently tested NB metrics, not mixture-mean approximations.
    base = dict(date=row['date'], home=row['home'], away=row['away'], baseline_mean=row['baseline_mean'],
                component_mean=goal_mean, dispersion=row['dispersion'], actual=row['actual'])
    g = row_metrics(base, 1.)
    j = row_metrics(dict(base, component_mean=row['joint_mean']), 1.)
    out = dict(row, goal_mean=goal_mean)
    for name, result, prefix in [('fixed180', g, 'baseline_'), ('joint', j, 'component_'), ('goal', g, 'component_')]:
        for k, v in result.items():
            if k.startswith(prefix): out[name + '_' + k[len(prefix):]] = v
    for k, v in g.items():
        if k.endswith('_observed'): out[k] = v
    for ref in ['fixed180', 'joint']:
        for metric in ['brier', 'nll', 'mae', 'bias']:
            out['goal_minus_' + ref + '_' + metric] = out['goal_' + metric] - out[ref + '_' + metric]
    return out


def pred_row(p, season, joint_mean):
    return dict(league=p.match.competition, date=str(p.match.match_date), home=p.match.home_team,
                away=p.match.away_team, venue=p.venue, season=season, actual=p.actual_corners,
                dispersion=p.dispersion, baseline_mean=p.expected_corners, joint_mean=joint_mean)


def train():
    quotes, _ = load_quotes(); ps, features, seasons = e1_inputs()
    folds = []
    for year in [2021, 2022]:
        cutoff = date(year, 7, 1)
        theta, cert = fit(ps, quotes, cutoff)
        early = [p for p in ps if p.match.match_date < cutoff and feature_key(p) in quotes]
        joint, jc = fit_joint(early, features)
        rows = []
        for p in ps:
            if seasons[p.match] != year or feature_key(p) not in quotes: continue
            assert p.match.match_date >= cutoff
            x = extended_design(p, quotes[feature_key(p)])
            row = pred_row(p, year, float(p.expected_corners * np.exp(np.dot(x[:4], joint))))
            rows.append(metrics(row, float(p.expected_corners * np.exp(np.dot(x, theta)))))
        folds.append({'season': year, 'theta': theta.tolist(), 'certificate': cert,
                      'joint_theta': joint.tolist(), 'joint_certificate': dict(jc, effective_fold_cutoff=str(cutoff)),
                      'heldout': summary(rows)})
    theta, cert = fit(ps, quotes, CUTOFF)
    result = {'theta': theta.tolist(), 'coefficient_names': ['a_home', 'a_away', 'gamma_minus_one', 'beta_1x2', 'delta_goal'],
              'certificate': cert, 'early_temporal_folds': folds,
              'selection': 'One predeclared feature and unit penalty; folds descriptive only, no tuning or selection gate.',
              'spec_sha256': digest(SPEC), 'code_sha256': digest(__file__), 'audit_sha256': digest(OUT / 'audit.json')}
    (OUT / 'fit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'theta': result['theta'], 'certificate': cert}, indent=2))
    for f in folds: print('early fold', f['season'], {k: v for k, v in f['heldout']['means'].items() if k.startswith('goal_minus_joint')})


def evaluate():
    trained = json.loads((OUT / 'fit.json').read_text())
    assert digest(SPEC) == trained['spec_sha256'] and digest(__file__) == trained['code_sha256']
    assert digest(OUT / 'audit.json') == trained['audit_sha256']
    theta = np.array(trained['theta']); quotes, _ = load_quotes()
    rows = []; excluded = []; counts = defaultdict(int)
    for r in csv.DictReader(Path('experiments/results/distribution_blend/predictions.csv').open()):
        league = r['league']; counts[league] += 1
        k = (league, r['date'], r['home'], r['away'])
        if k not in quotes:
            excluded.append([*k, r['venue']]); continue
        q, s = quotes[k]; b = float(r['baseline_mean'])
        x = [float(r['venue'] == 'home'), float(r['venue'] == 'away'), np.log(b / 5), s * (1 if r['venue'] == 'home' else -1), q - .5]
        row = dict(league=league, date=r['date'], home=r['home'], away=r['away'], venue=r['venue'], season=int(r['season']),
                   actual=int(r['actual']), dispersion=float(r['dispersion']), baseline_mean=b, joint_mean=float(r['component_mean']),
                   goal_probability=q, band='lt4' if b < 4 else '4to6' if b < 6 else 'ge6',
                   era='through_May2023' if r['date'] <= '2023-05-31' else 'after_May2023')
        out = metrics(row, float(b * np.exp(np.dot(x, theta))))
        for name, old in [('fixed180', 'baseline'), ('joint', 'component')]:
            for m in ['brier', 'nll', 'mae']:
                assert abs(out[name + '_' + m] - float(r[old + '_' + m])) < 1e-12
        rows.append(out)
    groups = defaultdict(list)
    for r in rows:
        for fields in [('league',), ('league', 'season'), ('league', 'venue'), ('league', 'band'), ('league', 'era'),
                       ('league', 'season', 'band'), ('league', 'era', 'band'), ('league', 'era', 'venue')]:
            groups['/'.join(f'{f}={r[f]}' for f in fields)].append(r)
    result = {'fit_sha256': digest(OUT / 'fit.json'), 'coverage_before_goal_quotes': dict(counts), 'excluded': excluded,
              'groups': {k: summary(v) for k, v in groups.items()},
              'sensitivity': {league: {str(w): summary(groups['league=' + league], w) for w in [14, 56]} for league in ['E1', 'E0']},
              'interpretation': 'Exploratory, conditional uncertainty, no promotion, no causal claim.'}
    (OUT / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    with (OUT / 'predictions.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
    for label in ['league=E1', 'league=E0', 'league=E0/era=through_May2023', 'league=E0/era=after_May2023']:
        g = result['groups'][label]
        print(label, g['n_team'], {k: (v, g['ci95'][k]) for k, v in g['means'].items() if k.startswith('goal_minus_') and not k.endswith('bias')})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['audit', 'train', 'evaluate'])
    {'audit': audit, 'train': train, 'evaluate': evaluate}[parser.parse_args().phase]()
