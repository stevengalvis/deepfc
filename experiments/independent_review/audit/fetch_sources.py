import json,hashlib,urllib.request,concurrent.futures
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Retrieve exact pinned mirror bytes for independent audit')
parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[3])
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args()
root=args.repo
files=[]
for league,manifest in [('E1','shot_reconstruction/verified_data_manifest.json'),('E0','e0_feasibility/inventory.json')]:
 for f in json.loads((root/'experiments/results'/manifest).read_text())['files']:
  files.append((league,f))
def get(item):
 league,f=item
 url=f['mirror_url'].replace('github.com/','raw.githubusercontent.com/').replace('/blob/','/')
 raw=urllib.request.urlopen(url,timeout=40).read()
 if league=='E1':raw=raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
 h=hashlib.sha256(raw).hexdigest()
 assert h==f['sha256'],(league,f['path'],h)
 name=Path(f['path']).name
 path=args.output_dir/league/name
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 return {'league':league,'path':str(path),'sha256':h}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
 result=list(ex.map(get,files))
(args.output_dir/'source_manifest.json').write_text(json.dumps(result,indent=2))
print('Verified exact manifest hashes:',len(result),'files')
