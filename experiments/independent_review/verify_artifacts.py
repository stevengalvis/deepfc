"""Verify published derived artifacts without fitting a historical candidate."""
from pathlib import Path
import csv,hashlib,json,os,shutil,subprocess,sys,tempfile
import numpy as np

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compare(a,b):
    if isinstance(a,dict):
        assert a.keys()==b.keys()
        for k in a:compare(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):compare(x,y)
    elif isinstance(a,(float,int)) and not isinstance(a,bool):
        assert np.isclose(a,b,rtol=1e-10,atol=1e-12),(a,b)
    else:assert a==b,(a,b)

def main():
    rel=HERE/'reliability';home=HERE/'home_slope'
    manifest=json.loads((rel/'manifest.json').read_text())
    for name,digest in manifest['inputs'].items():assert sha(rel/name)==digest
    original=json.loads((home/'pre_fit_manifest.json').read_text())
    assert sha(home/'home_slope.py')==original['code_sha256']
    assert sha(home/'APPROVED_PLAN.md')==original['plan_sha256']
    assert sha(REPO/'experiments/results/joint_market_calibration/results.json')==original['final_joint_coefficients_sha256']
    stopped=json.loads((home/'earlier_results.json').read_text())
    assert stopped['status']=='stop_nonpositive_delta' and stopped['later_scoring_executed'] is False
    assert -.5<stopped['scalar_fit']['delta']<=0 and not stopped['scalar_fit']['boundary']
    assert sha(home/'oof_predictions.csv')==stopped['oof_predictions_sha256']
    rows=list(csv.DictReader((home/'oof_predictions.csv').open()))
    assert len(rows)==3332 and all(r['fold_start']<=r['date']<r['fold_end']<='2023-07-01' for r in rows)
    for f in stopped['folds']:assert f['latest_training_date']<f['cutoff'] and f['training_fixtures']>=200
    for name in ['reproduce.py','fetch_sources.py','check_slices.py']:
        subprocess.run([sys.executable,str(HERE/'audit'/name),'--help'],check=True,capture_output=True,text=True)
    with tempfile.TemporaryDirectory(prefix='deepfc-artifact-smoke-') as tmp:
        tmp=Path(tmp);env=dict(os.environ,OPENBLAS_NUM_THREADS='1',MPLCONFIGDIR=str(tmp/'mpl'))
        slices=tmp/'slice_checks.json'
        subprocess.run([sys.executable,str(HERE/'audit/check_slices.py'),'--repo',str(REPO),'--arrays-dir',str(rel),'--output',str(slices)],check=True,env=env,capture_output=True,text=True)
        compare(json.loads((HERE/'audit/slice_checks.json').read_text()),json.loads(slices.read_text()))
        work=tmp/'reliability';shutil.copytree(rel,work)
        subprocess.run([sys.executable,str(work/'diagnostic.py')],check=True,env=env,capture_output=True,text=True)
        compare(json.loads((rel/'results.json').read_text()),json.loads((work/'results.json').read_text()))
        subprocess.run([sys.executable,str(work/'write_report.py')],check=True,env=env,capture_output=True,text=True)
        assert (work/'REPORT.md').stat().st_size>1000
        for name in ['E1_later','E0_post_training','E0_full_history']:
            assert (work/(name+'_reliability.png')).stat().st_size>1000
    print('Artifact verification passed. Audit slices and reliability metrics reproduced. No historical fit or stopped later evaluation executed.')

if __name__=='__main__':main()
