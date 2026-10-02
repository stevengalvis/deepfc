"""Source-schema/quality audit only, no forecasting imports or scores."""
import csv,hashlib,json,math,subprocess,re
from collections import Counter
from datetime import datetime
from pathlib import Path
ROOT=Path('/workspace/shot-data-mirror-liam')
OUT=Path('experiments/results/e0_feasibility')
def numeric(s,odds=False):
    try:
        x=float(s);return math.isfinite(x) and (x>1 if odds else x>=0 and x.is_integer())
    except (ValueError,TypeError):return False

def run():
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();records=[];globalkeys=set()
    for y in range(2017,2026):
        rel=f'data/ENGLAND/Premier league/GAMES/{y}-{y+1}.csv';p=ROOT/rel;raw=p.read_bytes()
        reader=csv.DictReader(raw.decode('utf-8-sig').splitlines());fields=reader.fieldnames;rows=list(reader)
        odds=['BbAvH','BbAvD','BbAvA'] if y<2019 else ['AvgH','AvgD','AvgA']
        required=['Div','Date','HomeTeam','AwayTeam','HC','AC','HS','AS','HST','AST']+odds
        checks={f:{'present':f in fields,'blank':sum(not str(r.get(f,'')).strip() for r in rows),'invalid':sum(not numeric(r.get(f),f in odds) for r in rows)} for f in ['HC','AC','HS','AS','HST','AST']+odds}
        dates=[];bad_date=[];keys=[];anomalies=[]
        for i,r in enumerate(rows,2):
            d=None
            for fmt in ['%d/%m/%Y','%d/%m/%y']:
                try:d=datetime.strptime(r['Date'],fmt).date();break
                except ValueError:pass
            if d is None:bad_date.append(i)
            else:dates.append(str(d))
            k=(str(d),r['HomeTeam'],r['AwayTeam']);keys.append(k)
            if k in globalkeys:anomalies.append({'row':i,'reason':'duplicate across source files'})
            globalkeys.add(k)
            for shot,target in [('HS','HST'),('AS','AST')]:
                if numeric(r.get(shot)) and numeric(r.get(target)) and float(r[target])>float(r[shot]):anomalies.append({'row':i,'fixture':list(k),'reason':target+' exceeds '+shot})
        teams=Counter(t for r in rows for t in [r['HomeTeam'],r['AwayTeam']]);paircounts=Counter((r['HomeTeam'],r['AwayTeam']) for r in rows)
        records.append({'season':f'{y}/{y+1}','path':rel,'mirror_commit':commit,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),
        'mirror_url':f'https://github.com/liammcdade/Footballdata/blob/{commit}/'+rel.replace(' ','%20'),
        'primary_url':f'https://www.football-data.co.uk/mmz4281/{str(y)[2:]}{str(y+1)[2:]}/E0.csv','primary_hash_verified':False,
        'rows':len(rows),'dates':[min(dates),max(dates)],'invalid_dates':bad_date,'wrong_division':sum(r['Div']!='E0' for r in rows),
        'missing_columns':sorted(set(required)-set(fields)),'fields':checks,'quote_family':odds,
        'complete_corner_rows':sum(all(numeric(r.get(f)) for f in ['HC','AC']) for r in rows),
        'valid_odds_triplets':sum(all(numeric(r.get(f),True) for f in odds) for r in rows),
        'team_appearances':dict(sorted(teams.items())),'team_count':len(teams),'duplicate_fixture_keys':len(keys)-len(set(keys)),
        'unique_ordered_team_pairs':len(paircounts),'pair_count_not_one':sum(n!=1 for n in paircounts.values()),
        'blank_or_identical_teams':sum(not r['HomeTeam'].strip() or not r['AwayTeam'].strip() or r['HomeTeam']==r['AwayTeam'] for r in rows),
        'anomalies':anomalies,'timestamp_fields':[f for f in fields if 'stamp' in f.lower() or 'updated' in f.lower()],'kickoff_time_present':'Time' in fields})
    names=sorted({n for r in records for n in r['team_appearances']});norm=lambda n:re.sub('[^a-z0-9]','',n.lower())
    aliases=[(a,b) for i,a in enumerate(names) for b in names[i+1:] if norm(a)==norm(b)]
    (OUT/'inventory.json').write_text(json.dumps({'files':records,'team_names':names,'normalized_name_collisions':aliases,'scope':'Schema, missingness and validity only. No model fitting/prediction/scoring.'},indent=2)+'\n')
    for r in records:print(r['season'],r['rows'],r['team_count'],'corners',r['complete_corner_rows'],'odds',r['valid_odds_triplets'],'missing',r['missing_columns'],'anomalies',r['anomalies'])
if __name__=='__main__':run()
