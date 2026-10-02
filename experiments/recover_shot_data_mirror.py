"""Recover exact archived CSV bytes from a pinned public mirror; fail on hash mismatch."""
import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from deepfc.football_data_csv import load_football_data_csv, _parse_date
from experiments.shot_reconstruction import load_shots

COMMIT='84eb7985dc4b842a62f2169eb6a5c2986834932f'
REPO='https://github.com/liammcdade/Footballdata'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mirror_checkout',type=Path)
    args=parser.parse_args()
    assert subprocess.check_output(['git','-C',str(args.mirror_checkout),'rev-parse','HEAD'],text=True).strip()==COMMIT
    out=Path('experiments/results/shot_reconstruction')
    expected=json.loads((out/'data_manifest.json').read_text())
    records=[]
    for year, prior in zip(range(2017,2026),expected,strict=True):
        relative=f'data/ENGLAND/championship/games/{year}-{year+1}.csv'
        # Read pinned Git object, not a potentially edited working file.
        raw=subprocess.check_output(['git','-C',str(args.mirror_checkout),'show',f'{COMMIT}:{relative}'])
        restored=raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
        digest=hashlib.sha256(restored).hexdigest()
        assert digest==prior['archived_sha256'], f'archived hash mismatch for {year}'
        path=Path(prior['path']);path.parent.mkdir(exist_ok=True);path.write_bytes(restored)
        rows=list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')))
        assert len(rows)==552
        assert {'HS','AS','HST','AST','HC','AC','Date','Div','HomeTeam','AwayTeam'} <= rows[0].keys()
        dates=[_parse_date(r['Date']) for r in rows]
        assert all(r['Div']=='E1' for r in rows)
        assert all(datetime(year,7,1).date() <= d < datetime(year+1,8,1).date() for d in dates)
        records.append(dict(path=str(path),primary_url=prior['url'],mirror_url=f'{REPO}/blob/{COMMIT}/{relative}',
            mirror_commit=COMMIT,mirror_raw_sha256=hashlib.sha256(raw).hexdigest(),sha256=digest,
            matches_archived_hash=True,transformation='LF to CRLF only',rows=len(rows),
            date_min=str(min(dates)),date_max=str(max(dates)),
            retrieved_at=datetime.now(timezone.utc).isoformat()))
    paths=[Path(r['path']) for r in records]
    loaded=load_football_data_csv(paths)
    assert (loaded.rows_read,loaded.rows_loaded,loaded.rows_without_corner_results)==(4968,4967,1)
    blanks=[]
    for p in paths:
        for r in csv.DictReader(p.open(encoding='utf-8-sig',newline='')):
            if not r['HC'].strip() and not r['AC'].strip():
                blanks.append([r['Date'],r['HomeTeam'],r['AwayTeam']])
    assert blanks==[['27/04/2019','Bolton','Brentford']]
    shots,excluded=load_shots(paths,loaded.matches)
    report=dict(files=records,rows_read=loaded.rows_read,rows_loaded=loaded.rows_loaded,
        blank_corner_rows=blanks,shot_fixtures=len(shots),excluded_shot_rows=excluded)
    (out/'verified_data_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))

if __name__=='__main__':main()
