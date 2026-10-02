# Cross-league feasibility and exposure audit — no evaluation

2026-10-02. **Recommend Germany's 2. Bundesliga (Football-Data D2) as a conditional transfer candidate. “Genuinely unused” is not established.** No recorded D2 model-development/evaluation exposure was found in the accessible Git histories. Source coverage is advertised, but row-level completeness remains unverified. No cross-league model scores were calculated or selected on.

## Exposure evidence

DeepFC research source:3782ad73306f66c87a99cbf2c6ee66879b824cc2. Fetched every advertised origin branch. Reviewed reachable text blobs for D2/Bundesliga2 references and research history. No D2 reference found before this audit. Existing work concentrates on Championship.

ModelFC main:958d651e4d04993c4036b5bbde562b6416e29a4a; cloned read-only for inspection, with96 remote refs including HEAD. Scanned all reachable distinct Markdown/Python/JSON/YAML/TOML blobs, not only main. See history_inventory.json and pinned ref inventories. D2 occurs only in DATA_REFRESH.md, src/modelfc/corner_capabilities.py and src/modelfc/corner_data.py: league recognition and optional loader support, not documented fitting or evaluation.

ModelFC EXPERIMENTS.md records corner-model evaluations in the five major European leagues and MLS, plus later probability, shot-informed and recency investigations. Those major leagues cannot be called untouched merely because this exact DeepFC candidate was not run there. Its default corner_data.json enables E0,E1,SP1,I1,D1,F1,P1; D2 is not enabled. Technical support for D2 is exposure to its identifier, not proof its match outcomes were evaluated.

Evidence links: [ModelFC experiment history](https://github.com/stevengalvis/modelfc/blob/958d651e4d04993c4036b5bbde562b6416e29a4a/EXPERIMENTS.md), [configured leagues](https://github.com/stevengalvis/modelfc/blob/958d651e4d04993c4036b5bbde562b6416e29a4a/corner_data.json), [optional coverage](https://github.com/stevengalvis/modelfc/blob/958d651e4d04993c4036b5bbde562b6416e29a4a/DATA_REFRESH.md).

Limits: Git does not reveal uncommitted local/VPS experiments, private runtime stores, deleted/unreachable refs, chats or undocumented human inspection. Those were not accessed. Keyword/history scans may miss unnamed league use. No claim of an untouched holdout is justified without the owner's exposure confirmation and any relevant external run inventory. Do not label missing evidence as proven absence.

## Availability-based choice

Football-Data advertises D2 match statistics plus match/goals/handicap odds for every season2017/18–2025/26. Notes define HC/AC corners, HS/AS/HST/AST shots, and AvgH/AvgD/AvgA pre-closing market averages. This supports prioritizing D2 over already-evaluated major leagues without viewing its predictive results. Second-tier context is an additional qualitative reason, not a guarantee of similar distributions. [Germany archive](https://football-data.co.uk/germanym.php), [field definitions](https://football-data.co.uk/notes.txt).

The three representative CSV requests (1718,1920,2526 D2) returned HTTP429 through the web fetcher. No retries to bypass that response; no alternate source was downloaded. Hence actual D2 headers, missingness, duplicate dates, completeness and odds triplet coverage have NOT been verified. The provider's “match stats” description does not prove all requested columns are populated. A metadata/quality-only inventory must precede approval to score; archive URLs alone are not a usable-data certificate. Historical pre-closing labels also do not provide exact quote timestamps.

## Frozen proposed transfer design, pending data/exposure clearance and execution approval

League selection is D2 based on the above availability/history, not performance. Do not evaluate other leagues and keep whichever wins. Proposed scoring seasons2023/24–2025/26; D2 seasons2017/18–2022/23 supply past history. Verify schema/quality and pin file hashes before any model scoring. Do not inspect candidate residuals or metrics during acquisition. All baseline inputs for a fixture must come from strictly earlier D2 dates; never update from other same-date fixtures.

Primary transfer candidate: saved joint baseline/odds calibration, with exact Championship-fitted coefficients from experiments/results/joint_market_calibration/results.json:
- a_home=−0.00870047867223288;
- a_away=−0.01899680404719811;
- gamma=0.3116296486016443;
- beta=0.4215638920715592.

Function remains log(mu_new)=log(5)+a_venue+gamma*log(mu_fixed180_D2/5)+beta*s. **No coefficient fitting, recalibration, penalty changes, thresholds or league-specific hyperparameter tuning.** Fixed180 uses D2-only past corner history, original180-day decay, smoothing/eligibility and earlier-history dispersion rules. Updating these prescribed sufficient statistics is permitted; estimating new correction coefficients is not. Frozen original odds coefficient0.11376584000060998 may be reported as a labelled secondary comparator, not selected retrospectively as the winner.

s uses normalized inverse AvgH/D/A, sign reversed for away. Require finite decimal prices>1; no imputation, BbAv splice, bookmaker substitution or closing fallback. Same complete quote/outcome fixture pair for all comparisons. Report excluded fixtures and overall coverage. Shots are part of source suitability checks only; the joint candidate contains no shot term and no new shots candidate is authorized.

Current DeepFC ingestion/experiment helpers enforce E1 in places. A later authorized implementation must add explicit D2 support and tests while preserving league identity; never disguise D2 as E1 or pool leagues to bypass guards. This audit makes no such code changes.

Primary endpoint: fixture-paired average Brier on equally weighted home/away and lines3.5–6.5 against D2 fixed180. Secondary NLL, MAE, season/venue/fixed180-band bias and <=1/>=10 tail calibration. Bands fixed180<4,[4,6),>=6; paired28-day blocks with14/56 sensitivity, 10,000 draws seed7. Report every registered slice and uncertainty; sparse cells are inconclusive. The prospective probability protocol's numeric margins remain unapproved proposals, so this design authorizes no new pass/fail classification or promotion. Resolve the interpretation contract before any scoring, not after results.

A D2 study tests transport of Championship-fitted coefficients into a different league, not future Championship accuracy. Differences in teams, schedule, corner generation, bookmaker mix and recording can change calibration and dependence. Even a truly uninspected D2 dataset cannot replace genuinely future Championship confirmation. Repeated prior model design on other leagues also limits claims of architectural independence. Preserve all existing failed-gate records whatever transfer results eventually show.

## Recommended next action

First resolve undocumented D2 exposure and obtain a header/quality inventory when access is available. Then separately approve execution of this single frozen transfer design. Until then: **one plausible league, no recorded Git-based evaluation exposure, but no certified unused/complete test set.** No model fitting, cross-league forecast generation or score inspection was performed here.
