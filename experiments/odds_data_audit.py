"""Inventory verified odds only; no outcomes modeled or candidate fitted."""
import csv,json,hashlib,math,statistics
from pathlib import Path

def value(row,key):
    try:
        x=float(row.get(key,''));return x if math.isfinite(x) else None
    except (ValueError,TypeError):return None

def valid(row,cols):return all(value(row,c) is not None and value(row,c)>1 for c in cols)
def summary(xs):
    if not xs:return None
    xs=sorted(xs);return {'n':len(xs),'min':xs[0],'median':statistics.median(xs),'p95':xs[int(.95*(len(xs)-1))],'max':xs[-1]}

def run():
    records=[];fieldrows=[]
    expected={r['path']:r['sha256'] for r in json.loads(Path('experiments/results/shot_reconstruction/verified_data_manifest.json').read_text())['files']}
    for path in sorted(Path('data').glob('E1_*.csv')):
        digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest==expected[str(path)]
        reader=csv.DictReader(path.open(encoding='utf-8-sig'));rows=list(reader);headers=reader.fieldnames
        fields=headers[headers.index('AR')+1:]
        old='BbAvH' in headers;avg=['BbAvH','BbAvD','BbAvA'] if old else ['AvgH','AvgD','AvgA']
        groups={'bet365_pre_1x2':['B365H','B365D','B365A'],'pinnacle_pre_1x2':['PSH','PSD','PSA'],
            'average_pre_1x2':avg,'average_close_1x2':['AvgCH','AvgCD','AvgCA'],
            'pinnacle_close_1x2':['PSCH','PSCD','PSCA'],'bet365_close_1x2':['B365CH','B365CD','B365CA'],
            'average_pre_goals':['BbAv>2.5','BbAv<2.5'] if old else ['Avg>2.5','Avg<2.5'],
            'average_close_goals':['AvgC>2.5','AvgC<2.5'],
            'average_pre_ah':['BbAvAHH','BbAvAHA'] if old else ['AvgAHH','AvgAHA'],
            'average_close_ah':['AvgCAHH','AvgCAHA']}
        counts={}
        for name,cols in groups.items():
            line=('BbAHh' if old else 'AHh') if name=='average_pre_ah' else 'AHCh' if name=='average_close_ah' else None
            present=all(c in headers for c in cols) and (line is None or line in headers)
            accepted=[r for r in rows if valid(r,cols) and (line is None or value(r,line) is not None)] if present else []
            counts[name]={'columns':cols,'line_column':line,'present':present,'valid_complete':len(accepted),'missing_or_invalid':len(rows)-len(accepted),'implied_probability_sum':summary([sum(1/value(r,c) for c in cols) for r in accepted])}
        for f in fields:
            xs=[value(r,f) for r in rows];line_or_count=f in ['Bb1X2','BbOU','BbAH','BbAHh','AHh','AHCh']
            fieldrows.append({'season':path.stem,'field':f,'rows':len(rows),'blank':sum(not str(r.get(f,'') or '').strip() for r in rows),'invalid_nonblank':sum(bool(str(r.get(f,'') or '').strip()) and (value(r,f) is None or (not line_or_count and value(r,f)<=1)) for r in rows),'valid':sum(x is not None and (line_or_count or x>1) for x in xs)})
        norm=lambda r,cols:[(1/value(r,c))/sum(1/value(r,k) for k in cols) for c in cols]
        diffs=[max(abs(a-b) for a,b in zip(norm(r,avg),norm(r,groups['bet365_pre_1x2']))) for r in rows if valid(r,avg) and valid(r,groups['bet365_pre_1x2'])]
        maxima=['BbMxH','BbMxD','BbMxA'] if old else ['MaxH','MaxD','MaxA']
        violations=sum(value(r,a)>value(r,m) for r in rows for a,m in zip(avg,maxima) if value(r,a) is not None and value(r,m) is not None)
        closing=groups['pinnacle_close_1x2'];pre=groups['pinnacle_pre_1x2']
        both=[r for r in rows if valid(r,pre) and valid(r,closing)]
        records.append({'season':path.stem,'rows':len(rows),'sha256':digest,'groups':counts,'all_odds_fields':fields,
          'bet365_vs_average_max_normalized_probability_difference':summary(diffs),'average_exceeds_max_1x2_cells':violations,
          'pinnacle_pre_close_comparable':len(both),'pinnacle_pre_close_identical_triplets':sum(all(value(r,a)==value(r,b) for a,b in zip(pre,closing)) for r in both),
          'quote_timestamp_fields':[f for f in headers if 'stamp' in f.lower() or 'updated' in f.lower()],
          'kickoff_time_present':'Time' in headers})
    out=Path('experiments/results/odds_audit');(out/'inventory.json').write_text(json.dumps(records,indent=2)+'\n')
    with (out/'field_missingness.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(fieldrows[0]),lineterminator="\n");writer.writeheader();writer.writerows(fieldrows)
    for r in records:print(r['season'],{k:v['valid_complete'] if v['present'] else 'absent' for k,v in r['groups'].items()},r['bet365_vs_average_max_normalized_probability_difference'])

if __name__=='__main__':run()
