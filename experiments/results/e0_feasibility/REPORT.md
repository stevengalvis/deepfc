# Premier League feasibility and prior-exposure audit

2026-10-02. **Conditional GO for a separately authorized historical no-refit transfer evaluation.** All nine E0 seasons have usable corner and required market-average odds coverage in an accessible pinned mirror. No recorded E0 evaluation of today's exact frozen original-odds or joint-calibration candidate was found. E0 itself is heavily previously inspected, so this cannot be called an untouched league or pristine holdout. No forecasts, fitted coefficients or candidate/baseline scores were computed in this audit.

## Verified source and coverage

Research checkout verified at1dab72265927e7cacd4a4d51ba6a14443fd85c81. Refreshed advertised Git branches for DeepFC and ModelFC. Source mirror: `liammcdade/Footballdata`, pinned commit `84eb7985dc4b842a62f2169eb6a5c2986834932f`, directory `data/ENGLAND/Premier league/GAMES/`. Used existing local public-mirror files; no blocked primary endpoint retries.

This is the same repository whose E1 files previously matched archived primary hashes after newline normalization. **That does not verify E0 bytes.** This audit records SHA256 of each original mirror file without normalization, exact repository paths, byte counts and intended primary URLs in inventory.json. No independent primary E0 hashes were available; provenance is pinned public mirror, not independently primary-hash-certified. Mirror documentation describes a heterogeneous collection, including future projections elsewhere; provenance here rests on the identified historical E0 file paths and audited contents, not a blanket endorsement of every file in that repository.

| Source season | Fixtures | Complete corner pairs | Valid required odds triplets | Odds schema | Team strings |
|---|---:|---:|---:|---|---:|
| 2017/18 | 380 | 380 | 380 | BbAvH/BbAvD/BbAvA | 20 |
| 2018/19 | 380 | 380 | 380 | BbAvH/BbAvD/BbAvA | 20 |
| 2019/20 | 380 | 380 | 380 | AvgH/AvgD/AvgA | 20 |
| 2020/21 | 380 | 380 | 380 | AvgH/AvgD/AvgA | 20 |
| 2021/22 | 380 | 380 | 380 | AvgH/AvgD/AvgA | 20 |
| 2022/23 | 380 | 380 | 380 | AvgH/AvgD/AvgA | 20 |
| 2023/24 | 380 | 380 | 380 | AvgH/AvgD/AvgA | 20 |
| 2024/25 | 380 | 380 | 380 | AvgH/AvgD/AvgA | 20 |
| 2025/26 | 380 | 380 | 380 | AvgH/AvgD/AvgA | 20 |

Total3,420 fixtures. The intended scoring seasons2023/24–2025/26 contain1,140 fixtures before unchanged earlier-history eligibility gates; no forecast eligibility/scoring calculation was run. Each season has380 unique ordered home/away pairs, each exactly once, and38 appearances for every team string. No duplicate fixture keys within/across files, bad dates, non-E0 division rows, blank/same-team identities or missing required columns. No blank, negative, non-integer or nonfinite corner/shot values. All expected odds triplets finite and>1. These checks establish structural completeness, not independent correctness of every recorded number.

Source-season identity must be retained:2019/20 ends2020-07-26, so naive July-to-June bucketing would mislabel late pandemic fixtures. Match dates range2017-08-11 through2026-05-24. Exact per-file ranges are in inventory.json.

One internal shot inconsistency: Newcastle–West Ham,2021-08-15, away shots AS=8 versus shots on target AST=9. It is flagged, not silently repaired. Corners and odds are present. Both proposed candidates use corners and odds only, so retain this fixture for them; any separately authorized shot feature must quarantine invalid shot inputs under a frozen policy. No shot feature is introduced here.

Team identifiers are stable-looking across the nine files:32 distinct strings, no normalized punctuation/case collisions, no within-season split identities or appearance-count anomalies. All names were inventoried, including `Nott'm Forest`, `Man City`, `Man United`, `Wolves`. No alias mapping was applied. This is a consistency check within one source; provider-to-provider identity equivalence remains a separate task.

## Market and timing assumptions

BbAvH/D/A are historical Betbrain average fields; AvgH/D/A are market-average fields. Inventory the former for2017/18–2018/19 but **do not splice them into the frozen candidate**: those years supply corner warmup only. Use AvgH/D/A from2019/20 onward under the original odds design, and exclusively those fields for scoring2023/24–2025/26. No Bet365, maximum-odds or closing substitution. The field meanings follow [Football-Data notes](https://football-data.co.uk/notes.txt); pre-closing and closing are different fields.

Files have no recognized per-quote timestamp field; kickoff Time appears from2019/20 onward and is not odds availability time. Historic snapshot timing/source composition may differ across leagues/years. This supports historical covariate evaluation, not a verified kickoff-minus60-minute information set, executable prices or profitable betting. A genuinely prospective study still needs timestamped capture.

## Prior use: league exposure is not exact-model exposure

ModelFC main `958d651e4d04993c4036b5bbde562b6416e29a4a` documents:
- EPL1X2 baseline/Poisson/Dixon-Coles experiments on2022/23 and2023/24;
- EPL corner baselines among five-league comparisons;
- probability diagnostics using2022/23–2026/27 files, scoring from2025-07-01;
- shot-informed corner-weight selection and recency investigations, including EPL.

These are recorded development/evaluation exposure, not mere loader support. See [pinned ModelFC EXPERIMENTS.md](https://github.com/stevengalvis/modelfc/blob/958d651e4d04993c4036b5bbde562b6416e29a4a/EXPERIMENTS.md). We inspected existing experiment records to establish exposure, not to select E0 based on transfer performance. User selected E0.

Scanned reachable text histories across refreshed refs for today's exact module names and distinctive original/joint coefficients. ModelFC has no matches for `experiments.market_strength`, `joint_market_calibration`,0.113765840...,0.421563892... or0.311629648.... DeepFC matches correspond to saved Championship experiments and subsequent proposed transfer documentation, not recorded E0 outputs. Original implementations restrict E1 in ingestion/feature paths; their saved manifests contain E1 files. Thus **no accessible record of exact frozen-model E0 evaluation** was found.

This negative search is bounded: renamed/equivalent implementations, uncommitted runs, chats, deleted/unreachable refs and external runtime stores may be absent. It is not proof of non-exposure. Ref inventories and pattern matches are saved in history_scan.json and *_refs.txt. Prior generic EPL work does not automatically disqualify a new frozen transfer comparison, but its architecture and diagnostics may have benefited from that knowledge. Label it “previously inspected league; exact frozen-model transfer not recorded,” not independent confirmation.

Steve separately confirmed no prior D2 tests; that statement is specific to D2 and does not erase documented EPL exposure. This audit changes focus to E0 without changing the saved D2 findings.

## Frozen proposed no-refit transfer specification — not executed

Target E0 only. Pin the nine inventory hashes before execution; no replacement source/season after seeing results. Use source seasons2017/18–2022/23 as initial historical inputs; score source seasons2023/24,2024/25,2025/26, combined primary. No league/model choice based on score, no retrospective window selection.

Primary candidate: today's joint baseline/odds calibration; fixed exact coefficients from saved Championship results:
`a_home=-0.00870047867223288, a_away=-0.01899680404719811, gamma=0.3116296486016443, beta=0.4215638920715592`.

`log(mu_new)=log(5)+a_venue+gamma*log(mu_fixed180_E0/5)+beta*s`.

Comparator fixed180_E0 uses E0-only strictly earlier-date corner histories, original180-day decay, smoothing, eligibility and earlier-history dispersion. Same-date outcomes cannot enter forecasts. Updating prescribed historical sufficient statistics is allowed; correction-coefficient re-estimation, cross-league pooling, dispersion recalibration and hyperparameter tuning are prohibited. Championship training cutoff remains before2023-07-01. No E0 outcomes fit those frozen correction coefficients.

Original frozen odds adjustment `mu_fixed180_E0*exp(0.11376584000060998*s)` is a secondary comparator, not a selectable fallback winner. s is normalized inverse AvgH/AvgD/AvgA probability(home win) minus probability(away win), with opposite sign for the away observation. Preserve NB dispersion. Reject invalid/missing odds triplets identically for all three models; no imputation. Same complete fixture/venue/outcome cohort. Shots anomaly above does not exclude a valid corner/odds fixture.

A later authorized implementation must support E0 explicitly where E1 guards currently exist and test league isolation; never relabel E0 rows as E1. This audit does not modify forecasting code. Preserve original provider team strings absent a documented required identity correction before scoring.

Primary metric is fixture-paired equal-weight mean Brier for both team sides and four lines3.5,4.5,5.5,6.5. Report original/joint versus fixed180, plus joint versus original as secondary. Prespecify count NLL/MAE and calibration/bias by season, venue and fixed180-defined bands<4,[4,6),>=6; <=1/>=10 tail diagnostics. Calendar paired28-day blocks,10,000 resamples seed7,14/56-day sensitivity; no independent-line sample claims. All periods and failures shown, no score-driven retuning.

The probability protocol's0.001 worthwhile margin and safety tolerances remain proposals, not newly approved acceptance gates. Do not silently retrofit them onto this transfer or reinterpret original rejections. Set the transfer's research-only interpretation contract before execution. Historical transfer can answer whether these fixed Championship coefficients generalize to E0 under its local histories; it cannot establish future Championship accuracy, a pristine holdout, deployment readiness or betting value. Domain shifts include team strength distribution, scheduling, corner process, quote aggregation and recording conventions.

## Recommendation and deliverables

Data are **usable for the proposed corners-plus-average-odds historical computation, conditional on accepting pinned-mirror provenance and separately authorizing execution/interpretation**. Unlike D2, required average odds are available. No primary hash certification or quote timestamp guarantee is claimed. Prefer an independent primary checksum comparison when legitimate access returns; do not repeatedly retry blocked endpoints.

Reproduce this data-only audit with `/workspace/.venvs/deepfc/bin/python -m experiments.audit_e0_coverage` from the research checkout. It reads the pinned local mirror and writes inventory.json/run output; no model imports. Review history_scan.json for exposure-search bounds. All files saved locally without commit/push/PR. Original frozen model records and pass/fail decisions remain unchanged.
