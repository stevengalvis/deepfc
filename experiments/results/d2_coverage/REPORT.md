# D2 data completeness recovery — partial success, required odds still blocked

2026-10-02. Data-quality audit only: no candidate/baseline predictions, losses or performance scores calculated. No further request was made to the rate-limited Football-Data endpoint; no rate-limit bypass, proxy change or credential workaround attempted. The prior fetcher returned HTTP429 without exposing Retry-After guidance. Used legitimate public repositories already available locally plus one small repository inspection.

## Sources inspected

- liammcdade/Footballdata at84eb7985dc4b842a62f2169eb6a5c2986834932f: same mirror that supplied hash-verified E1 data. Repository tree has English division files and top-five aggregates, but no D2 match dataset. It cannot establish D2 completeness.
- footballcsv/cache.footballdata atf43a2aa0c65fb061c87e9541e7a567dd58ff933a: de.2.csv files through2023/24. Inspected2023/24 header is `Date,Team 1,FT,HT,Team 2`; required corners/shots/market-average columns absent. No2024/25–2025/26 files in that pinned tree. Unsuitable.
- renators99/football-data ata4f04eb09f0b65e2a83256a2b34e9b964be9f69b: downloader/pipeline code, no committed required match CSV dataset. No downloader executed.
- xgabora/Club-Football-Match-Data-2000-2025 at25882a58a736daf7ece3781940eac17ae1117a66: merged, transformed Football-Data-derived Matches.csv with D2 corners and shots. Successfully audited below. It is not a byte-identical primary-source mirror and cannot substitute for the required market-average odds.

[Exact inspected merged file](https://github.com/xgabora/Club-Football-Match-Data-2000-2025/blob/25882a58a736daf7ece3781940eac17ae1117a66/data/Matches.csv), [pinned field documentation](https://github.com/xgabora/Club-Football-Match-Data-2000-2025/blob/25882a58a736daf7ece3781940eac17ae1117a66/README.md).

Entire original local file SHA256: `ef224cf2c252f07a842b3bcfd4ba5c718c25cedd8937ffa174a74b86b5ba4221`. Exact hash, byte count, schema, dates, per-column quality counts and team identities are saved in inventory.json. No source data copied into DeepFC. This hash pins the transformed mirror bytes only; there is no independently verified Football-Data D2 hash.

## Row-level findings

| July–June window | Rows | Distinct team strings | Invalid/blank corner or shot cells | Duplicate fixture keys | HST>HS or AST>AS rows |
|---|---:|---:|---:|---:|---:|
| 2017/18 | 306 | 18 | 0 | 0 | 0 |
| 2018/19 | 306 | 18 | 0 | 0 | 0 |
| 2019/20 | 306 | 18 | 0 | 0 | 0 |
| 2020/21 | 306 | 18 | 0 | 0 | 0 |
| 2021/22 | 306 | 18 | 0 | 0 | 0 |
| 2022/23 | 306 | 18 | 0 | 0 | 0 |
| 2023/24 | 306 | 18 | 0 | 0 | 0 |
| 2024/25 | 306 | 19 | 0 | 0 | 0 |
| 2025/26 | 306 | 18 | 0 | 0 | 0 |

Total2,754 rows; proposed scored windows2023/24–2025/26 contain918 rows before any model-eligibility filtering (no such filtering or forecasting was run). Dates parsed, all selected Divisions D2; no blank or same-home/away team entries. Required statistical fields map to HomeCorners/AwayCorners, HomeShots/AwayShots, HomeTarget/AwayTarget; all values finite nonnegative integers. Counts match the expected18-team double round-robin size but are not independent verification of every fixture/result. Windows are derived from dates because the merged file lacks a source-season column.

**Identity defect:**2024/25 contains `Preussen Munster`17 appearances and `Preußen Münster`17 appearances; all other team strings have34. This strongly suggests a split identity, but no normalization or join was applied. Require a documented verified alias map before league-history construction; naive name-based history would split the team. “Complete numeric cells” therefore does not mean model-ready data.

**Critical schema gap:** AvgH,AvgD,AvgA are absent for every season. The README explicitly identifies OddHome/OddDraw/OddAway as **Bet365** prices. These are not missing values that can be filled: they are the wrong odds feature for the frozen design. MaxHome/MaxDraw/MaxAway also cannot replace averages. No odds substitutions, fair-probability calculation or forecast scores were made. Quote-level timestamp provenance remains unresolved as well.

## Conclusion and next step

Statistical coverage is substantially corroborated through a legitimate transformed mirror, with one team-name defect identified. **The specified D2 transfer dataset remains unavailable:** need original-schema D2 files with pre-closing AvgH/D/A for the scored seasons, and trusted history/identity provenance. The successfully inspected mirror does not close that requirement.

Reasonable recovery stopped after inspecting the known E1 mirror, two existing alternative datasets and one public pipeline repository. Do not run the transfer experiment or call the dataset fully validated. Next authorized step can be a provider download after rate-limit clearance or another verifiable original-schema source. Parent is separately checking undocumented D2 evaluation; this report makes no new untouched-data claim.

Reproduce the quality-only inventory with `/workspace/.venvs/deepfc/bin/python -m experiments.audit_d2_mirror` from the research checkout, using the pinned mirror at the script's documented local path. No model modules imported. Findings and script saved locally, uncommitted; no further GitHub push.

## Authorized single primary retry, 16:23:40 UTC

Checked saved records: the earlier web fetcher exposed no Retry-After header. Parent confirmed over ten minutes since the original429. Made exactly one request to https://football-data.co.uk/mmz4281/2526/D2.csv with retries disabled and unchanged network configuration. The execution environment's CONNECT proxy returned HTTP403 Forbidden (server:envoy), before a provider HTTP response was available; curl exited56 with origin status000. No Retry-After header was returned, and no CSV was obtained. This does not establish whether the provider's original rate limit expired. Stopped immediately: no second route, parallel retry, remaining-season requests or scoring. Exact receipt is in primary_retry.json. Primary acquisition remains blocked by the execution network; the market-average odds and identity/provenance gaps remain unresolved.
