"""All forecast/outcome fixtures here are synthetic; never use actual pilot outcomes."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pytest
from experiments import pilot_outcomes as p

NOW=datetime(2020,1,5,tzinfo=timezone.utc)

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(value).encode();path.write_bytes(raw);return p.sha(raw)

def make_specs(tmp_path):
    specs=[];original=None
    for cohort,n in [('original_five',5),('additive_three',3)]:
        base=tmp_path/cohort;base.mkdir()
        proto={'models':'SYNTHETIC stored probabilities, no model calculation',
               'hashes':{'synthetic/vendor_modelfc_goal_estimator.py':'a'*64,'synthetic/vendor_modelfc_decay_estimator.py':'b'*64}}
        ph=dump(base/'PROTOCOL_FREEZE.json',proto)
        snap={'schema_version':1,'record_type':'private_exploratory_prematch_primary_issuance' if original is None else 'private_exploratory_prematch_additive_amendment',
              'issued_at_utc':'2020-01-01T10:00:00Z','capture_completed_utc':'2020-01-01T10:01:00Z','protocol_sha256':ph,
              'pre_review_sha256':dump(base/'PRE_REVIEW.json',{'synthetic':True}),
              'fixture_sha256':dump(base/'fixtures.json',{'synthetic':True}),
              'derived_data_sha256':dump(base/'current_derived_E0.json',{'synthetic':True}), 'fixtures':[]}
        if original:snap['original_snapshot_sha256']=original
        for i in range(n):
            snap['fixtures'].append({'status':'ISSUED','home_canonical':f'Synthetic {cohort} home{i}',
                'away_canonical':f'Synthetic {cohort} away{i}','kickoff_utc':'2020-01-03T14:00:00Z',
                'issuance_utc':snap['issued_at_utc'],'market_order':p.MARKETS,
                'models':{name:{'probabilities':probs} for name,probs in zip(p.MODELS,[[.8,.2],[.6,.4],[.5,.5]])}})
        snap['fixtures'].append({'status':'EXCLUDED','reason':'INSUFFICIENT_HISTORY','home_display':'Synthetic excluded','away_display':'Synthetic other'})
        path=base/'snapshot.json';sh=dump(path,snap)
        specs.append({'snapshot':str(path),'sha256':sh,'cohort':cohort,'issued_count':n,'competition':'E0','season':'2019/20'})
        if original is None:original=sh
    return specs

@pytest.fixture
def env(tmp_path):
    (tmp_path/'snapshots').mkdir()
    specs=make_specs(tmp_path/'snapshots')
    catalog=p.load_catalog(specs)
    return tmp_path,specs,catalog,tmp_path/'ledger'

def observation(env,fid=None,status='played_final',tag='one'):
    root,_,catalog,_=env;fid=fid or next(iter(catalog['fixtures']));ref=catalog['fixtures'][fid]['reference']
    raw=('SYNTHETIC TEST EVIDENCE ONLY '+tag).encode();h=p.sha(raw);path=root/('evidence-'+tag);path.write_bytes(raw)
    e={'source_url':'https://www.premierleague.com/synthetic-test-only', 'sha256':h,
       'captured_at_utc':'2020-01-03T17:00:00Z','verified_at_utc':'2020-01-03T17:01:00Z','verified_by':'synthetic reviewer',
       'verification_note':'SYNTHETIC fixture identity, played status, regulation time goals checked',
       'verified_status':status,'official_identity_and_result_checked':True}
    out={k:ref[k] for k in ['snapshot_sha256','competition','season','home','away']}
    out.update(fixture_id=fid,status=status,actual_kickoff_utc='2020-01-03T14:00:00Z' if status=='played_final' else None,
       completed_at_utc='2020-01-03T16:00:00Z' if status=='played_final' else None,scheduled_kickoff_utc=None,
       home_goals=2 if status=='played_final' else None,away_goals=1 if status=='played_final' else None,
       observed_at_utc='2020-01-03T18:00:00Z',evidence=[e],action='initial',supersedes=None,reason=None)
    return out,{h:path}

def tail(env):
    files=sorted((env[3]/'records').glob('*.json'))
    return p.read_json(files[-1])['record_id'] if files else 'EMPTY'

def append(env,out,paths):return p.append_outcome(env[2],env[3],out,paths,expected_tail=tail(env),now=NOW)

def scored(env):return p.score(env[2],env[3],expected_tail=tail(env))

def test_weighting_three_models_and_cohorts(env):
    ids=list(env[2]['fixtures'])
    o,m=observation(env,ids[0]);append(env,o,m)
    o,m=observation(env,ids[-1],tag='two');o['home_goals']=0;o['away_goals']=3;append(env,o,m)
    r=scored(env)
    assert r['coverage']=={'issued_fixtures':8,'scored_fixtures':2,'scored_events':4,'excluded_by_reason':{'missing':6}}
    # Direct hand arithmetic: original outcomes1/0 give plain .04 vs decay .16;
    # additive outcomes0/1 give plain .64 vs decay .36. Each fixture gets half weight.
    assert r['all']['models']['plain']['brier']==pytest.approx(.34)
    assert r['all']['models']['fixed180']['brier']==pytest.approx(.26)
    assert r['all']['models']['venue_frequency']['brier']==pytest.approx(.25)
    assert r['all']['paired']['fixed180_minus_plain']['fixture_weighted_brier_difference']==pytest.approx(-.08)
    assert r['cohorts']['original_five']['metrics']['models']['plain']['brier']==pytest.approx(.04)
    assert r['cohorts']['additive_three']['metrics']['models']['plain']['brier']==pytest.approx(.64)
    assert r['all']['models']['plain']['venues']['home']['calibration_gap']==pytest.approx(.3)
    assert len(r['issuance_exclusions'])==2

def test_missing_empty_scores_are_null(env):
    r=scored(env);assert r['all'] is None and r['coverage']['excluded_by_reason']=={'missing':8}
    assert all(c['metrics'] is None for c in r['cohorts'].values())

@pytest.mark.parametrize('status',['postponed','abandoned','awarded','cancelled'])
def test_nonfinal_excluded(env,status):
    o,m=observation(env,status=status);append(env,o,m)
    r=scored(env);assert r['all'] is None and r['coverage']['excluded_by_reason'][status]==1

def test_conflict_then_explicit_correction(env):
    o,m=observation(env);first=append(env,o,m)
    conflict,paths=observation(env,status='conflicting',tag='conflict-a')
    second,more=observation(env,status='conflicting',tag='conflict-b');conflict['evidence']+=second['evidence'];paths.update(more)
    conflict.update(action='correction',supersedes=first['record_id'],reason='Conflicting official evidence: suspend scoring')
    c=append(env,conflict,paths);assert scored(env)['all'] is None
    resolved,paths=observation(env,tag='resolved');resolved.update(action='correction',supersedes=c['record_id'],reason='Official correction resolves conflict',home_goals=0,away_goals=2)
    append(env,resolved,paths);r=scored(env);assert r['all']['models']['plain']['brier']==pytest.approx(.64)
    assert r['ledger_records']==3 and p.read_ledger(env[2],env[3])[0][0]==first

def test_postponement_then_completion_uses_original_forecast(env):
    o,m=observation(env,status='postponed');o['scheduled_kickoff_utc']='2020-01-04T14:00:00Z';first=append(env,o,m)
    final,m=observation(env,tag='rescheduled');final.update(action='update',supersedes=first['record_id'],reason='Played after postponement',actual_kickoff_utc='2020-01-04T14:00:00Z',completed_at_utc='2020-01-04T16:00:00Z',observed_at_utc='2020-01-04T18:00:00Z')
    final['evidence'][0].update(captured_at_utc='2020-01-04T17:00:00Z',verified_at_utc='2020-01-04T17:01:00Z');append(env,final,m)
    r=scored(env);assert r['fixtures'][0]['reference']['original_kickoff_utc']=='2020-01-03T14:00:00Z'
    assert r['all']['models']['plain']['brier']==pytest.approx(.04)

def test_duplicate_initial_and_conflicting_initial_rejected(env):
    o,m=observation(env);append(env,o,m)
    for goals in [2,4]:
        o['home_goals']=goals
        with pytest.raises(p.Invalid,match='duplicate/conflicting'):append(env,o,m)
    assert len(p.read_ledger(env[2],env[3])[0])==1

def test_concurrent_duplicate_has_one_record(env):
    o,m=observation(env)
    def attempt(_):
        try:append(env,o,m);return True
        except p.Invalid:return False
    with ThreadPoolExecutor(max_workers=2) as ex:assert sum(ex.map(attempt,range(2)))==1
    assert len(p.read_ledger(env[2],env[3])[0])==1

def test_stale_correction_parent_and_terminal_update_rejected(env):
    o,m=observation(env);first=append(env,o,m)
    o.update(action='correction',supersedes='a'*64,reason='correction')
    with pytest.raises(p.Invalid,match='parent'):append(env,o,m)
    o.update(action='update',supersedes=first['record_id'],home_goals=4)
    with pytest.raises(p.Invalid,match='requires correction'):append(env,o,m)

@pytest.mark.parametrize('field,value', [('snapshot_sha256','a'*64),('competition','SP1'),('season','2020/21'),('home','wrong'),('away','wrong'),('fixture_id','unknown')])
def test_identity_mismatch(env,field,value):
    o,m=observation(env);o[field]=value
    with pytest.raises(p.Invalid):append(env,o,m)

@pytest.mark.parametrize('field,value',[('home_goals',True),('away_goals',-1),('home_goals',1.5),('status','completed'),('actual_kickoff_utc','2020-01-01T09:00:00Z'),('observed_at_utc','2030-01-01T00:00:00Z'),('completed_at_utc','2020-01-03T19:00:00Z'),('observed_at_utc','2020-01-03T18:00:00')])
def test_bad_outcome_fields(env,field,value):
    o,m=observation(env);o[field]=value
    with pytest.raises(p.Invalid):append(env,o,m)

@pytest.mark.parametrize('field,value',[('source_url','https://premierleague.com.evil.test/result'),('source_url','http://www.premierleague.com/result'),('source_url','https://name@www.premierleague.com/result'),('official_identity_and_result_checked',False),('verified_status','awarded'),('verified_by',''),('captured_at_utc','2020-01-03T15:00:00Z'),('verified_at_utc','2020-01-06T00:00:00Z')])
def test_bad_evidence_attestation(env,field,value):
    o,m=observation(env);o['evidence'][0][field]=value
    with pytest.raises(p.Invalid):append(env,o,m)

def test_missing_evidence_and_conflict_single_capture(env):
    o,m=observation(env);o['evidence']=[]
    with pytest.raises(p.Invalid):append(env,o,m)
    o,m=observation(env,status='conflicting')
    with pytest.raises(p.Invalid,match='both conflicting'):append(env,o,m)

def test_awarded_score_cannot_be_treated_as_final(env):
    o,m=observation(env,status='awarded');o['home_goals']=3
    with pytest.raises(p.Invalid,match='non-final'):append(env,o,m)

def test_evidence_content_tamper_before_and_after_append(env):
    o,m=observation(env);file=next(iter(m.values()));original=file.read_bytes();file.write_bytes(b'changed')
    with pytest.raises(p.Invalid,match='evidence'):append(env,o,m)
    file.write_bytes(original);append(env,o,m)
    (env[3]/'evidence'/o['evidence'][0]['sha256']).write_bytes(b'tampered')
    with pytest.raises(p.Invalid,match='evidence'):scored(env)

def test_record_tamper_and_missing_middle_fail_closed(env):
    o,m=observation(env);append(env,o,m);o,m=observation(env,list(env[2]['fixtures'])[1],tag='two');append(env,o,m)
    file=env[3]/'records/000001.json';raw=file.read_bytes();r=p.read_json(file);r['outcome']['home_goals']=4;dump(file,r)
    with pytest.raises(p.Invalid,match='tampered'):scored(env)
    file.write_bytes(raw);file.unlink()
    with pytest.raises(p.Invalid,match='chain'):scored(env)

@pytest.mark.parametrize('filename',['snapshot.json','PROTOCOL_FREEZE.json','PRE_REVIEW.json','fixtures.json','current_derived_E0.json'])
def test_frozen_file_tamper(env,filename):
    path=Path(env[1][0]['snapshot']).parent/filename;path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(p.Invalid,match='hash mismatch'):p.load_catalog(env[1])

def test_market_timing_and_bad_probability_schema_even_with_new_hash(env):
    spec=env[1][0];path=Path(spec['snapshot']);snap=p.read_json(path)
    snap['fixtures'][0]['models']['plain']['probabilities']=[True,.5];spec['sha256']=dump(path,snap)
    with pytest.raises(p.Invalid,match='probability'):p.load_catalog(env[1][:1])
    snap['fixtures'][0]['models']['plain']['probabilities']=[.4,.5];snap['capture_completed_utc']='2020-01-03T15:00:00Z';spec['sha256']=dump(path,snap)
    with pytest.raises(p.Invalid,match='before original kickoff'):p.load_catalog(env[1][:1])

def test_zero_probability_impossible_loss_not_clipped(env):
    spec=env[1][0];path=Path(spec['snapshot']);snap=p.read_json(path);snap['fixtures'][0]['models']['plain']['probabilities']=[0,1];spec['sha256']=dump(path,snap)
    env=(env[0],env[1],p.load_catalog([spec]),env[3]);o,m=observation(env);append(env,o,m);r=scored(env)
    assert r['all']['models']['plain']['brier']==1
    assert r['all']['models']['plain']['venues']['home']['binary_logloss'] is None
    assert r['all']['models']['plain']['venues']['home']['infinite_logloss_events']==1

def test_score_receipt_cannot_overwrite(tmp_path):
    path=tmp_path/'receipt.json';p.write_new(path,b'first')
    with pytest.raises(FileExistsError):p.write_new(path,b'second')
    assert path.read_bytes()==b'first'

def test_duplicate_json_keys_rejected(tmp_path):
    path=tmp_path/'bad.json';path.write_text('{"x":1,"x":2}')
    with pytest.raises(p.Invalid,match='duplicate JSON'):p.read_json(path)


def test_tail_rollback_and_wrong_ledger_fail_against_retained_receipt(env):
    o,m=observation(env);first=append(env,o,m)
    o,m=observation(env,list(env[2]['fixtures'])[1],tag='two');second=append(env,o,m)
    (env[3]/'records/000002.json').unlink()
    with pytest.raises(p.Invalid,match='retained receipt'):
        p.score(env[2],env[3],expected_tail=second['record_id'])
    with pytest.raises(p.Invalid,match='retained receipt'):
        p.append_outcome(env[2],env[3],o,m,expected_tail=second['record_id'],now=NOW)
    with pytest.raises(p.Invalid,match='retained receipt'):
        p.score(env[2],env[0]/'wrong-ledger',expected_tail=first['record_id'])

def test_noop_correction_is_duplicate(env):
    o,m=observation(env);first=append(env,o,m)
    o.update(action='correction',supersedes=first['record_id'],reason='no actual new evidence')
    with pytest.raises(p.Invalid,match='duplicate observation'):append(env,o,m)

def test_anchor_cannot_be_omitted_or_none(env):
    o,m=observation(env)
    with pytest.raises(TypeError):p.score(env[2],env[3])
    with pytest.raises(p.Invalid):p.score(env[2],env[3],expected_tail=None)
    with pytest.raises(p.Invalid):p.append_outcome(env[2],env[3],o,m,expected_tail=None,now=NOW)
