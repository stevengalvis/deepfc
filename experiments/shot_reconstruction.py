"""Explicit reconstruction, not the unavailable original shot-pressure implementation."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date
from itertools import groupby
from pathlib import Path

from deepfc.football_data_csv import load_football_data_csv, _parse_date
from deepfc.corner_distribution import negative_binomial_over_probability
from deepfc.team_corners import TEAM_CORNER_LINES, evaluate_predictions
from experiments.time_decay import compare_models, time_weight
from experiments.signal_strength import _comparison, _season

STRENGTHS = (0.25, 0.5, 1.0)
SELECTION_END = date(2023, 7, 1)
VALIDATION_END = date(2024, 7, 1)
QUARANTINE = (date(2024, 11, 10), 'Burnley', 'Swansea')

@dataclass(frozen=True)
class Shot:
    when: date
    team: str
    venue: str
    shots_for: int
    shots_allowed: int
    sot_for: int
    sot_allowed: int


def key(match):
    return (match.match_date, match.home_team, match.away_team)


def load_shots(paths, matches):
    eligible = {key(m) for m in matches}
    observations, excluded, seen = {}, [], set()
    for path in paths:
        with Path(path).open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            required = {'Div','Date','HomeTeam','AwayTeam','HS','AS','HST','AST'}
            if required - set(reader.fieldnames or ()):
                raise ValueError(f'{path}: missing shot columns')
            for row_number, row in enumerate(reader, 2):
                identity = (_parse_date(row['Date']), row['HomeTeam'].strip(), row['AwayTeam'].strip())
                if row['Div'] != 'E1' or identity in seen:
                    raise ValueError('wrong competition or duplicate shot fixture')
                seen.add(identity)
                if identity not in eligible:
                    continue
                raw = {field: row[field] for field in ('HS','AS','HST','AST')}
                reason = None
                try:
                    values = [float(raw[f]) for f in ('HS','AS','HST','AST')]
                    if any(not math.isfinite(v) or v < 0 or not v.is_integer() for v in values):
                        raise ValueError('nonnegative integer shots required')
                    hs, ass, hst, ast = map(int, values)
                    if hst > hs or ast > ass:
                        raise ValueError('shots on target exceed shots')
                except (ValueError, TypeError) as error:
                    reason = str(error)
                if identity == QUARANTINE:
                    reason = 'explicit Burnley-Swansea quarantine; ' + (reason or 'source corrected')
                if reason:
                    excluded.append(dict(path=str(path), row=row_number, fixture=[str(v) for v in identity], raw=raw, reason=reason))
                    continue
                when, home, away = identity
                observations[identity] = (
                    Shot(when, home, 'home', hs, ass, hst, ast),
                    Shot(when, away, 'away', ass, hs, ast, hst),
                )
    return observations, excluded


def pressure(history, team, opponent, venue, prediction_date):
    """Geometric mean of two smoothed, league-relative multiplicative ratios."""
    if any(item.when >= prediction_date for item in history):
        raise ValueError('shot history must strictly precede prediction date')
    opposite = 'away' if venue == 'home' else 'home'
    ratios = []
    for feature in ('shots', 'sot'):
        def totals(items, suffix):
            weighted = [(time_weight((prediction_date-i.when).days), getattr(i, feature+suffix)) for i in items]
            return sum(w*v for w,v in weighted), sum(w for w,_ in weighted)
        total, count = totals([i for i in history if i.venue == venue], '_for')
        if not count or not total:
            ratios.append(1.0)
            continue
        league = total/count
        attack, n_attack = totals([i for i in history if i.team == team and i.venue == venue], '_for')
        allowed, n_allowed = totals([i for i in history if i.team == opponent and i.venue == opposite], '_allowed')
        attack = (attack+5*league)/(n_attack+5)
        allowed = (allowed+5*league)/(n_allowed+5)
        ratios.append(attack*allowed/league**2)
    return math.sqrt(math.prod(ratios))


def generate(matches, shots):
    baseline = compare_models(matches).time_weighted
    by_day = defaultdict(list)
    for item in baseline:
        by_day[item.match.match_date].append(item)
    candidates = {s: [] for s in STRENGTHS}
    history = []
    for when, group in groupby(sorted(matches, key=lambda m:m.match_date), key=lambda m:m.match_date):
        for before in by_day[when]:
            opponent = before.match.away_team if before.venue == 'home' else before.match.home_team
            ratio = pressure(history, before.team, opponent, before.venue, when)
            for strength in STRENGTHS:
                mean = before.expected_corners * ratio**strength
                candidates[strength].append(replace(before, expected_corners=mean,
                    over_probabilities={line:negative_binomial_over_probability(mean,line,before.dispersion) for line in TEAM_CORNER_LINES}))
        for match in group:
            history.extend(shots.get(key(match), ()))
    identity = lambda values: [(p.match,p.venue,p.actual_corners,p.dispersion) for p in values]
    assert all(identity(values) == identity(baseline) for values in candidates.values())
    return baseline, {s:tuple(values) for s,values in candidates.items()}


def summarize(baseline, candidate):
    def comparison(predicate):
        return _comparison(tuple(p for p in baseline if predicate(p)), tuple(p for p in candidate if predicate(p)))
    periods = {
        'selection':lambda p:p.match.match_date < SELECTION_END,
        'validation':lambda p:SELECTION_END <= p.match.match_date < VALIDATION_END,
        'later_test':lambda p:p.match.match_date >= VALIDATION_END,
    }
    return dict(periods={name:comparison(fn) for name,fn in periods.items()},
        by_season={str(y):comparison(lambda p:_season(p)==y) for y in sorted({_season(p) for p in baseline})},
        by_period_venue={name:{v:comparison(lambda p:fn(p) and p.venue==v) for v in ('home','away')} for name,fn in periods.items()})


def run(paths):
    loaded = load_football_data_csv(paths)
    shots, excluded = load_shots(paths, loaded.matches)
    baseline, candidates = generate(loaded.matches, shots)
    earlier = lambda values:evaluate_predictions(p for p in values if p.match.match_date < SELECTION_END)
    tuning = {str(s):earlier(v) for s,v in candidates.items()}
    selected = min(STRENGTHS, key=lambda s:(tuning[str(s)]['mean_brier_score'],s))
    baseline_tuning = earlier(baseline)
    digest = lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    result = dict(label='reconstruction; implementation equivalence not established',
        selected_strength=selected, reported_strength=0.25,
        selected_beats_baseline_in_selection=tuning[str(selected)]['mean_brier_score'] < baseline_tuning['mean_brier_score'],
        tuning=tuning, baseline_tuning=baseline_tuning,
        comparison=summarize(baseline,candidates[selected]),
        data_quality=dict(rows_read=loaded.rows_read,rows_loaded=loaded.rows_loaded,
            rows_without_corner_results=loaded.rows_without_corner_results,
            valid_shot_fixtures=len(shots),excluded_shot_rows=excluded),
        source_files=[dict(path=str(p),sha256=digest(p)) for p in paths],
        specification_sha256=digest('experiments/shot_reconstruction_spec.md'),
        code_sha256={str(p):digest(p) for p in sorted([*Path('src/deepfc').glob('*.py'),*Path('experiments').glob('*.py')])})
    if selected != 0.25:
        result['predeclared_025_diagnostic'] = summarize(baseline,candidates[0.25])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_paths', nargs='+', type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.csv_paths),indent=2))

if __name__ == '__main__':
    main()
