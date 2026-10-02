"""Download the nine public E1 archives and retain an auditable manifest."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen


def main():
    Path('data').mkdir(exist_ok=True)
    output = Path('experiments/results/shot_reconstruction/data_manifest.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    archived = dict(re.findall(r'\| (E1_\d+.csv) \| `([a-f0-9]{64})`',
                    Path('experiments/results/championship_signal_strength.md').read_text()))
    records = []
    for year in range(17, 26):
        season = f'{year:02d}{year+1:02d}'
        name = f'E1_{season}.csv'
        url = f'https://www.football-data.co.uk/mmz4281/{season}/E1.csv'
        record = dict(path=f'data/{name}', url=url,
                      attempted_at=datetime.now(timezone.utc).isoformat(),
                      archived_sha256=archived.get(name))
        try:
            payload = urlopen(url, timeout=30).read()
            if b'HomeTeam' not in payload[:500]:
                raise ValueError('response is not the expected CSV')
            Path(record['path']).write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            record.update(status='downloaded', size=len(payload), sha256=digest,
                          matches_archived_hash=digest == archived.get(name))
        except Exception as error:
            record.update(status='blocked', error=str(error))
        records.append(record)
        output.write_text(json.dumps(records, indent=2)+'\n')
    print(json.dumps(records, indent=2))
    if any(r['status'] != 'downloaded' for r in records):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
