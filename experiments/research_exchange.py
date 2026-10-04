"""Local research-only forecast exchange. No providers, publishing or model fitting."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import date, datetime, timezone
import math
import json
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

from experiments import pilot_outcomes as core
from experiments.goals_plain_poisson import Match
from experiments.vendor_modelfc_goal_estimator import estimate_expected_goals
from experiments.vendor_modelfc_decay_estimator import estimate_decay_expected_goals
from experiments.team_goals_over15 import probabilities

LEAGUES = ('E0', 'E1', 'SP1')
MODELS = core.MODELS
HOSTS = {'E0': {'premierleague.com', 'thefa.com'},
         'E1': {'efl.com', 'thefa.com'}, 'SP1': {'laliga.com', 'rfef.es'}}
PINNED = {'vendor_modelfc_goal_estimator.py': 'ffe417a8ad21783b9cc654d013cc187a6aebc8a74117ea2d62f16a5662a774d5',
          'vendor_modelfc_decay_estimator.py': 'e623f0fc33c94296f4a8219b20823207586f64baa347ed510036bb3d176a2cb5'}
POLICY = {'id': 'three-league-o15-v1', 'league_order': list(LEAGUES),
          'target_lead_hours': 24, 'lead_tolerance_hours': 1,
          'max_snapshot_age_hours': 24, 'max_fixture_check_age_hours': 24,
          'minimum_history_fixtures': 100, 'minimum_venue_appearances': 5,
          'primary_comparison': 'fixed180_minus_plain', 'context_model': 'venue_frequency',
          'smoothing_matches': 5, 'half_life_days': 180,
          'research_only': True, 'automatic_promotion': False}
require = core.require
read_json = core.read_json
PERMITTED_USE = {'private_research':True,'public_posting':False,'commercial_redistribution':False,'production_promotion':False}

def _json(raw):
    def pairs(items):
        out={}
        for k,v in items:
            require(k not in out,'duplicate JSON key');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda v: (_ for _ in ()).throw(core.Invalid('nonfinite JSON')))

def now_utc():
    return datetime.now(timezone.utc)

def identity(f):
    return core.sha(core.canonical({k: f[k] for k in ('competition', 'season', 'home', 'away')}))

def seal(record):
    return dict(record, record_id=core.sha(core.canonical(record)))

def validate_record(r):
    require(set(r)=={'schema_version','kind','environment','research_only','fixture','fixture_id','market','issued_at_utc','exported_at_utc','issuance_kind','cohort','status','abstention_reasons','source','models','outcome_evidence_refs','record_id'}, 'forecast schema mismatch')
    require(r['schema_version'] == 1 and r['kind'] == 'deepfc_research_forecast', 'unsupported contract')
    require(r['environment'] == 'research_real' and r['research_only'] is True, 'synthetic/production records prohibited')
    require(r['record_id'] == core.sha(core.canonical({k:v for k,v in r.items() if k != 'record_id'})), 'record hash mismatch')
    f = r['fixture']; require(set(f)=={'competition','season','home','away','kickoff_utc','provider_fixture_id'}, 'fixture schema mismatch')
    require(f['competition'] in LEAGUES and f['home'] != f['away'], 'invalid fixture')
    core.timestamp(f['kickoff_utc'])
    for k in ('season', 'home', 'away'): core.text(f[k])
    if f['provider_fixture_id'] is not None:core.text(f['provider_fixture_id'])
    require(r['fixture_id'] == identity(f), 'fixture identity mismatch')
    require(r['market'] == {'type':'team_goals', 'period':'regulation', 'selection':'over', 'line':1.5,
                            'team_order':['home','away']}, 'unsupported market')
    require(r['status'] in ('issued','abstained'), 'invalid status')
    require(r['issuance_kind'] in ('new_capture','preserved_legacy'), 'invalid issuance kind')
    issued, captured = core.timestamp(r['issued_at_utc']), core.timestamp(r['exported_at_utc'])
    require(issued <= captured, 'issuance after export')
    require(isinstance(r['abstention_reasons'],list),'invalid abstention reasons')
    for reason in r['abstention_reasons']:core.text(reason)
    if r['status'] == 'issued':
        require(r['abstention_reasons']==[],'issued forecast has abstention reasons')
        require(issued < core.timestamp(f['kickoff_utc']), 'not issued prematch')
        require(set(r['models']) == set(MODELS), 'paired models required')
        for name, m in r['models'].items():
            require(set(m)=={'version','probabilities'}, 'model schema mismatch')
            core.text(m['version'])
            require(len(m['probabilities']) == 2 and all(type(p) in (int,float) and math.isfinite(p) and 0 <= p <= 1 for p in m['probabilities']), 'invalid probability')
    else:
        require(r['models'] == {} and bool(r['abstention_reasons']), 'abstention cannot contain forecasts')
    require(r['outcome_evidence_refs'] == [], 'outcomes must be separate append-only observations')
    _validate_source(r,issued,captured)
    return r

def _validate_source(r,issued,captured):
    s=r['source'];f=r['fixture']
    require(isinstance(s,dict),'invalid source')
    if r['issuance_kind']=='new_capture':
        require(r['cohort']==POLICY['id'] and issued==captured,'new capture cohort/clock mismatch')
        require(set(s)=={'request_sha256','cutoff_utc','cutoff_date','cutoff_precision','retrieved_at_utc','fixture_checked_at_utc','latest_match_date','evidence_sha256','review','quarantined_fixtures','history_counts','policy_sha256'},'new source schema mismatch')
        require(s['cutoff_precision']=='utc' and s['cutoff_date'] is None,'new cutoff precision mismatch')
        cutoff=core.timestamp(s['cutoff_utc']);retrieved=core.timestamp(s['retrieved_at_utc']);checked=core.timestamp(s['fixture_checked_at_utc'])
        require(cutoff<=retrieved<=issued and checked<=issued,'future/inconsistent source timestamps')
        if s['latest_match_date'] is not None:
            d=date.fromisoformat(s['latest_match_date']);require(d<issued.date() and d<=cutoff.date(),'future source history')
        core.digest_text(s['request_sha256'])
        require(s['policy_sha256']==core.sha(core.canonical(POLICY)),'unknown source policy')
        require(set(s['evidence_sha256'])=={'history_evidence','fixture_evidence'},'missing source evidence')
        for h in s['evidence_sha256'].values():core.digest_text(h)
        review=s['review']
        review_flags=('real_data_verified','history_complete','fixture_identity_checked','private_research_use_reviewed')
        require(set(review)=={'reviewer','source_url','rights_basis',*review_flags} and all(type(review[k]) is bool for k in review_flags),'invalid source review schema')
        for k in ('reviewer','source_url','rights_basis'):core.text(review[k])
        counts=s['history_counts'];require(set(counts)=={'fixtures','home_venue','away_venue'} and all(type(v) is int and v>=0 for v in counts.values()),'invalid history counts')
        require(max(counts['home_venue'],counts['away_venue'])<=counts['fixtures'],'inconsistent history counts')
        require(isinstance(s['quarantined_fixtures'],list),'invalid quarantine')
        if r['status']=='issued':
            require(all(review.get(k) is True for k in ('real_data_verified','history_complete','fixture_identity_checked','private_research_use_reviewed')),'missing source review')
            require(23<=(core.timestamp(f['kickoff_utc'])-issued).total_seconds()/3600<=25,'outside capture window')
            require(all((issued-t).total_seconds()<=86400 for t in (cutoff,retrieved,checked)),'stale source')
            require(counts['fixtures']>=100 and min(counts['home_venue'],counts['away_venue'])>=5,'insufficient source support')
            require(r['models']['plain']['version']==PINNED['vendor_modelfc_goal_estimator.py'] and r['models']['fixed180']['version']==PINNED['vendor_modelfc_decay_estimator.py'],'unknown model version')
    else:
        require(set(s)=={'legacy_reference','legacy_fixture_id','snapshot_sha256','cutoff_utc','cutoff_date','cutoff_precision','limits','primary_cohort_eligible'},'legacy source schema mismatch')
        ref=s['legacy_reference'];spec=next((v for v in core.ACTUAL if v['sha256']==s['snapshot_sha256']),None)
        require(spec is not None and r['cohort']=='legacy/'+spec['cohort'] and r['status']=='issued','unknown legacy cohort')
        require(s['cutoff_precision']=='date' and s['cutoff_utc'] is None and date.fromisoformat(s['cutoff_date'])<issued.date(),'legacy cutoff mismatch')
        require(s['primary_cohort_eligible'] is False and bool(s['limits']),'legacy limitations missing')
        require(s['legacy_fixture_id']==core.sha(core.canonical(ref)) and ref['snapshot_sha256']==s['snapshot_sha256'],'legacy reference mismatch')
        for k in ('competition','season','home','away'):require(f[k]==ref[k],'legacy fixture mismatch')
        require(f['kickoff_utc']==ref['original_kickoff_utc'] and r['issued_at_utc']==ref['issued_at_utc'] and ref['cohort']==spec['cohort'],'legacy issuance mismatch')
        hashes=ref['model_source_hashes'];require({Path(k).name:v for k,v in hashes.items()}==PINNED,'unknown legacy model source')
        require(all(r['models'][n]['version']==core.sha(core.canonical(hashes)) for n in ('plain','fixed180')),'legacy model version mismatch')
    if r['status']=='issued':require(r['models']['venue_frequency']['version']=='beta11-venue-o15-v1','unknown context model version')

def put_record(store, r):
    validate_record(r)
    root = Path(store)
    with core.locked(root):
        # One capture per fixture/cohort; no selecting a later, more attractive forecast.
        slot = core.sha(core.canonical([r['cohort'], r['fixture_id']]))
        index = root/'slots'/f'{slot}.json'
        require(not index.exists(), 'fixture already captured for cohort')
        core.write_new(root/'forecasts'/f"{r['record_id']}.json", core.canonical(r)+b'\n')
        core.write_new(index, core.canonical({'record_id':r['record_id']})+b'\n')
    return r

def _base(fixture, issued, exported, kind, cohort, source):
    return {'schema_version':1, 'kind':'deepfc_research_forecast', 'environment':'research_real',
            'research_only':True, 'fixture':fixture, 'fixture_id':identity(fixture),
            'market':{'type':'team_goals','period':'regulation','selection':'over','line':1.5,'team_order':['home','away']},
            'issued_at_utc':issued, 'exported_at_utc':exported, 'issuance_kind':kind, 'cohort':cohort,
            'status':'issued','abstention_reasons':[], 'source':source, 'models':{},
            'outcome_evidence_refs':[]}

def issue(request_path, store, *, now=None):
    """Compute only existing frozen models from an attested local normalized bundle.

    CLI clock cannot be supplied. Python now injection exists for deterministic tests.
    Attestation establishes reviewer accountability, not independent source truth.
    """
    now = now or now_utc(); request_raw=Path(request_path).read_bytes(); q = read_json(request_path)
    require(q==json.loads(request_raw),'request changed during read')
    require(set(q) == {'schema_version','data_kind','fixture','history','source','review'}, 'request schema mismatch')
    require(q['schema_version'] == 1 and q['data_kind'] == 'real_completed_match_history', 'real input bundle required')
    f, s, review = q['fixture'], q['source'], q['review']
    flags=('real_data_verified','history_complete','fixture_identity_checked','private_research_use_reviewed')
    require(set(review)<={'reviewer','source_url','rights_basis',*flags},'unknown review field')
    review={**review,**{k:review.get(k,False) for k in flags}}
    require(all(type(review[k]) is bool for k in flags),'review flags must be boolean')
    require(set(f) == {'competition','season','home','away','kickoff_utc','provider_fixture_id'}, 'fixture schema mismatch')
    require(f['competition'] in LEAGUES and f['home'] != f['away'], 'unsupported fixture')
    for k in ('season','home','away'): core.text(f[k])
    require(f['provider_fixture_id'] is None or isinstance(f['provider_fixture_id'],str), 'provider ID must be actual text or null')
    for k in ('reviewer','source_url','rights_basis'): core.text(review[k])
    # Raw input and fixture evidence must already exist locally. No network action here.
    base = Path(request_path).parent
    evidence = {}; evidence_blobs = {}
    for k in ('history_evidence','fixture_evidence'):
        item = s[k]; core.digest_text(item['sha256']); raw = (base/item['path']).read_bytes()
        require(raw and core.sha(raw) == item['sha256'], 'input evidence mismatch')
        evidence[k] = item['sha256']
        evidence_blobs[item['sha256']] = raw
    reasons = []
    for k in ('real_data_verified','history_complete','fixture_identity_checked','private_research_use_reviewed'):
        if review.get(k) is not True: reasons.append(k.upper())
    retrieved, checked, cutoff = (core.timestamp(s[k]) for k in ('retrieved_at_utc','fixture_checked_at_utc','complete_through_utc'))
    require(cutoff <= retrieved <= now and checked <= now, 'future/inconsistent source timestamps')
    kickoff = core.timestamp(f['kickoff_utc'])
    lead = (kickoff-now).total_seconds()/3600
    if not 23 <= lead <= 25: reasons.append('OUTSIDE_FROZEN_24H_WINDOW')
    if (now-retrieved).total_seconds() > 86400 or (now-cutoff).total_seconds() > 86400: reasons.append('STALE_OR_INCOMPLETE_HISTORY_SNAPSHOT')
    if (now-checked).total_seconds() > 86400: reasons.append('STALE_FIXTURE_CHECK')
    history=[]; seen=set(); quarantine=[]
    for h in q['history']:
        require(set(h) == {'competition','date','home','away','home_goals','away_goals','status'}, 'history schema mismatch')
        require(h['competition'] == f['competition'], 'mixed league history')
        d = date.fromisoformat(h['date']); k = (h['date'],h['home'],h['away'])
        require(k not in seen and h['home'] != h['away'], 'duplicate/self fixture'); seen.add(k)
        for v in ('home','away'): core.text(h[v])
        require(d <= cutoff.date() and d < now.date() and d < kickoff.date(), 'same-day/future history prohibited')
        require(all(type(h[v]) is int and h[v] >= 0 for v in ('home_goals','away_goals')), 'invalid goals')
        require(h['status'] in core.STATUSES, 'unknown historical status')
        known = (f['competition'],*k) in {('E1','2019-04-27','Bolton','Brentford'),('SP1','2023-12-11','Granada','Ath Bilbao')}
        if known or h['status'] != 'played_final':
            quarantine.append(k); continue
        history.append(Match(d,h['home'],h['away'],h['home_goals'],h['away_goals']))
    history.sort(key=lambda m:(m.match_date,m.home_team,m.away_team))
    nh=sum(m.home_team==f['home'] for m in history); na=sum(m.away_team==f['away'] for m in history)
    if len(history)<100 or min(nh,na)<5: reasons.append('INSUFFICIENT_HISTORY_SUPPORT')
    source = {'request_sha256':core.sha(request_raw), 'cutoff_utc':s['complete_through_utc'],
              'cutoff_date':None,'cutoff_precision':'utc', 'retrieved_at_utc':s['retrieved_at_utc'],
              'fixture_checked_at_utc':s['fixture_checked_at_utc'],
              'latest_match_date':str(history[-1].match_date) if history else None,
              'evidence_sha256':evidence, 'review':review, 'quarantined_fixtures':quarantine,
              'history_counts':{'fixtures':len(history),'home_venue':nh,'away_venue':na},
              'policy_sha256':core.sha(core.canonical(POLICY))}
    r = _base(f,now.isoformat(),now.isoformat(),'new_capture',POLICY['id'],source)
    if reasons: r.update(status='abstained',abstention_reasons=reasons)
    else:
        for filename,h in PINNED.items(): require(core.sha((Path(__file__).parent/filename).read_bytes())==h, 'frozen estimator changed')
        means={'plain':estimate_expected_goals(history,f['home'],f['away'],5.),
               'fixed180':estimate_decay_expected_goals(history,f['home'],f['away'],kickoff.date(),180.,5.)}
        for name,mu in means.items():
            filename='vendor_modelfc_goal_estimator.py' if name=='plain' else 'vendor_modelfc_decay_estimator.py'
            r['models'][name]={'version':PINNED[filename],'probabilities':probabilities(mu)}
        r['models']['venue_frequency']={'version':'beta11-venue-o15-v1','probabilities':[(sum(getattr(m,k)>=2 for m in history)+1)/(len(history)+2) for k in ('home_goals','away_goals')]}
    # Preserve supplied source bytes with the receipt, rather than depend on mutable paths.
    for k in ('history_evidence','fixture_evidence'):
        item=s[k]; dst=Path(store)/'evidence'/item['sha256']; raw=evidence_blobs[item['sha256']]
        if not dst.exists(): core.write_new(dst,raw)
        else: require(core.sha(dst.read_bytes())==item['sha256'], 'stored evidence mismatch')
    dst=Path(store)/'evidence'/source['request_sha256']
    if not dst.exists():core.write_new(dst,request_raw)
    return put_record(store,seal(r))

def export_pilot(store, *, now=None):
    """Verified legacy import only; original issuance times/probabilities survive."""
    now=now or now_utc(); catalog=core.load_catalog(); out=[]
    for old_id,item in catalog['fixtures'].items():
        ref=item['reference']; spec=next(s for s in core.ACTUAL if s['sha256']==ref['snapshot_sha256'])
        snap=read_json(spec['snapshot']); original=snap['fixtures'][ref['fixture_index']]
        f={'competition':ref['competition'],'season':ref['season'],'home':ref['home'],'away':ref['away'],
           'kickoff_utc':ref['original_kickoff_utc'],'provider_fixture_id':None}
        source={'legacy_reference':ref,'legacy_fixture_id':old_id,'snapshot_sha256':ref['snapshot_sha256'],
                'cutoff_utc':None,'cutoff_date':original['history_latest_date'],'cutoff_precision':'date',
                'limits':snap['source_limits'],'primary_cohort_eligible':False}
        r=_base(f,ref['issued_at_utc'],now.isoformat(),'preserved_legacy','legacy/'+ref['cohort'],source)
        for name in MODELS:
            r['models'][name]={'version':core.sha(core.canonical(ref['model_source_hashes'])) if name!='venue_frequency' else 'beta11-venue-o15-v1',
                               'probabilities':item['models'][name]['probabilities']}
        out.append(put_record(store,seal(r)))
    receipt={'legacy_issued':len(out),'export_ids':[r['record_id'] for r in out],
             'original_issuance_exclusions':catalog['issuance_exclusions'],'primary_cohort_eligible':False}
    core.write_new(Path(store)/'legacy_export_receipt.json',core.canonical(receipt)+b'\n')
    return receipt

def _load_forecasts(store):
    out={};slots=set()
    for p in sorted((Path(store)/'forecasts').glob('*.json')):
        r=validate_record(read_json(p));require(p.stem==r['record_id'],'filename/hash mismatch')
        slot=core.sha(core.canonical([r['cohort'],r['fixture_id']]))
        require(slot not in slots,'duplicate cohort fixture');slots.add(slot)
        require(read_json(Path(store)/'slots'/f'{slot}.json')['record_id']==r['record_id'],'uncommitted/mismatched forecast slot')
        out[r['record_id']]=r
    return out

def _validate_outcome(o, f, evidence, now):
    require(set(o)=={'forecast_record_id','status','home_goals','away_goals','actual_kickoff_utc','scheduled_kickoff_utc','completed_at_utc','observed_at_utc','evidence','supersedes','reason'}, 'outcome schema mismatch')
    require(o['forecast_record_id']==f['record_id'] and f['status']=='issued','unknown/abstained forecast')
    require(o['status'] in core.STATUSES,'unknown outcome status')
    observed=core.timestamp(o['observed_at_utc']);require(core.timestamp(f['issued_at_utc'])<=observed<=now,'outcome chronology')
    completed=None
    if o['scheduled_kickoff_utc'] is not None:
        require(core.timestamp(o['scheduled_kickoff_utc'])>core.timestamp(f['issued_at_utc']),'revised schedule precedes issuance')
    if o['status']=='played_final':
        require(o['scheduled_kickoff_utc'] is None,'final uses actual kickoff')
        require(all(type(o[k]) is int and o[k]>=0 for k in ('home_goals','away_goals')),'invalid regulation goals')
        kickoff=core.timestamp(o['actual_kickoff_utc']);completed=core.timestamp(o['completed_at_utc'])
        require(core.timestamp(f['issued_at_utc'])<kickoff<completed<=observed,'completion chronology')
    else:require(all(o[k] is None for k in ('home_goals','away_goals','actual_kickoff_utc','completed_at_utc')),'non-final result cannot score')
    require(bool(o['evidence']),'evidence required');seen=set()
    for e in o['evidence']:
        require(set(e)==core.EVIDENCE_KEYS,'evidence schema mismatch');u=urlsplit(e['source_url'])
        host=u.hostname.removeprefix('www.') if u.hostname else ''
        require(u.scheme=='https' and host in HOSTS[f['fixture']['competition']] and not u.username and not u.password and u.port in (None,443),'official competition source required')
        core.digest_text(e['sha256']);require(e['sha256'] not in seen,'duplicate evidence');seen.add(e['sha256'])
        if evidence is not None:require(core.sha(evidence(e['sha256']))==e['sha256'],'evidence hash mismatch')
        captured=core.timestamp(e['captured_at_utc']);verified=core.timestamp(e['verified_at_utc'])
        require(captured<=verified<=observed,'evidence chronology')
        if completed:require(completed<=captured,'evidence before completion')
        require(e['official_identity_and_result_checked'] is True and e['verified_status']==o['status'],'reviewer attestation required')
        core.text(e['verified_by']);core.text(e['verification_note'])
    if o['status']=='conflicting':require(len(seen)>=2,'conflict needs both sources')

def _result_envelope(r):
    require(set(r)=={'schema_version','sequence','previous_record_id','recorded_at_utc','outcome','record_id'} and type(r['schema_version']) is int and r['schema_version']==1,'result schema mismatch')
    require(type(r['sequence']) is int and r['sequence']>=1,'invalid result sequence')
    if r['previous_record_id'] is not None:core.digest_text(r['previous_record_id'])
    core.timestamp(r['recorded_at_utc']);core.digest_text(r['record_id'])

def _ledger(store, forecasts, expected_tail):
    require(expected_tail=='EMPTY' or isinstance(expected_tail,str) and len(expected_tail)==64,'retained tail required')
    rows=[];latest={};prev=None
    for i,p in enumerate(sorted((Path(store)/'results').glob('*.json')),1):
        r=read_json(p);_result_envelope(r);body={k:v for k,v in r.items() if k!='record_id'}
        require(r['record_id']==core.sha(core.canonical(body)) and r['previous_record_id']==prev and r['sequence']==i and p.name==f'{i:06d}.json','broken result chain')
        o=r['outcome'];f=forecasts[o['forecast_record_id']]
        _validate_outcome(o,f,lambda h:(Path(store)/'evidence'/h).read_bytes(),core.timestamp(r['recorded_at_utc']))
        parent=latest.get(f['record_id']);require(o['supersedes']==(parent['record_id'] if parent else None),'broken correction lineage')
        if parent:
            core.text(o['reason']);require(core.timestamp(o['observed_at_utc'])>=core.timestamp(parent['outcome']['observed_at_utc']),'correction moves backwards')
        if rows:require(core.timestamp(r['recorded_at_utc'])>=core.timestamp(rows[-1]['recorded_at_utc']),'ledger clock moved backwards')
        rows.append(r);latest[f['record_id']]=r;prev=r['record_id']
    require(expected_tail==(prev or 'EMPTY'),'ledger rollback/stale retained tail')
    return rows,latest

def append_result(store, outcome, evidence_paths, *, expected_tail, now=None):
    now=now or now_utc();root=Path(store)
    with core.locked(root):
        forecasts=_load_forecasts(root);rows,latest=_ledger(root,forecasts,expected_tail)
        f=forecasts[outcome['forecast_record_id']];blobs={h:Path(p).read_bytes() for h,p in evidence_paths.items()}
        _validate_outcome(outcome,f,lambda h:blobs[h],now)
        parent=latest.get(f['record_id']);require(outcome['supersedes']==(parent['record_id'] if parent else None),'stale correction parent')
        if parent:
            core.text(outcome['reason'])
            require(core.timestamp(outcome['observed_at_utc'])>=core.timestamp(parent['outcome']['observed_at_utc']),'correction moves backwards')
            semantic=lambda o:(o['status'],o['home_goals'],o['away_goals'],o['actual_kickoff_utc'],o['scheduled_kickoff_utc'],o['completed_at_utc'],sorted(e['sha256'] for e in o['evidence']))
            require(semantic(outcome)!=semantic(parent['outcome']),'duplicate/no-op result')
        if rows:require(now>=core.timestamp(rows[-1]['recorded_at_utc']),'ledger clock moved backwards')
        for h,raw in blobs.items():
            p=root/'evidence'/h
            if p.exists():require(core.sha(p.read_bytes())==h,'tampered stored evidence')
            else:core.write_new(p,raw)
        r=seal({'schema_version':1,'sequence':len(rows)+1,'previous_record_id':rows[-1]['record_id'] if rows else None,'recorded_at_utc':now.isoformat(),'outcome':outcome})
        core.write_new(root/'results'/f'{len(rows)+1:06d}.json',core.canonical(r)+b'\n');return r

def score(store, *, expected_tail):
    with core.locked(store):
        ff=_load_forecasts(store);records,latest=_ledger(store,ff,expected_tail)
    return _score_snapshot(ff,records,latest)

def _score_snapshot(ff,records,latest):
    groups={}
    for cohort in sorted({f['cohort'] for f in ff.values()}):
        for league in LEAGUES:
            fs=[f for f in ff.values() if f['cohort']==cohort and f['fixture']['competition']==league]
            if not fs:continue
            rows=[];statuses=Counter()
            for f in fs:
                r=latest.get(f['record_id']);status='abstained' if f['status']=='abstained' else r['outcome']['status'] if r else 'missing'
                statuses[status]+=1
                if status=='played_final':
                    o=r['outcome'];rows.append({'probabilities':{n:f['models'][n]['probabilities'] for n in MODELS},'outcomes':[int(o['home_goals']>=2),int(o['away_goals']>=2)]})
            groups[cohort+'/'+league]={'captured_fixtures':len(fs),'status_counts':dict(statuses),'metrics':core._metrics(rows)}
    return {'schema_version':1,'ledger_tail':records[-1]['record_id'] if records else None,'groups':groups,
            'interpretation':'Descriptive research monitoring only; no automatic significance, calibration, edge or promotion claim.'}

def draft(r):
    validate_record(r);f=r['fixture'];label='Legacy research forecast' if r['issuance_kind']=='preserved_legacy' else 'Experimental forecast'
    if r['status']=='abstained':return f"DRAFT — {f['competition']}: {f['home']} v {f['away']}. No forecast: {', '.join(r['abstention_reasons'])}."
    lines=[f"DRAFT — {label}: {f['home']} v {f['away']} ({f['competition']}).", 'Team goals over 1.5 (regulation):']
    for j,v in enumerate(('home','away')):lines.append(f"{f[v]}: plain {r['models']['plain']['probabilities'][j]:.1%}; recency {r['models']['fixed180']['probabilities'][j]:.1%}.")
    lines += [f"Issued {r['issued_at_utc']}. Research comparison, not a betting-value claim."]
    if r['issuance_kind']=='preserved_legacy':lines.append('Legacy input freshness/provenance limitations apply; not the new prospective cohort.')
    return '\n'.join(lines)

def draft_posts(r, limit=280):
    """Private thread draft with complete qualification on every standalone post.

    Pack whole semantic units, never split a warning across numbered posts.
    The bound counts Unicode code points, not platform-specific weighted length.
    """
    validate_record(r)
    require(type(limit) is int and limit>=100,'draft limit too small')
    f=r['fixture'];context=f"{f['home']} v {f['away']} ({f['competition']})."
    qualification='Research only; not a betting-value claim.'
    if r['issuance_kind']=='preserved_legacy':
        qualification+=' Legacy inputs: freshness/provenance limits; not prospective.'
    if r['status']=='abstained':
        context+=' No forecast.'
        units=[f'Reason: {reason}.' for reason in r['abstention_reasons']]
    else:
        units=[f"{f[v]} regulation goals O1.5: plain {r['models']['plain']['probabilities'][j]:.1%}; recency {r['models']['fixed180']['probabilities'][j]:.1%}." for j,v in enumerate(('home','away'))]
    units.append(f"Issued {r['issued_at_utc']}.")
    # Reserve numbering space before packing; reject overlong units without truncation.
    available=limit-len(context)-len(qualification)-30
    parts=[];current=''
    for unit in units:
        require(len(unit)<=available,'semantic draft unit exceeds limit; use long-form draft')
        candidate=(current+' '+unit).strip()
        if len(candidate)>available:parts.append(current);current=unit
        else:current=candidate
    if current:parts.append(current)
    posts=[f'DRAFT {i}/{len(parts)}: {context} {part} {qualification}' for i,part in enumerate(parts,1)]
    require(all(len(post)<=limit for post in posts),'draft numbering exceeds limit')
    return posts

def validate_odds_reference(quote, forecast, *, now=None):
    """Optional evidence contract only: no odds provider, value rank or ROI claim."""
    validate_record(forecast); now=now or now_utc()
    require(set(quote)=={'forecast_record_id','team','market','decimal_odds','bookmaker','quoted_at_utc','captured_at_utc','evidence_sha256'}, 'odds schema mismatch')
    require(quote['forecast_record_id']==forecast['record_id'] and forecast['status']=='issued','odds forecast mismatch')
    require(quote['team'] in ('home','away') and quote['market']==forecast['market'],'odds market mismatch')
    p=quote['decimal_odds'];require(type(p) in (float,int) and math.isfinite(p) and p>1,'invalid decimal odds')
    core.text(quote['bookmaker']);core.digest_text(quote['evidence_sha256'])
    q,c=core.timestamp(quote['quoted_at_utc']),core.timestamp(quote['captured_at_utc'])
    require(core.timestamp(forecast['issued_at_utc'])<=q<=c<=now and c<core.timestamp(forecast['fixture']['kickoff_utc']),'odds must be genuinely captured after issuance and before kickoff')
    return quote

def bundle(store, output, *, expected_tail, now=None):
    """Consistent complete store snapshot; no source datasets or synthetic samples."""
    now=now or now_utc();root=Path(store)
    with core.locked(root):
        ff=_load_forecasts(root);rr,latest=_ledger(root,ff,expected_tail)
        content={f'forecasts/{rid}.json':core.canonical(r)+b'\n' for rid,r in sorted(ff.items())}
        content.update({f"results/{r['sequence']:06d}.json":core.canonical(r)+b'\n' for r in rr})
        content['scores.json']=core.canonical(_score_snapshot(ff,rr,latest))+b'\n'
        if (root/'legacy_export_receipt.json').exists():content['legacy_export_receipt.json']=(root/'legacy_export_receipt.json').read_bytes()
        body={'contract_version':'deepfc.exchange/1.0.0','created_at_utc':now.isoformat(),
              'permitted_use':PERMITTED_USE,
              'forecast_count':len(ff),'result_count':len(rr),'result_tail':rr[-1]['record_id'] if rr else 'EMPTY',
              'policy':POLICY,'files':[{'path':n,'sha256':core.sha(raw),'bytes':len(raw)} for n,raw in sorted(content.items())],
              'evidence_delivery':'Evidence payloads retained by exporter; references/attestations included, not independent source authentication. Request authorized evidence transfer separately if consumer needs raw verification.'}
        manifest=dict(body,manifest_id=core.sha(core.canonical(body)));content['manifest.json']=core.canonical(manifest)+b'\n'
        # Build privately, then use existing atomic create-exclusive writer.
        import io
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for n,raw in sorted(content.items()):z.writestr(n,raw)
        core.write_new(Path(output),buf.getvalue())
    return {'manifest_id':manifest['manifest_id'],'bundle_sha256':core.sha(Path(output).read_bytes()),'forecast_count':len(ff),'result_count':len(rr)}

def verify_bundle(path, *, expected_sha256):
    raw=Path(path).read_bytes();require(core.sha(raw)==expected_sha256,'bundle digest mismatch')
    with zipfile.ZipFile(path) as z:
        names=z.namelist();require(len(names)==len(set(names)),'duplicate archive entry')
        m=_json(z.read('manifest.json'));body={k:v for k,v in m.items() if k!='manifest_id'}
        require(set(m)=={'contract_version','created_at_utc','permitted_use','forecast_count','result_count','result_tail','policy','files','evidence_delivery','manifest_id'},'manifest schema mismatch')
        require(m['contract_version']=='deepfc.exchange/1.0.0' and m['manifest_id']==core.sha(core.canonical(body)),'manifest mismatch')
        require(m['permitted_use']==PERMITTED_USE and m['policy']==POLICY,'unsupported permissions/policy')
        created=core.timestamp(m['created_at_utc']);core.text(m['evidence_delivery'])
        require(all(type(m[k]) is int and m[k]>=0 for k in ('forecast_count','result_count')),'invalid manifest counts')
        require(isinstance(m['files'],list) and len(m['files'])==len({f['path'] for f in m['files']}),'duplicate manifest path')
        require(set(names)=={'manifest.json'}|{f['path'] for f in m['files']},'unlisted or missing archive member')
        ff={};slots=set();rr=[]
        for f in m['files']:
            require(set(f)=={'path','sha256','bytes'} and type(f['bytes']) is int and f['bytes']>=0,'manifest member schema mismatch')
            core.digest_text(f['sha256'])
            n=f['path'];require(not n.startswith('/') and '..' not in Path(n).parts,'unsafe member path')
            require(n in ('scores.json','legacy_export_receipt.json') or n.startswith(('forecasts/','results/')),'unknown archive member')
            b=z.read(n);require(len(b)==f['bytes'] and core.sha(b)==f['sha256'],'member digest mismatch')
            if n.startswith('forecasts/'):
                r=validate_record(_json(b));require(n==f"forecasts/{r['record_id']}.json",'forecast path mismatch')
                require(core.timestamp(r['exported_at_utc'])<=created,'forecast after bundle creation')
                slot=(r['cohort'],r['fixture_id']);require(slot not in slots,'duplicate cohort fixture');slots.add(slot);ff[r['record_id']]=r
            elif n.startswith('results/'):rr.append((n,_json(b)))
        previous=None;latest={};last_recorded=None;ordered=[]
        for i,(n,r) in enumerate(sorted(rr),1):
            _result_envelope(r)
            require(n==f'results/{i:06d}.json' and r['sequence']==i and r['previous_record_id']==previous,'result chain mismatch')
            require(r['record_id']==core.sha(core.canonical({k:v for k,v in r.items() if k!='record_id'})),'result hash mismatch')
            o=r['outcome'];fid=o['forecast_record_id'];require(fid in ff and ff[fid]['status']=='issued','result join mismatch')
            recorded=core.timestamp(r['recorded_at_utc']);require(recorded<=created and (last_recorded is None or recorded>=last_recorded),'result clock mismatch')
            # No raw evidence is delivered: validate all semantics/attestations, not evidence bytes.
            _validate_outcome(o,ff[fid],None,recorded)
            parent=latest.get(fid)
            require(o['supersedes']==(parent['record_id'] if parent else None),'correction lineage mismatch')
            if parent:
                core.text(o['reason']);require(core.timestamp(o['observed_at_utc'])>=core.timestamp(parent['outcome']['observed_at_utc']),'correction moves backwards')
            latest[fid]=r;previous=r['record_id'];last_recorded=recorded;ordered.append(r)
        require(len(ff)==m['forecast_count'] and len(rr)==m['result_count'] and (previous or 'EMPTY')==m['result_tail'],'bundle totals mismatch')
        require('scores.json' in names and _json(z.read('scores.json'))==_score_snapshot(ff,ordered,latest),'derived score mismatch')
    return m

def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    for name in ('issue','export-pilot','score','append-result','bundle'):
        a=s.add_parser(name);a.add_argument('--store',required=True,type=Path)
        if name=='issue':a.add_argument('--request',required=True,type=Path)
        if name in ('score','append-result','bundle'):a.add_argument('--expected-tail',required=True)
        if name=='bundle':a.add_argument('--output',required=True,type=Path)
        if name=='append-result':a.add_argument('--outcome',required=True,type=Path);a.add_argument('--evidence-map',required=True,type=Path)
    a=s.add_parser('draft');a.add_argument('--forecast',required=True,type=Path)
    args=p.parse_args()
    if args.command=='issue':result=issue(args.request,args.store)
    elif args.command=='export-pilot':result=export_pilot(args.store)
    elif args.command=='append-result':result=append_result(args.store,read_json(args.outcome),read_json(args.evidence_map),expected_tail=args.expected_tail)
    elif args.command=='score':result=score(args.store,expected_tail=args.expected_tail)
    elif args.command=='bundle':result=bundle(args.store,args.output,expected_tail=args.expected_tail)
    else:print(core.canonical({'draft_posts':draft_posts(read_json(args.forecast)),'published':False}).decode());return
    print(core.canonical(result).decode())

if __name__=='__main__':main()
