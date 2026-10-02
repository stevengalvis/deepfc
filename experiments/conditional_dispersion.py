"""Three mean-preserving NB dispersion arms; fixed early OOF calibration."""
import argparse
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import numpy as np
from scipy.optimize import minimize, minimize_scalar, LinearConstraint
from scipy.special import gammaln

from deepfc.corner_distribution import negative_binomial_negative_log_loss as old_nll
from deepfc.corner_distribution import negative_binomial_over_probability as over
from deepfc.football_data_csv import _parse_date
from experiments.distribution_blend import e1_inputs
from experiments.e0_transfer import summary
from experiments.goal_total_extension import sources
from experiments.joint_market_calibration import design
from experiments.market_strength import strength, key

OUT = Path('experiments/results/conditional_dispersion')
PLAN = Path('experiments/protocols/conditional_dispersion_plan.md')
SPEC = Path('experiments/conditional_dispersion_spec.md')
LOW, HIGH = float(np.log(1e-4)), 0.
SLOPE_SD = .25
ENDPOINTS = np.array([[1., -.5], [1., .5]])


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def logalpha_bounds(theta):
    return ENDPOINTS @ np.asarray(theta)


def objective(theta, y, mu, z, conditional=True, derivatives=True):
    """Exact integer-count full NB likelihood, avoiding large gamma subtraction."""
    y = np.asarray(y, dtype=int); mu = np.asarray(mu, dtype=np.longdouble)
    X = np.column_stack([np.ones(len(y)), z]) if conditional else np.ones((len(y), 1))
    X = X.astype(np.longdouble); theta = np.asarray(theta, dtype=np.longdouble)
    a = np.exp(X @ theta); u = a * mu
    j = np.arange(int(max(y)) + 1, dtype=np.longdouble)
    active = j[None, :] < y[:, None]
    aj = a[:, None] * j[None, :]
    logproduct = np.sum(np.where(active, np.log1p(aj), 0), axis=1)
    loss = -logproduct + gammaln(y + 1) - y * np.log(mu) + (y + 1 / a) * np.log1p(u)
    penalty = theta[-1]**2 / (2 * SLOPE_SD**2) if conditional else 0
    value = np.sum(loss, dtype=np.longdouble) + penalty
    if not derivatives: return value
    g = -np.sum(np.where(active, aj / (1 + aj), 0), axis=1) - np.log1p(u) / a + (y + 1 / a) * u / (1 + u)
    h = -np.sum(np.where(active, aj / (1 + aj)**2, 0), axis=1) + np.log1p(u) / a - 2 * mu / (1 + u) + (y + 1 / a) * u / (1 + u)**2
    gradient = X.T @ g; hessian = (X.T * h) @ X
    if conditional:
        gradient[-1] += theta[-1] / SLOPE_SD**2
        hessian[-1, -1] += 1 / SLOPE_SD**2
    return float(value), np.asarray(gradient, dtype=float), np.asarray(hessian, dtype=float)


def polish(theta, arrays, conditional):
    """Deterministic interior Newton refinement of the SAME likelihood/objective."""
    theta = np.array(theta, dtype=float)
    for iteration in range(30):
        value, gradient, hessian = objective(theta, *arrays, conditional)
        if np.max(abs(gradient)) <= 1e-8: break
        step = np.linalg.solve(hessian, -gradient)
        if gradient @ step >= 0: raise RuntimeError('non-descent polishing direction')
        previous = objective(theta, *arrays, conditional, derivatives=False)
        for backtrack in range(40):
            candidate = theta + step * 2.**(-backtrack)
            endpoints = logalpha_bounds(candidate) if conditional else candidate
            if min(endpoints) <= LOW or max(endpoints) >= HIGH: continue
            diff = objective(candidate, *arrays, conditional, derivatives=False) - previous
            if diff <= 1e-4 * (gradient @ (candidate - theta)):
                theta = candidate; break
        else: raise RuntimeError('polishing line search unresolved')
    value, gradient, hessian = objective(theta, *arrays, conditional)
    endpoints = logalpha_bounds(theta) if conditional else theta
    distance = min(float(min(endpoints) - LOW), float(HIGH - max(endpoints)))
    eps = 1e-4; fd = []
    for i in range(len(theta)):
        step = np.eye(len(theta))[i] * eps
        fd.append(float((objective(theta + step, *arrays, conditional, derivatives=False) - objective(theta - step, *arrays, conditional, derivatives=False)) / (2 * eps)))
    agreement = float(max(abs(np.array(fd) - gradient)))
    cert = dict(objective=value, score_max=float(max(abs(gradient))), finite_difference_agreement=agreement,
                hessian_min_eigenvalue=float(min(np.linalg.eigvalsh(hessian))), bound_distance=distance, polish_iterations=iteration)
    cert['certified'] = bool(np.isfinite(theta).all() and cert['score_max'] <= 1e-6 and agreement <= 1e-5 and distance > 1e-6 and cert['hessian_min_eigenvalue'] > 0)
    return theta, cert


def fit(rows, cutoff):
    train = [r for r in rows if r['league'] == 'E1' and r['season'] in [2021, 2022] and r['date'] < str(cutoff)]
    if not train: raise ValueError('no eligible early OOF training rows')
    arrays = (np.array([r['actual'] for r in train]), np.array([r['mean'] for r in train]), np.array([r['z'] for r in train]))
    scalar = minimize_scalar(lambda a: objective([a], *arrays, False)[0], bounds=(LOW, HIGH), method='bounded', options={'xatol': 1e-12, 'maxiter': 500})
    btheta, bcert = polish([scalar.x], arrays, False)
    bcert['scalar_success'] = bool(scalar.success)
    if not scalar.success or not bcert['certified']: raise RuntimeError('constant likelihood fit not certified: ' + str(bcert))
    starts = []
    for b in [0., .25, -.25]:
        # Feasible intercept projection leaves the fixed slope start unchanged.
        a = np.clip(btheta[0], LOW + .5 * abs(b) + 1e-8, HIGH - .5 * abs(b) - 1e-8)
        initial = np.array([a, b])
        result = minimize(lambda t: objective(t, *arrays, True)[:2], initial, jac=True, method='SLSQP',
                          constraints=LinearConstraint(ENDPOINTS, LOW, HIGH), options={'ftol': 1e-12, 'maxiter': 500})
        theta, cert = polish(result.x, arrays, True)
        cert.update(initial=initial.tolist(), slsqp_success=bool(result.success), slsqp_message=str(result.message), theta=theta.tolist())
        starts.append(cert)
    if not all(c['certified'] for c in starts): raise RuntimeError('conditional starts not certified: ' + str(starts))
    spread = (max(c['objective'] for c in starts) - min(c['objective'] for c in starts)) / len(train)
    if spread > 1e-8: raise RuntimeError('conditional numerical starts disagree')
    best = min(starts, key=lambda c: c['objective'])
    return {'B': [float(btheta[0]), 0.], 'C': best['theta'], 'B_certificate': bcert, 'C_start_certificates': starts,
            'objective_spread_per_observation': spread, 'training_n': len(train), 'cutoff': str(cutoff),
            'first_training_date': min(r['date'] for r in train), 'last_training_date': max(r['date'] for r in train)}


def paired(rows):
    identities = [(r['league'], r['date'], r['home'], r['away'], r['venue']) for r in rows]
    if len(set(identities)) != len(rows): raise ValueError('duplicate forecast')
    fixtures = defaultdict(list)
    for r in rows: fixtures[(r['league'], r['date'], r['home'], r['away'])].append(r)
    if any({r['venue'] for r in part} != {'home', 'away'} or len(part) != 2 for part in fixtures.values()):
        raise ValueError('unpaired fixture forecasts')


def load_features():
    features = {}; invalid = []
    for league, year, path, sha in sources():
        assert digest(path) == sha
        if year < 2019: continue
        for r in csv.DictReader(path.open(encoding='utf-8-sig')):
            identity = (league, str(_parse_date(r['Date'])), r['HomeTeam'].strip(), r['AwayTeam'].strip())
            assert r['Div'] == league and identity not in features
            try: features[identity] = abs(strength(r)) - .5
            except (ValueError, TypeError, KeyError): invalid.append(identity)
    return features, invalid


def inputs(phase):
    features, invalid = load_features(); rows = []; excluded = []
    if phase == 'early':
        ps, signed, seasons = e1_inputs()
        folds = {f['source_season']: f for f in json.loads(Path('experiments/results/distribution_blend/selection.json').read_text())['folds']}
        for p in ps:
            year = seasons[p.match]
            if year not in folds: continue
            identity = ('E1', str(p.match.match_date), p.match.home_team, p.match.away_team)
            if identity not in features: excluded.append(identity); continue
            f = folds[year]
            assert f['certificate']['latest_training_date'] < str(date(year, 7, 1)) <= str(p.match.match_date)
            s = signed[key(p.match)] * (1 if p.venue == 'home' else -1)
            mean = float(p.expected_corners * np.exp(np.dot(design(p, s), f['theta'])))
            rows.append(dict(league='E1', date=str(p.match.match_date), home=p.match.home_team, away=p.match.away_team,
                             venue=p.venue, season=year, actual=p.actual_corners, mean=mean, current_alpha=p.dispersion,
                             baseline_mean=p.expected_corners, z=features[identity]))
    else:
        for r in csv.DictReader(Path('experiments/results/distribution_blend/predictions.csv').open()):
            identity = (r['league'], r['date'], r['home'], r['away'])
            if identity not in features: excluded.append(identity); continue
            rows.append(dict(league=r['league'], date=r['date'], home=r['home'], away=r['away'], venue=r['venue'],
                             season=int(r['season']), actual=int(r['actual']), mean=float(r['component_mean']), current_alpha=float(r['dispersion']),
                             baseline_mean=float(r['baseline_mean']), z=features[identity]))
    paired(rows)
    return rows, {'invalid_source_quotes': invalid, 'excluded_forecast_rows': excluded}


def metrics(r, fitted):
    row = dict(r); mu = r['mean']; y = r['actual']
    alphas = {'A': r['current_alpha'], **{arm: float(np.exp(np.dot([1., r['z']], fitted[arm]))) for arm in ['B', 'C']}}
    for arm, alpha in alphas.items():
        row[arm + '_alpha'] = alpha; row[arm + '_mean'] = mu
        row[arm + '_bias'] = y - mu; row[arm + '_mae'] = abs(y - mu); row[arm + '_squared_error'] = (y - mu)**2
        row[arm + '_nll'] = old_nll(y, mu, alpha)
        for label, line, invert in [('3.5', 3.5, False), ('4.5', 4.5, False), ('5.5', 5.5, False), ('6.5', 6.5, False),
                                    ('zero', .5, True), ('low_tail', 1.5, True), ('high_tail', 9.5, False)]:
            probability = over(mu, line, alpha); observed = float(y > line)
            if invert: probability = 1 - probability; observed = 1 - observed
            row[label + '_observed'] = observed; row[arm + '_' + label + '_probability'] = probability
            row[arm + '_' + label + '_error'] = observed - probability
            row[arm + '_' + label + '_brier'] = (observed - probability)**2
        row[arm + '_brier'] = sum(row[arm + '_' + str(l) + '_brier'] for l in [3.5, 4.5, 5.5, 6.5]) / 4
        assert row['A_mean'] == row[arm + '_mean'] and row['A_mae'] == row[arm + '_mae'] and row['A_bias'] == row[arm + '_bias']
    for target, ref in [('C', 'B'), ('B', 'A'), ('C', 'A')]:
        for m in ['brier', 'nll', 'mae', 'bias']:
            row[target + '_minus_' + ref + '_' + m] = row[target + '_' + m] - row[ref + '_' + m]
    row['band'] = 'lt4' if r['baseline_mean'] < 4 else '4to6' if r['baseline_mean'] < 6 else 'ge6'
    imbalance = r['z'] + .5
    row['strength_band'] = 'lt0.2' if imbalance < .2 else '0.2to0.5' if imbalance < .5 else 'ge0.5'
    row['era'] = 'through_May2023' if r['date'] <= '2023-05-31' else 'after_May2023'
    return row


def summarize(rows, width=28):
    result = summary(rows, width)
    result['alpha_ranges'] = {arm: [min(r[arm + '_alpha'] for r in rows), max(r[arm + '_alpha'] for r in rows)] for arm in ['A', 'B', 'C']}
    result['candidate_bound_rates'] = {arm: sum(min(abs(np.log(r[arm + '_alpha']) - LOW), abs(np.log(r[arm + '_alpha']) - HIGH)) <= 1e-6 for r in rows) / len(rows) for arm in ['B', 'C']}
    # Same ordered calendar blocks and random draws as summary(): preserve pairing
    # when comparing absolute aggregate calibration error (a nonlinear quantity).
    labels = ['3.5', '4.5', '5.5', '6.5', 'zero', 'low_tail', 'high_tail']
    names = [arm + '_' + label + '_error' for arm in ['A', 'B', 'C'] for label in labels]
    blocks = defaultdict(list)
    for r in rows: blocks[date.fromisoformat(r['date']).toordinal() // width].append([r[k] for k in names])
    sizes = np.array([len(v) for v in blocks.values()]); totals = np.array([np.sum(v, axis=0) for v in blocks.values()]); n = len(sizes)
    rng = random.Random(7)
    weights = np.array([np.bincount(rng.choices(range(n), k=n), minlength=n) for _ in range(10000)])
    draws = (weights @ totals) / (weights @ sizes)[:, None]
    result['absolute_calibration_error_changes'] = {}
    for target, ref in [('C', 'B'), ('B', 'A'), ('C', 'A')]:
        for label in labels:
            tk = target + '_' + label + '_error'; rk = ref + '_' + label + '_error'
            delta = np.sort(np.abs(draws[:, names.index(tk)]) - np.abs(draws[:, names.index(rk)]))
            result['absolute_calibration_error_changes'][target + '_minus_' + ref + '/' + label] = {
                'point': abs(result['means'][tk]) - abs(result['means'][rk]), 'ci95': [float(delta[249]), float(delta[9749])]}
    return result


def save_rows(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(rows)


def train():
    rows, coverage = inputs('early')
    dev = fit(rows, date(2022, 7, 1))
    heldout = [metrics(r, dev) for r in rows if r['season'] == 2022]
    development = {'fit': dev, 'assessment_2022': summarize(heldout), 'coverage': coverage}
    (OUT / 'development.json').write_text(json.dumps(development, indent=2) + '\n')
    final = fit(rows, date(2023, 7, 1))
    final.update(code_sha256=digest(__file__), spec_sha256=digest(SPEC), plan_sha256=digest(PLAN), coverage=coverage,
                 development_sha256=digest(OUT / 'development.json'))
    (OUT / 'fit.json').write_text(json.dumps(final, indent=2) + '\n')
    save_rows(OUT / 'early_oof_inputs.csv', rows)
    print(json.dumps(final, indent=2))
    print('Development2022 deltas', {k: v for k, v in development['assessment_2022']['means'].items() if '_minus_' in k})


def evaluate():
    fitted = json.loads((OUT / 'fit.json').read_text())
    for field, path in [('code_sha256', __file__), ('spec_sha256', SPEC), ('plan_sha256', PLAN)]: assert fitted[field] == digest(path)
    source, coverage = inputs('later'); rows = [metrics(r, fitted) for r in source]
    saved = list(csv.DictReader(Path('experiments/results/distribution_blend/predictions.csv').open()))
    previous = {(r['league'], r['date'], r['home'], r['away'], r['venue']): r for r in saved}
    for r in rows:
        old = previous[tuple(r[k] for k in ['league', 'date', 'home', 'away', 'venue'])]
        assert r['mean'] == float(old['component_mean'])
        for m in ['brier', 'nll', 'mae', 'bias']: assert abs(r['A_' + m] - float(old['component_' + m])) < 1e-12
    groups = defaultdict(list)
    for r in rows:
        for fields in [('league',), ('league', 'season'), ('league', 'venue'), ('league', 'band'), ('league', 'strength_band'),
                       ('league', 'era'), ('league', 'era', 'band'), ('league', 'era', 'strength_band'), ('league', 'era', 'venue')]:
            groups['/'.join(f'{k}={r[k]}' for k in fields)].append(r)
    result = {'fit_sha256': digest(OUT / 'fit.json'), 'coverage': coverage, 'n_team': len(rows),
              'groups': {k: summarize(v) for k, v in groups.items()},
              'sensitivity': {k: {str(w): summarize(groups[k], w) for w in [56, 84]} for k in ['league=E1', 'league=E0', 'league=E0/era=after_May2023']},
              'mean_invariance': 'Every mean, mean-MAE and bias exactly identical across all three arms; A reproduces saved joint metrics within1e-12.'}
    (OUT / 'results.json').write_text(json.dumps(result, indent=2) + '\n'); save_rows(OUT / 'predictions.csv', rows)
    for label in ['league=E1', 'league=E0', 'league=E0/era=through_May2023', 'league=E0/era=after_May2023']:
        g = result['groups'][label]
        print(label, {k: (v, g['ci95'][k]) for k, v in g['means'].items() if '_minus_' in k and k.endswith(('brier', 'nll'))})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['train', 'evaluate'])
    {'train': train, 'evaluate': evaluate}[parser.parse_args().phase]()
