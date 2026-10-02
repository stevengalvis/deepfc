"""Data quality only; does not import or run forecasting models."""
import csv,hashlib,json,math,subprocess
from pathlib import Path
from datetime import date
from collections import defaultdict,Counter
SOURCE=Path('/workspace/shot-data-mirror-xgabora/data/Matches.csv')
OUT=Path('experiments/results/d2_coverage')

def invalid(x):
    try:
        v=float(x)
        return not math.isfinite(v) or v<0 or not v.is_integer()
    except (ValueError,TypeError):return True

def run():
    groups=defaultdict(list)
    with SOURCE.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f);headers=reader.fieldnames
        for row in reader:
            if row['Division']!='D2':continue
            d=date.fromisoformat(row['MatchDate'])
            if date(2017,7,1)<=d<date(2026,7,1):groups[d.year if d.month>=7 else d.year-1].append(row)
    stats={}
    fields=['HomeCorners','AwayCorners','HomeShots','AwayShots','HomeTarget','AwayTarget']
    for year,rows in sorted(groups.items()):
        keys=[(r['MatchDate'],r['HomeTeam'],r['AwayTeam']) for r in rows]
        shots_bad=sum(not any(invalid(r[f]) for f in ['HomeShots','AwayShots','HomeTarget','AwayTarget']) and (float(r['HomeTarget'])>float(r['HomeShots']) or float(r['AwayTarget'])>float(r['AwayShots'])) for r in rows)
        stats[str(year)]={'rows':len(rows),'dates':[min(r['MatchDate'] for r in rows),max(r['MatchDate'] for r in rows)],
            'teams':len({r[t] for r in rows for t in ['HomeTeam','AwayTeam']}),'team_appearance_counts':dict(Counter(r[t] for r in rows for t in ['HomeTeam','AwayTeam'])),'duplicate_fixture_rows':len(keys)-len(set(keys)),
            'blank_team_rows':sum(not r['HomeTeam'].strip() or not r['AwayTeam'].strip() for r in rows),
            'same_team_rows':sum(r['HomeTeam']==r['AwayTeam'] for r in rows),
            'fields':{f:{'blank':sum(not r[f].strip() for r in rows),'invalid_including_blank':sum(invalid(r[f]) for r in rows)} for f in fields},
            'shots_on_target_exceeds_shots_rows':shots_bad,
            'required_market_average_columns_absent':[f for f in ['AvgH','AvgD','AvgA'] if f not in headers]}
    result={'mirror':'https://github.com/xgabora/Club-Football-Match-Data-2000-2025',
      'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE.parent.parent,text=True).strip(),
      'source_path':'data/Matches.csv','sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'bytes':SOURCE.stat().st_size,
      'headers':headers,'window_labels':'July1-June30 calendar windows; merged file supplies no source season column.',
      'odds_provenance':'README identifies OddHome/OddDraw/OddAway as Bet365, not AvgH/D/A. Not accepted as a substitution.',
      'primary_hash_verified':False,'seasons':stats}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'inventory.json').write_text(json.dumps(result,indent=2)+'\n')
    print('commit',result['commit'],'sha256',result['sha256'])
    for y,v in stats.items():print(y,v['rows'],v['teams'],'invalid stats',sum(x['invalid_including_blank'] for x in v['fields'].values()),'duplicate',v['duplicate_fixture_rows'],'shot consistency',v['shots_on_target_exceeds_shots_rows'])

if __name__=='__main__':run()
