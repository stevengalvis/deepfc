# Verified alternate-source acquisition

Primary request to https://www.football-data.co.uk/mmz4281/1718/E1.csv failed
with `curl: (56) CONNECT tunnel failed, response 403`. Response headers included
`HTTP/1.1 403 Forbidden`, `server: envoy`, `content-type: text/plain`,
`content-length: 16`. This is an environment egress proxy tunnel rejection before
TLS to the origin, not evidence that Football-Data denied website access.
No proxy disabling, credential changes, access-control bypass or Library retries
were used. Public GitHub Git transport was accessible.

All accessible DeepFC branch histories were inspected; only the small test fixture
CSV is tracked, not season archives. Existing research docs supplied reference
SHA256 hashes for all nine seasons. Two other public mirrors were inspected:
footballcsv/cache.footballdata provides reduced score-only columns and was not
used; xgabora/Club-Football-Match-Data-2000-2025 contains a transformed combined
dataset and was not used once the exact archive was identified.

Chosen mirror: https://github.com/liammcdade/Footballdata
Pinned commit: 84eb7985dc4b842a62f2169eb6a5c2986834932f
Paths: data/ENGLAND/championship/games/2017-2018.csv through 2025-2026.csv.
The mirror README labels this directory EFL Championship; its Football-Data
column layout and E1 codes match the archive format. Stronger provenance evidence:
for ALL NINE files, converting LF line endings to CRLF produces exactly the
SHA256 recorded in DeepFC's prior Championship signal-strength research. There
are no other byte differences after that deterministic conversion. Raw mirror and
restored hashes, pinned URLs, coverage, and retrieval UTC are all saved in
verified_data_manifest.json. data_manifest.json preserves initial failed attempts.

Each season has 552 E1 rows and required HS/AS/HST/AST/HC/AC columns. Total 4968
rows, 4967 completed corner rows. Only Bolton–Brentford 2019-04-27 has blank
corners. Valid shot history contains 4966 fixtures after explicitly excluding
Burnley–Swansea 2024-11-10 (HS=2, HST=7, AS=9, AST=4). Its corner outcome stays
in the baseline/candidate evaluation cohort. No leagues/seasons were substituted.

Reproduce from /workspace/deepfc-shot-reconstruction:

```bash
git clone https://github.com/liammcdade/Footballdata.git /workspace/shot-data-mirror-liam
git -C /workspace/shot-data-mirror-liam checkout 84eb7985dc4b842a62f2169eb6a5c2986834932f
PYTHONPATH=src:. /workspace/.venvs/deepfc/bin/python -m experiments.recover_shot_data_mirror /workspace/shot-data-mirror-liam
PYTHONPATH=src:. /workspace/.venvs/deepfc/bin/python -m experiments.shot_reconstruction data/E1_*.csv > experiments/results/shot_reconstruction/results.json
PYTHONPATH=src:. /workspace/.venvs/deepfc/bin/python -m pytest
```

The frozen experiment source and specification hashes are unchanged from the
previous blocked attempt. The new recovery utility only restores source data.
