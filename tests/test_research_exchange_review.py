"""Independent adversarial contract checks; all generated inputs are synthetic tests."""
import copy
import json
import runpy
from pathlib import Path
import zipfile

import pytest
from experiments import research_exchange as x

_HELPERS = runpy.run_path(str(Path(__file__).with_name('test_research_exchange.py')))


def _record(tmp_path):
    return _HELPERS['capture'](tmp_path)


def _reseal(record):
    return x.seal({k: v for k, v in record.items() if k != 'record_id'})


@pytest.mark.parametrize('defect', ['missing_source', 'future_cutoff', 'wrong_cohort', 'wrong_model_version', 'numeric_provider', 'issued_abstention'])
def test_independent_forecast_semantics(tmp_path, defect):
    r = copy.deepcopy(_record(tmp_path))
    if defect == 'missing_source': r['source'] = {}
    elif defect == 'future_cutoff': r['source']['cutoff_utc'] = '2099-01-01T00:00:00Z'
    elif defect == 'wrong_cohort': r['cohort'] = 'legacy/original_five'
    elif defect == 'wrong_model_version': r['models']['plain']['version'] = 'unreviewed-estimator'
    elif defect == 'numeric_provider': r['fixture']['provider_fixture_id'] = 123
    elif defect == 'issued_abstention': r['abstention_reasons'] = ['UNVERIFIED']
    with pytest.raises(x.core.Invalid):
        x.validate_record(_reseal(r))


def _archive(tmp_path, *, with_result=False):
    r = _record(tmp_path)
    tail = 'EMPTY'
    now = _HELPERS['NOW']
    if with_result:
        o, evidence, now = _HELPERS['outcome'](r, tmp_path)
        tail = x.append_result(tmp_path/'store', o, evidence, expected_tail=tail, now=now)['record_id']
    original = tmp_path/'original.zip'
    x.bundle(tmp_path/'store', original, expected_tail=tail, now=now)
    with zipfile.ZipFile(original) as z:
        return {n: z.read(n) for n in z.namelist()}


def _write_rehashed(tmp_path, contents):
    """Repair all integrity hashes so rejection must follow semantic checks."""
    m = json.loads(contents['manifest.json'])
    m['files'] = [{'path': n, 'sha256': x.core.sha(b), 'bytes': len(b)} for n, b in sorted(contents.items()) if n != 'manifest.json']
    m.pop('manifest_id')
    m['manifest_id'] = x.core.sha(x.core.canonical(m))
    contents['manifest.json'] = x.core.canonical(m)+b'\n'
    p = tmp_path/'malformed.zip'
    with zipfile.ZipFile(p, 'w') as z:
        for n, b in contents.items(): z.writestr(n, b)
    return p, x.core.sha(p.read_bytes())


@pytest.mark.parametrize('defect', ['public_permission', 'changed_policy', 'unknown_manifest_field'])
def test_independent_manifest_semantics(tmp_path, defect):
    contents = _archive(tmp_path)
    m = json.loads(contents['manifest.json'])
    if defect == 'public_permission': m['permitted_use']['public_posting'] = True
    elif defect == 'changed_policy': m['policy']['half_life_days'] = 999
    else: m['unreviewed_extension'] = True
    contents['manifest.json'] = x.core.canonical(m)
    p, digest = _write_rehashed(tmp_path, contents)
    with pytest.raises(x.core.Invalid):
        x.verify_bundle(p, expected_sha256=digest)


@pytest.mark.parametrize('defect', ['negative_goals', 'completion_before_issuance', 'missing_attestation', 'unknown_status', 'unknown_result_version'])
def test_independent_imported_result_semantics(tmp_path, defect):
    contents = _archive(tmp_path, with_result=True)
    name = 'results/000001.json'
    r = json.loads(contents[name])
    if defect == 'negative_goals': r['outcome']['home_goals'] = -1
    elif defect == 'completion_before_issuance': r['outcome']['completed_at_utc'] = '2000-01-01T00:00:00Z'
    elif defect == 'missing_attestation': r['outcome']['evidence'][0]['official_identity_and_result_checked'] = False
    elif defect == 'unknown_status': r['outcome']['status'] = 'unreviewed'
    else: r['schema_version'] = 999
    r = _reseal(r)
    contents[name] = x.core.canonical(r)+b'\n'
    m = json.loads(contents['manifest.json']); m['result_tail'] = r['record_id']
    contents['manifest.json'] = x.core.canonical(m)
    p, digest = _write_rehashed(tmp_path, contents)
    with pytest.raises(x.core.Invalid):
        x.verify_bundle(p, expected_sha256=digest)


def test_independent_altered_scores_rejected(tmp_path):
    contents = _archive(tmp_path, with_result=True)
    scores = json.loads(contents['scores.json'])
    scores['groups'][x.POLICY['id']+'/E0']['metrics']['models']['plain']['brier'] = 0.99999
    contents['scores.json'] = x.core.canonical(scores)+b'\n'
    p, digest = _write_rehashed(tmp_path, contents)
    with pytest.raises(x.core.Invalid, match='derived score mismatch'):
        x.verify_bundle(p, expected_sha256=digest)


def test_independent_correction_observation_cannot_move_backwards(tmp_path):
    from datetime import timedelta
    r = _record(tmp_path)
    o, evidence, now = _HELPERS['outcome'](r, tmp_path)
    first = x.append_result(tmp_path/'store', o, evidence, expected_tail='EMPTY', now=now)
    correction, evidence, _ = _HELPERS['outcome'](r, tmp_path, 'awarded')
    correction.update(supersedes=first['record_id'], reason='Synthetic test correction')
    second = x.append_result(tmp_path/'store', correction, evidence, expected_tail=first['record_id'], now=now+timedelta(hours=1))
    original = tmp_path/'original.zip'
    x.bundle(tmp_path/'store', original, expected_tail=second['record_id'], now=now+timedelta(hours=2))
    with zipfile.ZipFile(original) as z:
        contents = {n:z.read(n) for n in z.namelist()}
    second['outcome']['observed_at_utc'] = (now-timedelta(minutes=1)).isoformat()
    for e in second['outcome']['evidence']:
        e['captured_at_utc'] = e['verified_at_utc'] = second['outcome']['observed_at_utc']
    second = _reseal(second)
    contents['results/000002.json'] = x.core.canonical(second)+b'\n'
    m = json.loads(contents['manifest.json']);m['result_tail'] = second['record_id']
    contents['manifest.json'] = x.core.canonical(m)
    p,digest = _write_rehashed(tmp_path,contents)
    with pytest.raises(x.core.Invalid, match='correction moves backwards'):
        x.verify_bundle(p,expected_sha256=digest)
