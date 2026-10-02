# Prospective team-corner probability evaluation

Draft v1, 2026-10-02. **Objective approved; numerical acceptance margins and operational registration remain proposed.** Writing this protocol does not select or authorize a candidate, start collection, or revise historical outcomes.

Verified checkout: `research/shot-pressure-reconstruction`, commit `3782ad73306f66c87a99cbf2c6ee66879b824cc2`. Scope matches `TEAM_CORNER_LINES`. Basis: [acceptance-criteria audit](../results/acceptance_criteria_audit/AUDIT.md). That audit's open objective question is now resolved: prioritize accurate probabilities at specified team-corner lines; count accuracy is secondary.

## 1. Target and comparison

- EFL Championship completed fixtures, each team's full-match corners, using the existing outcome convention. Events: **over 3.5, 4.5, 5.5 and 6.5**, meaning respectively at least4,5,6,7 corners. No additional leagues, lines or outcome subsets selected after results.
- Four lines receive equal weight; home and away receive equal weight; each complete eligible fixture receives equal weight. This estimates average accuracy for that declared population, not prices, stakes or selected betting opportunities.
- Primary research comparator: fixed180 implementation at the verified commit, with its existing eligibility, dispersion and strictly earlier-date history updates. Freeze a manifest of implementation and configuration hashes at registration. Retained main may be reported as secondary context; beating fixed180 does not establish superiority to a different operational incumbent.
- Register exactly one candidate, coefficients or full earlier-only refitting procedure, input schema and forecast horizon before confirmation. Candidate choice is not made by this document. Require finite coherent probabilities: 1>=p3.5>=p4.5>=p5.5>=p6.5>=0. Freeze failure handling; no silent fallback or revised candidate during evaluation.

## 2. Primary endpoint and worthwhile effect

For fixture f, team side v and line l, let z=1(corners>l). Define

`B_f(model) = (1/8) * sum_v sum_l (p_f,v,l(model) - z_f,v,l)^2`.

The primary endpoint is `Delta = mean_f[B_f(candidate)-B_f(fixed180)]`; negative favors the candidate. Pair both models, both team sides and all lines within the same fixture. Eight event scores are not eight independent observations. Report fixture count, team count, dates, blocks and coverage alongside the estimate.

**Recommended research planning value: delta=0.001 absolute Brier improvement**, pending explicit agreement. This maintains continuity with prior research and is about0.48% of historical fixed180 Brier0.209; it is not a demonstrated business-value threshold or a universal probability-error reduction. Alternatives to consider before registration are0.0005 (smaller gain deemed worthwhile, harder to distinguish from noise) or0.002 (larger required gain, stricter performance target). Do not choose among these after candidate results. A change in delta also changes the relevant power alternative; the target alone does not determine study size.

Evidence of meaningful improvement requires the **one-sided97.5% upper confidence bound U(Delta)<−delta**. Merely observing a point gain of delta with an interval excluding zero is insufficient. Report the full two-sided95% interval as well.

## 3. Secondary checks and calibration

Count negative log loss (NLL) is a secondary distributional harm guard. Report count RMSE, mean residual and MAE as diagnostics; MAE of a predictive mean is not a calibration test and is not a required improvement gate. If a candidate supplies only four event probabilities, a full-distribution NLL guard is undefined: resolve its predictive-distribution specification before registration rather than dropping that guard after results.

Proposed mandatory safety family:

| Quantity | Proposed future requirement | Margin status |
|---|---|---|
| Overall count-NLL difference | Upper simultaneous bound below m_NLL | +0.005 is a continuity option, not an approved tolerance |
| Four-line Brier difference in each venue, each fixed180 extreme band, and each scheduled source-season slice | Upper simultaneous bound below m_Brier | +0.001 is a continuity option, not an approved tolerance |
| Candidate event calibration error `mean(z-p)` for each of4 lines ×2 venues | Entire simultaneous interval inside [−epsilon_p,+epsilon_p] | epsilon_p=0.02 is an illustrative2-percentage-point research tolerance, not a known acceptable risk |

Approve or replace these numeric options **before** power planning is finalized, with a recorded reason tied to the intended forecast use. They are not inferred from what would admit today's candidates. If no tolerances can be justified, report the associated diagnostics but do not issue an unqualified research-acceptance claim under this protocol.

Extreme bands remain fixed180 expected corners<4 and>=6, with [4,6) also reported. Use the same membership for paired comparisons. Do not require every seasonal point difference to be negative or halve a baseline bias near zero. Count bias by band remains visible, but has no automatic veto under this probability-first objective.

Also report reliability by fixed probability bins [0,.2),[.2,.4),[.4,.6),[.6,.8),[.8,1], separately by line and model, and <=1/>=10 corner tail calibration when full distributions exist. These are exploratory diagnostics, not additional selectable gates. Candidate-specific reliability bins describe its calibration; they are not paired common cohorts across models. Do not merge sparse bins after viewing outcomes. Mean calibration checks cannot rule out all within-cell errors.

## 4. Dependence, uncertainty and multiplicity

Use paired calendar blocks, retaining all fixtures and their entire forecast vectors within a block. Proposed primary resampling: nonoverlapping date-ordinal//28-day blocks, sampled with replacement; recompute observation-weighted means, not an equal-weight average of unequal-sized block means. Use shared resamples across endpoints and subgroup checks. For seasonal bounds, resample that season's available blocks. A resample with no observations in a mandatory cell is undefined, not zero; frequent undefined draws make that cell's inference inadequate.

Use seed7 and at least10,000 draws; finalize a larger count if needed for simultaneous-tail quantile precision before registration. Predeclare14/56-day block sensitivities. If the acceptance classification is not robust to these plausible lengths, label the evidence inconclusive, not whichever result looks favorable. Development-only dependence checks must support the selected scheme; calendar blocking cannot guarantee protection against long-lived team dependence or regime changes. Failure of the assumptions requires redesign before collection or an inconclusive final result.

Primary inference uses one comparison and endpoint. For a collectively interpretable safety statement, use a conservative Bonferroni family of K=13+S quantities (NLL1; venue2; extreme band2; scheduled season S; calibration8), with family error0.05: one-sided bounds at1−0.05/K for harm differences and two-sided intervals with tails0.05/(2K) for calibration. Freeze S, grouping and K at registration. This is a transparent choice for simultaneous safety claims, not an assertion that every all-must-pass testing procedure inherently needs Bonferroni. No uncorrected search over candidates, periods, lines or cutoffs.

## 5. Size, horizon and new evidence

Before registration, use existing historical data **only as development evidence** to estimate paired variance, dependence, event rates, subgroup coverage and missingness. Simulate power and interval precision across conservative scenarios. Do not use historical selection-biased gains as the sole assumed future effect.

Proposed planning target:90% primary power at a separately specified plausible true improvement D>delta, with adequate simultaneous precision for every mandatory cell. As a rough independent-equivalent guide, required precision depends on `(z_.975+z_.90)*sigma/(D-delta)`; actual fixture/block counts must come from the dependence-aware plan. At D=delta, high probability of certifying improvement beyond delta is not achievable merely by declaring a sample floor. Rare outcomes and seasonal cells can determine study length. A count of100 observations or20 blocks alone is not a power justification. No power analysis is executed in this writing task.

Register exact future start/end dates, planned season coverage and minimum usable coverage after that plan. Start strictly after registration and operational input verification; a date after the historical CSV cutoff alone is insufficient. All previously observed2023/24–2025/26 outcomes remain exploratory. Existing outcome knowledge must not influence confirmation forecasts. A genuine cohort consists of forecasts archived before outcomes, made with inputs available at the declared horizon.

For an odds candidate, proposed horizon is kickoff−60 minutes with ±5-minute tolerance, pending source feasibility and approval. Verify source/bookmaker aggregation parity with development data; store kickoff, source quote and capture timestamps and original payloads. A historical “pre-closing” column is not evidence of availability at that horizon. Freeze odds validation and exclusions. Require the whole valid fixture pair for primary scoring; report all otherwise-eligible fixtures, missing inputs, forecast failures and exclusions by time/venue. Qualification is restricted to this coverage population. Missingness or operational failures cannot be used to hide difficult fixtures; material provenance violations invalidate the evaluation.

## 6. Fixed analysis and decision

No intermediate performance review for model selection, optional stopping, coefficient changes or endpoint changes. Input-integrity monitoring is allowed under a locked procedure. One final analysis at the registered end date. Insufficient coverage or precision yields inconclusive evidence, not an outcome-dependent extension. Any later study needs a new registration and new outcomes.

- **Accept for research qualification:** U(Delta)<−delta, every simultaneous safety requirement passes, coverage/precision and inference are adequate, and the conclusion survives the prespecified dependence sensitivities.
- **Reject for the specified qualification target:** the primary lower bound is above−delta, ruling out the required gain at that confidence level; or a simultaneous harm lower bound exceeds its margin; or a calibration interval lies wholly beyond the approved tolerance. Rejection for insufficient worthwhile gain is not a claim that the candidate is worse on every metric.
- **Inconclusive:** all remaining statistically valid cases, including intervals crossing decision boundaries, sparse required cells, or dependence-sensitivity disagreement. No promotion, no equivalence claim and no automatic claim of harm. Invalid provenance/chronology instead invalidates the study.

Qualification is evidence about these probabilities on this cohort, not deployment approval. Deployment additionally requires operational suitability; betting profitability would require a separately defined decision policy and executable team-corner prices. No staking or risk preference is assumed.

## Registration decisions and next action

The objective is settled. Next, agree **delta and the safety-margin package**, then commission development-only power/feasibility planning to set the confirmation window. The recommended starting discussion is delta0.001, with the explicitly provisional m_Brier0.001, m_NLL0.005 and epsilon_p0.02. Choosing those numbers means accepting those research tradeoffs; it is not implied by approval of the probability-first objective.

Candidate identity, operational comparator if different from fixed180, horizon/source feasibility and exact dates must also be frozen before execution. None is silently selected here. All original frozen outcomes remain unchanged; this document neither re-scores nor promotes an old experiment.
