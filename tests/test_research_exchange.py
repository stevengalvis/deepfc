"""Synthetic unit-test inputs only; never exported as genuine provider data."""
import copy
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import pytest
from experiments import research_exchange as x

NOW=datetime(2026,10,4,12,tzinfo=timezone.utc)

def request(tmp_path, league='E0'):
    raw=b'unit-test evidence, not provider data';(tmp_path/'evidence').write_bytes(raw)
    rows=[]
    for i in range(120):
        rows.append({'competition':league,'date':str((NOW-timedelta(days=121-i)).date()),'home':'Test A' if i%2 else 'Test B','away':'Test B' if i%2 else 'Test A','home_goals':i%4,'away_goals':i%3,'status':'played_final'})
    return {'schema_version':1,'data_kind':'real_completed_match_history',
      'fixture':{'competition':league,'season':'2026/27','home':'Test A','away':'Test B','kickoff_utc':(NOW+timedelta(hours=24)).isoformat(),'provider_fixture_id':None},
      'history':rows,'source':{'history_evidence':{'path':'evidence','sha256':x.core.sha(raw)},'fixture_evidence':{'path':'evidence','sha256':x.core.sha(raw)},'retrieved_at_utc':NOW.isoformat(),'fixture_checked_at_utc':NOW.isoformat(),'complete_through_utc':NOW.isoformat()},
      'review':{'reviewer':'unit test only','source_url':'https://example.invalid','rights_basis':'synthetic test fixture only','real_data_verified':True,'history_complete':True,'fixture_identity_checked':True,'private_research_use_reviewed':True}}

def capture(tmp_path, q=None):
    q=q or request(tmp_path);p=tmp_path/'request.json';p.write_text(json.dumps(q))
    return x.issue(p,tmp_path/'store',now=NOW)

def outcome(r,tmp_path,status='played_final'):
    observed=NOW+timedelta(days=2);raw=b'unit test outcome evidence';p=tmp_path/'result-evidence';p.write_bytes(raw);h=x.core.sha(raw)
    host={'E0':'premierleague.com','E1':'efl.com','SP1':'laliga.com'}[r['fixture']['competition']]
    evidence={'source_url':f'https://{host}/unit-test','sha256':h,'captured_at_utc':observed.isoformat(),'verified_at_utc':observed.isoformat(),'verified_by':'unit tester','verification_note':'synthetic arithmetic test only','verified_status':status,'official_identity_and_result_checked':True}
    return {'forecast_record_id':r['record_id'],'status':status,'home_goals':2 if status=='played_final' else None,'away_goals':0 if status=='played_final' else None,'actual_kickoff_utc':r['fixture']['kickoff_utc'] if status=='played_final' else None,'scheduled_kickoff_utc':None,'completed_at_utc':(NOW+timedelta(hours=27)).isoformat() if status=='played_final' else None,'observed_at_utc':observed.isoformat(),'evidence':[evidence],'supersedes':None,'reason':None},{h:str(p)},observed

@pytest.mark.parametrize('league',x.LEAGUES)
def test_real_contract_flow_and_hand_scoring(tmp_path,league):
    r=capture(tmp_path,request(tmp_path,league));assert r['status']=='issued'
    o,paths,now=outcome(r,tmp_path);receipt=x.append_result(tmp_path/'store',o,paths,expected_tail='EMPTY',now=now)
    result=x.score(tmp_path/'store',expected_tail=receipt['record_id'])['groups'][x.POLICY['id']+'/'+league]
    assert result['metrics']['fixtures']==1
    for name in x.MODELS:
        p,q=r['models'][name]['probabilities']
        assert result['metrics']['models'][name]['brier']==pytest.approx(((p-1)**2+q*q)/2)
    output=tmp_path/'bundle.zip';info=x.bundle(tmp_path/'store',output,expected_tail=receipt['record_id'],now=now)
    assert x.verify_bundle(output,expected_sha256=info['bundle_sha256'])['result_count']==1

@pytest.mark.parametrize('defect,reason',[('late','OUTSIDE_FROZEN_24H_WINDOW'),('stale','STALE_OR_INCOMPLETE_HISTORY_SNAPSHOT'),('unchecked','FIXTURE_IDENTITY_CHECKED'),('support','INSUFFICIENT_HISTORY_SUPPORT')])
def test_abstentions_preserve_denominator(tmp_path,defect,reason):
    q=request(tmp_path)
    if defect=='late':q['fixture']['kickoff_utc']=(NOW+timedelta(hours=2)).isoformat()
    if defect=='stale':q['source']['complete_through_utc']=(NOW-timedelta(days=2)).isoformat()
    if defect=='unchecked':q['review']['fixture_identity_checked']=False
    if defect=='support':q['history']=q['history'][:4]
    r=capture(tmp_path,q);assert r['status']=='abstained' and reason in r['abstention_reasons'] and not r['models']
    group=x.score(tmp_path/'store',expected_tail='EMPTY')['groups'][x.POLICY['id']+'/E0']
    assert group['captured_fixtures']==1 and group['status_counts']=={'abstained':1} and group['metrics'] is None

@pytest.mark.parametrize('defect',['synthetic','future_history','mixed_league','duplicate','bool_goals','unknown_status','evidence_tamper','future_cutoff'])
def test_invalid_source_hard_stop(tmp_path,defect):
    q=request(tmp_path)
    if defect=='synthetic':q['data_kind']='synthetic-team-goals'
    if defect=='future_history':q['history'][0]['date']=str(NOW.date())
    if defect=='mixed_league':q['history'][0]['competition']='SP1'
    if defect=='duplicate':q['history'].append(q['history'][0])
    if defect=='bool_goals':q['history'][0]['home_goals']=True
    if defect=='unknown_status':q['history'][0]['status']='assumed_played'
    if defect=='evidence_tamper':(tmp_path/'evidence').write_bytes(b'tampered')
    if defect=='future_cutoff':q['source']['complete_through_utc']=(NOW+timedelta(days=1)).isoformat()
    with pytest.raises(x.core.Invalid):capture(tmp_path,q)

def test_no_reissue_backdating_or_rewrite(tmp_path):
    q=request(tmp_path);r=capture(tmp_path,q)
    assert r['issued_at_utc']==NOW.isoformat()
    with pytest.raises(x.core.Invalid,match='already captured'):capture(tmp_path,q)
    q['issued_at_utc']='2000-01-01T00:00:00Z'
    with pytest.raises(x.core.Invalid,match='schema'):capture(tmp_path,q)
    r['models']['plain']['probabilities'][0]=.999
    with pytest.raises(x.core.Invalid,match='hash'):x.validate_record(r)

def test_correction_award_and_rollback(tmp_path):
    r=capture(tmp_path);o,p,now=outcome(r,tmp_path);first=x.append_result(tmp_path/'store',o,p,expected_tail='EMPTY',now=now)
    with pytest.raises(x.core.Invalid):x.append_result(tmp_path/'store',o,p,expected_tail='EMPTY',now=now)
    o,p,now=outcome(r,tmp_path,'awarded');o.update(supersedes=first['record_id'],reason='corrected to administrative award')
    second=x.append_result(tmp_path/'store',o,p,expected_tail=first['record_id'],now=now)
    assert x.score(tmp_path/'store',expected_tail=second['record_id'])['groups'][x.POLICY['id']+'/E0']['metrics'] is None
    (tmp_path/'store/results/000002.json').unlink()
    with pytest.raises(x.core.Invalid,match='tail'):x.score(tmp_path/'store',expected_tail=second['record_id'])

@pytest.mark.parametrize('defect',['wrong_league_host','before_completion','missing_attestation','synthetic_host','same_evidence_conflict'])
def test_outcome_evidence_guards(tmp_path,defect):
    r=capture(tmp_path);o,p,now=outcome(r,tmp_path)
    if defect=='wrong_league_host':o['evidence'][0]['source_url']='https://laliga.com/test'
    if defect=='synthetic_host':o['evidence'][0]['source_url']='https://example.invalid/test'
    if defect=='before_completion':o['evidence'][0]['captured_at_utc']=NOW.isoformat()
    if defect=='missing_attestation':o['evidence'][0]['official_identity_and_result_checked']=False
    if defect=='same_evidence_conflict':o,p,now=outcome(r,tmp_path,'conflicting')
    with pytest.raises(x.core.Invalid):x.append_result(tmp_path/'store',o,p,expected_tail='EMPTY',now=now)

def test_kickoff_correction_does_not_reissue(tmp_path):
    r=capture(tmp_path);o,p,now=outcome(r,tmp_path);o['actual_kickoff_utc']=(NOW+timedelta(hours=25)).isoformat()
    receipt=x.append_result(tmp_path/'store',o,p,expected_tail='EMPTY',now=now)
    stored=x._load_forecasts(tmp_path/'store')[r['record_id']]
    assert stored['fixture']['kickoff_utc']==r['fixture']['kickoff_utc']
    assert x.score(tmp_path/'store',expected_tail=receipt['record_id'])['groups'][x.POLICY['id']+'/E0']['metrics']['fixtures']==1

@pytest.mark.skipif(not all(Path(s['snapshot']).exists() for s in x.core.ACTUAL),reason='private genuine legacy snapshots unavailable in this environment')
def test_legacy_genuine_export_preserves_originals(tmp_path):
    before={s['snapshot']:x.core.sha(Path(s['snapshot']).read_bytes()) for s in x.core.ACTUAL}
    receipt=x.export_pilot(tmp_path/'store',now=NOW);assert receipt['legacy_issued']==8
    original=x.core.load_catalog()
    for r in x._load_forecasts(tmp_path/'store').values():
        item=original['fixtures'][r['source']['legacy_fixture_id']]
        assert r['issued_at_utc']==item['reference']['issued_at_utc'] and r['issuance_kind']=='preserved_legacy'
        assert not r['source']['primary_cohort_eligible']
        assert all(r['models'][n]['probabilities']==item['models'][n]['probabilities'] for n in x.MODELS)
        assert 'DRAFT' in x.draft(r) and 'Legacy' in x.draft(r)
        posts=x.draft_posts(r);assert all(len(p)<=280 and p.startswith('DRAFT') for p in posts)
        assert all('not a betting-value claim' in p and 'Legacy inputs: freshness/provenance limits; not prospective.' in p for p in posts)
        assert all(r['fixture']['home'] in p and r['fixture']['away'] in p for p in posts)
    assert before=={p:x.core.sha(Path(p).read_bytes()) for p in before}

def test_odds_contract_has_no_synthetic_or_mismatched_market(tmp_path):
    r=capture(tmp_path);q={'forecast_record_id':r['record_id'],'team':'home','market':r['market'],'decimal_odds':2.3,'bookmaker':'user-supplied test','quoted_at_utc':NOW.isoformat(),'captured_at_utc':NOW.isoformat(),'evidence_sha256':'a'*64}
    assert x.validate_odds_reference(q,r,now=NOW)==q
    q['market']={**r['market'],'line':2.5}
    with pytest.raises(x.core.Invalid):x.validate_odds_reference(q,r,now=NOW)

def test_archive_integrity_and_exclusive_output(tmp_path):
    capture(tmp_path);p=tmp_path/'b.zip';m=x.bundle(tmp_path/'store',p,expected_tail='EMPTY',now=NOW)
    assert x.verify_bundle(p,expected_sha256=m['bundle_sha256'])['forecast_count']==1
    with pytest.raises(FileExistsError):x.bundle(tmp_path/'store',p,expected_tail='EMPTY',now=NOW)
    with pytest.raises(x.core.Invalid):x.verify_bundle(p,expected_sha256='0'*64)

def test_draft_standalone_qualification_and_no_truncation(tmp_path):
    r=capture(tmp_path);posts=x.draft_posts(r)
    assert all(len(p)<=280 and 'Research only; not a betting-value claim.' in p for p in posts)
    assert 'Issued '+r['issued_at_utc'] in ' '.join(posts)
    assert sum('plain ' in p for p in posts)>=1
    for j,v in enumerate(('home','away')):
        assert f"{r['fixture'][v]} regulation goals O1.5: plain {r['models']['plain']['probabilities'][j]:.1%}; recency {r['models']['fixed180']['probabilities'][j]:.1%}." in ' '.join(posts)
    with pytest.raises(x.core.Invalid,match='semantic draft unit'):x.draft_posts(r,limit=100)

def test_abstention_drafts_do_not_imply_probability(tmp_path):
    q=request(tmp_path);q['review']['fixture_identity_checked']=False;r=capture(tmp_path,q)
    posts=x.draft_posts(r)
    assert all('No forecast.' in p and 'not a betting-value claim' in p for p in posts)
    assert 'FIXTURE_IDENTITY_CHECKED' in ' '.join(posts)
