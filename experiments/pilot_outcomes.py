"""Private research outcome linker for frozen team-goals O1.5 snapshots.

No forecasting, model imports, providers, fitting, or production integrations.
Official evidence is locally retained and explicitly attested by a reviewer;
this module validates that attestation and its bytes, not the website's truth.
"""
from __future__ import annotations
import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit

MODELS = ('plain', 'fixed180', 'venue_frequency')
MARKETS = ['home_team_goals_over1.5', 'away_team_goals_over1.5']
BASE = Path('/workspace/private-research-inputs')
ACTUAL = (
    {'snapshot': str(BASE/'epl-prematch-pilot-20261003/PRIMARY_SNAPSHOT.json'),
     'sha256': '14bd7fa60f6cc319808ec4427292c9def5a156efc9d6d4ac19e3ca7d2bdb0eb1',
     'cohort': 'original_five', 'issued_count': 5, 'competition': 'E0', 'season': '2026/27'},
    {'snapshot': str(BASE/'epl-prematch-amendment-20261003/AMENDMENT_SNAPSHOT.json'),
     'sha256': '29cea9794f6567ffbe614cc706edc0371a6da5603db8e0f8b073ba8aca1e773b',
     'cohort': 'additive_three', 'issued_count': 3, 'competition': 'E0', 'season': '2026/27'},
)
STATUSES = {'played_final', 'postponed', 'abandoned', 'awarded', 'cancelled', 'conflicting'}
OFFICIAL_HOSTS = {'premierleague.com', 'www.premierleague.com', 'thefa.com', 'www.thefa.com'}
OUTCOME_KEYS = {'fixture_id','snapshot_sha256','competition','season','home','away','status',
                'actual_kickoff_utc','completed_at_utc','scheduled_kickoff_utc',
                'home_goals','away_goals','observed_at_utc','evidence','action','supersedes','reason'}
EVIDENCE_KEYS = {'source_url','sha256','captured_at_utc','verified_at_utc','verified_by',
                 'verification_note','verified_status','official_identity_and_result_checked'}

class Invalid(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise Invalid(message)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_json(path):
    def pairs(items):
        out = {}
        for k,v in items:
            require(k not in out, 'duplicate JSON key')
            out[k] = v
        return out
    return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs,
                      parse_constant=lambda v: (_ for _ in ()).throw(Invalid('nonfinite JSON')))

def timestamp(value):
    require(isinstance(value,str), 'timestamp must be text')
    try:
        dt = datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as exc:
        raise Invalid('invalid timestamp') from exc
    require(dt.tzinfo is not None and dt.utcoffset().total_seconds() == 0, 'UTC timestamp required')
    return dt

def digest_text(value):
    require(isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value), 'invalid SHA256')

def text(value):
    require(isinstance(value,str) and bool(value.strip()), 'nonempty text required')

def load_catalog(specs=ACTUAL):
    fixtures = {}; exclusions = []; snapshots = []; identities = set(); previous = None
    for spec in specs:
        path = Path(spec['snapshot']); raw = path.read_bytes()
        require(sha(raw)==spec['sha256'], 'snapshot hash mismatch')
        snap = read_json(path); proto_path = path.parent/'PROTOCOL_FREEZE.json'
        proto_raw = proto_path.read_bytes(); proto = read_json(proto_path)
        require(sha(proto_raw)==snap['protocol_sha256'], 'protocol hash mismatch')
        for key, filename in [('pre_review_sha256','PRE_REVIEW.json'),('fixture_sha256','fixtures.json'),('derived_data_sha256','current_derived_E0.json')]:
            require(sha((path.parent/filename).read_bytes())==snap[key], filename+' hash mismatch')
        require(snap['schema_version']==1, 'unsupported snapshot schema')
        expected_type = 'private_exploratory_prematch_primary_issuance' if previous is None else 'private_exploratory_prematch_additive_amendment'
        require(snap['record_type']==expected_type, 'snapshot record type mismatch')
        if previous is not None:
            require(snap['original_snapshot_sha256']==previous, 'amendment parent mismatch')
        else:
            previous = spec['sha256']
        issued = timestamp(snap['issued_at_utc']); captured = timestamp(snap['capture_completed_utc'])
        require(issued<=captured, 'snapshot capture before issuance')
        text(proto['models']); model_hashes = {k:v for k,v in proto['hashes'].items() if Path(k).name in {'vendor_modelfc_goal_estimator.py','vendor_modelfc_decay_estimator.py'}}
        require(len(model_hashes)==2, 'missing frozen model identities')
        for v in model_hashes.values():digest_text(v)
        count = 0
        for index, f in enumerate(snap['fixtures']):
            if f['status']=='EXCLUDED':
                exclusions.append({'cohort':spec['cohort'],'fixture_index':index,'reason':f['reason'],
                                   'home':f.get('home_canonical') or f['home_display'],
                                   'away':f.get('away_canonical') or f['away_display']})
                continue
            require(f['status']=='ISSUED', 'unknown issuance status')
            kickoff = timestamp(f['kickoff_utc'])
            require(timestamp(f['issuance_utc'])==issued and captured<kickoff, 'not frozen before original kickoff')
            require(f['market_order']==MARKETS and set(f['models'])==set(MODELS), 'market/model mismatch')
            for team in (f['home_canonical'],f['away_canonical']):text(team)
            require(f['home_canonical']!=f['away_canonical'], 'self fixture')
            identity=(spec['competition'],spec['season'],f['home_canonical'],f['away_canonical'],f['kickoff_utc'])
            require(identity not in identities, 'duplicate issued fixture');identities.add(identity)
            for name in MODELS:
                probabilities = f['models'][name]['probabilities']
                require(isinstance(probabilities,list) and len(probabilities)==2, 'two probabilities required')
                require(all(type(p) in (int,float) and math.isfinite(p) and 0<=p<=1 for p in probabilities), 'invalid frozen probability')
            ref={'snapshot_sha256':spec['sha256'],'protocol_sha256':snap['protocol_sha256'],
                 'fixture_index':index,'cohort':spec['cohort'],'competition':spec['competition'],'season':spec['season'],
                 'home':f['home_canonical'],'away':f['away_canonical'],'original_kickoff_utc':f['kickoff_utc'],
                 'issued_at_utc':snap['issued_at_utc'],'capture_completed_utc':snap['capture_completed_utc'],
                 'model_description':proto['models'],'model_source_hashes':model_hashes,
                 'derived_data_sha256':snap['derived_data_sha256'],'market_order':MARKETS}
            fid=sha(canonical(ref));fixtures[fid]={'reference':ref,'models':f['models']};count+=1
        require(count==spec['issued_count'], 'issued cohort count mismatch')
        snapshots.append({'cohort':spec['cohort'],'sha256':spec['sha256'],'protocol_sha256':snap['protocol_sha256'],'issued':count})
    return {'fixtures':fixtures,'snapshots':snapshots,'issuance_exclusions':exclusions}

def _outcome_check(o, catalog, latest, now, evidence_bytes):
    require(set(o)==OUTCOME_KEYS, 'outcome schema mismatch')
    require(o['fixture_id'] in catalog['fixtures'], 'unknown/excluded fixture')
    ref=catalog['fixtures'][o['fixture_id']]['reference']
    for key in ['snapshot_sha256','competition','season','home','away']:
        require(o[key]==ref[key], key+' mismatch')
    require(o['status'] in STATUSES, 'unknown outcome status')
    require(o['action'] in {'initial','update','correction'}, 'unknown action')
    old=latest.get(o['fixture_id'])
    if old is None:
        require(o['action']=='initial' and o['supersedes'] is None, 'first record must be initial')
    else:
        require(o['action']!='initial', 'duplicate/conflicting initial record; use explicit update/correction')
        require(o['supersedes']==old['record_id'], 'stale/mismatched correction parent')
        text(o['reason'])
        semantic = lambda v: (v['status'],v['home_goals'],v['away_goals'],v['actual_kickoff_utc'],v['completed_at_utc'],v['scheduled_kickoff_utc'],sorted(e['sha256'] for e in v['evidence']))
        require(semantic(o)!=semantic(old['outcome']), 'duplicate observation has no new status/result/schedule/evidence')
        if o['action']=='update':
            require(old['outcome']['status'] in {'postponed','abandoned'}, 'terminal/conflicting result requires correction')
        require(timestamp(o['observed_at_utc'])>=timestamp(old['outcome']['observed_at_utc']), 'observation predates previous record')
    require(o['reason'] is None or isinstance(o['reason'],str), 'invalid reason')
    observed=timestamp(o['observed_at_utc'])
    require(timestamp(ref['issued_at_utc'])<=observed<=now, 'future/pre-issuance observation')
    if o['scheduled_kickoff_utc'] is not None:
        require(timestamp(o['scheduled_kickoff_utc'])>timestamp(ref['capture_completed_utc']), 'schedule predates capture')
    completed=None
    if o['status']=='played_final':
        require(o['scheduled_kickoff_utc'] is None, 'final uses actual kickoff, not proposed schedule')
        require(type(o['home_goals']) is int and type(o['away_goals']) is int and min(o['home_goals'],o['away_goals'])>=0, 'invalid regulation goals')
        kickoff=timestamp(o['actual_kickoff_utc']);completed=timestamp(o['completed_at_utc'])
        require(timestamp(ref['capture_completed_utc'])<kickoff<completed<=observed, 'invalid actual-match chronology')
    else:
        require(all(o[k] is None for k in ['home_goals','away_goals','actual_kickoff_utc','completed_at_utc']), 'non-final status cannot carry scoring goals/times')
    require(isinstance(o['evidence'],list) and len(o['evidence'])>0, 'official evidence required')
    hashes=[]
    for e in o['evidence']:
        require(set(e)==EVIDENCE_KEYS, 'evidence schema mismatch')
        u=urlsplit(e['source_url'])
        require(u.scheme=='https' and u.hostname in OFFICIAL_HOSTS and not u.username and not u.password and u.port in (None,443), 'official HTTPS source required')
        digest_text(e['sha256']);hashes.append(e['sha256'])
        raw=evidence_bytes(e['sha256']);require(raw and sha(raw)==e['sha256'], 'missing/tampered evidence bytes')
        captured=timestamp(e['captured_at_utc']);verified=timestamp(e['verified_at_utc'])
        require(captured<=verified<=observed, 'evidence verification chronology mismatch')
        if completed is not None:require(completed<=captured, 'final evidence predates completion')
        require(e['official_identity_and_result_checked'] is True and e['verified_status']==o['status'], 'explicit official status/identity/result attestation required')
        text(e['verified_by']);text(e['verification_note'])
    require(len(hashes)==len(set(hashes)), 'duplicate evidence')
    if o['status']=='conflicting':require(len(hashes)>=2, 'conflicting status needs both conflicting evidence captures')
    return ref

def read_ledger(catalog, ledger, *, expected_tail=None):
    ledger=Path(ledger);records=[];latest={};previous=None
    paths=sorted((ledger/'records').glob('*.json')) if ledger.exists() else []
    for i,path in enumerate(paths,1):
        r=read_json(path)
        require(set(r)=={'schema_version','sequence','previous_record_id','recorded_at_utc','forecast_reference','outcome','record_id'}, 'ledger schema mismatch')
        require(path.name==f'{i:06d}.json' and r['sequence']==i and r['previous_record_id']==previous, 'broken append-only chain')
        core={k:v for k,v in r.items() if k!='record_id'}
        require(r['schema_version']==1 and sha(canonical(core))==r['record_id'], 'record tampered')
        now=timestamp(r['recorded_at_utc'])
        if records:require(now>=timestamp(records[-1]['recorded_at_utc']), 'ledger clock moved backwards')
        ref=_outcome_check(r['outcome'],catalog,latest,now,lambda h:(ledger/'evidence'/h).read_bytes())
        require(r['forecast_reference']==ref, 'forecast provenance mismatch')
        records.append(r);latest[r['outcome']['fixture_id']]=r;previous=r['record_id']
    if expected_tail is not None:
        require(expected_tail == (previous or 'EMPTY'), 'ledger tail differs from retained receipt')
    return records,latest

@contextmanager
def locked(ledger):
    ledger=Path(ledger);ledger.mkdir(parents=True,exist_ok=True)
    with (ledger/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        try:yield ledger
        finally:fcntl.flock(lock,fcntl.LOCK_UN)

def write_new(path, raw):
    """Atomic visibility plus create-exclusive destination; never replace records."""
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.pending-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        os.link(name,path)
        directory=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:Path(name).unlink(missing_ok=True)

def append_outcome(catalog, ledger, outcome, evidence_paths, *, expected_tail, now=None):
    """Append one attested observation; evidence_paths maps declared SHA to file."""
    require(expected_tail == 'EMPTY' or isinstance(expected_tail,str) and len(expected_tail)==64, 'retained ledger receipt required')
    now=now or datetime.now(timezone.utc);timestamp(now.isoformat())
    # Freeze supplied bytes once before validation/storage (avoid mutable external-path rereads).
    blobs={h:Path(p).read_bytes() for h,p in evidence_paths.items()}
    with locked(ledger) as root:
        records,latest=read_ledger(catalog,root,expected_tail=expected_tail)
        ref=_outcome_check(outcome,catalog,latest,now,lambda h:blobs[h])
        if records:require(now>=timestamp(records[-1]['recorded_at_utc']), 'ledger clock moved backwards')
        for e in outcome['evidence']:
            h=e['sha256'];path=root/'evidence'/h
            if path.exists():require(sha(path.read_bytes())==h, 'stored evidence tampered')
            else:write_new(path,blobs[h])
        core={'schema_version':1,'sequence':len(records)+1,'previous_record_id':records[-1]['record_id'] if records else None,
              'recorded_at_utc':now.isoformat(),'forecast_reference':ref,'outcome':outcome}
        record=dict(core,record_id=sha(canonical(core)))
        write_new(root/'records'/f'{len(records)+1:06d}.json',canonical(record)+b'\n')
        return record

def _metrics(rows):
    if not rows:return None
    out={}
    for name in MODELS:
        venues={}
        for j,v in enumerate(['home','away']):
            ps=[r['probabilities'][name][j] for r in rows];ys=[r['outcomes'][j] for r in rows]
            assigned=[p if y else 1-p for p,y in zip(ps,ys)];impossible=sum(p==0 for p in assigned)
            venues[v]={'brier':sum((p-y)**2 for p,y in zip(ps,ys))/len(rows),
                       'binary_logloss':None if impossible else sum(-math.log(p) for p in assigned)/len(rows),
                       'infinite_logloss_events':impossible,'mean_probability':sum(ps)/len(rows),
                       'event_rate':sum(ys)/len(rows),'calibration_gap':sum(p-y for p,y in zip(ps,ys))/len(rows)}
        impossible=sum(v['infinite_logloss_events'] for v in venues.values())
        out[name]={'brier':(venues['home']['brier']+venues['away']['brier'])/2,
                   'binary_logloss':None if impossible else sum(v['binary_logloss'] for v in venues.values())/2,
                   'infinite_logloss_events':impossible,'venues':venues}
    paired={}
    for a,b in [('fixed180','plain'),('plain','venue_frequency'),('fixed180','venue_frequency')]:
        differences=[sum((r['probabilities'][a][j]-r['outcomes'][j])**2-(r['probabilities'][b][j]-r['outcomes'][j])**2 for j in range(2))/2 for r in rows]
        paired[a+'_minus_'+b]={'fixture_weighted_brier_difference':sum(differences)/len(rows),
                             'home':out[a]['venues']['home']['brier']-out[b]['venues']['home']['brier'],
                             'away':out[a]['venues']['away']['brier']-out[b]['venues']['away']['brier']}
    return {'fixtures':len(rows),'events':2*len(rows),'models':out,'paired':paired}

def score(catalog, ledger, *, expected_tail):
    require(expected_tail == 'EMPTY' or isinstance(expected_tail,str) and len(expected_tail)==64, 'retained ledger receipt required')
    # Readers take the same lock: a consistent tail and no half-written record reads.
    with locked(ledger):records,latest=read_ledger(catalog,ledger,expected_tail=expected_tail)
    rows=[];excluded=[]
    for fid,f in catalog['fixtures'].items():
        r=latest.get(fid);ref=f['reference'];status=r['outcome']['status'] if r else 'missing'
        if status!='played_final':
            excluded.append({'fixture_id':fid,'cohort':ref['cohort'],'reason':status,'record_id':r['record_id'] if r else None});continue
        o=r['outcome'];rows.append({'fixture_id':fid,'cohort':ref['cohort'],'record_id':r['record_id'],
                                   'reference':ref,'outcomes':[int(o['home_goals']>=2),int(o['away_goals']>=2)],
                                   'probabilities':{n:f['models'][n]['probabilities'] for n in MODELS}})
    return {'schema_version':1,'snapshots':catalog['snapshots'],'ledger_records':len(records),
            'ledger_tail':records[-1]['record_id'] if records else None,
            'coverage':{'issued_fixtures':len(catalog['fixtures']),'scored_fixtures':len(rows),'scored_events':2*len(rows),
                        'excluded_by_reason':dict(Counter(r['reason'] for r in excluded))},
            'issuance_exclusions':catalog['issuance_exclusions'],'outcome_exclusions':excluded,
            'all':_metrics(rows),'cohorts':{s['cohort']:{'issued':s['issued'],'scored':sum(r['cohort']==s['cohort'] for r in rows),
                       'metrics':_metrics([r for r in rows if r['cohort']==s['cohort']])} for s in catalog['snapshots']},
            'fixtures':rows,'inference':'Descriptive pilot only; no significance, promotion, profit or calibration-fit claim.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('inspect')
    add=sub.add_parser('append');add.add_argument('--ledger',type=Path,required=True);add.add_argument('--outcome',type=Path,required=True);add.add_argument('--evidence-map',type=Path,required=True);add.add_argument('--expected-tail',required=True,help='Previously retained record_id, or EMPTY for a new ledger')
    s=sub.add_parser('score');s.add_argument('--ledger',type=Path,required=True);s.add_argument('--output',type=Path,required=True);s.add_argument('--expected-tail',required=True,help='Previously retained record_id, or EMPTY')
    args=parser.parse_args();catalog=load_catalog()
    if args.command=='inspect':print(json.dumps(catalog,indent=2,allow_nan=False))
    elif args.command=='append':print(json.dumps(append_outcome(catalog,args.ledger,read_json(args.outcome),read_json(args.evidence_map),expected_tail=args.expected_tail),indent=2,allow_nan=False))
    else:
        result=score(catalog,args.ledger,expected_tail=args.expected_tail);write_new(args.output,json.dumps(result,indent=2,allow_nan=False).encode()+b'\n');print(args.output)

if __name__=='__main__':main()
