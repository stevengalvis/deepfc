# Acceptance-criteria audit — prospective recommendations only

2026-10-02. Verified accessible, clean research checkout `/workspace/deepfc-shot-reconstruction`, branch `research/shot-pressure-reconstruction`, commit `3782ad73306f66c87a99cbf2c6ee66879b824cc2`. Reviewed frozen joint-strength, odds-strength and joint-calibration specifications, the implemented `joint_strength.gates`, saved results, diagnostic and bootstrap helpers. No model execution, revised scoring, historical reclassification or publication.

**Recommendation:** keep all historical decisions; replace the next experiment's point-estimate vetoes with a prespecified proper-score improvement target and uncertainty-aware, practically justified safety margins. First establish what the forecasts are for. The current rules are legitimate frozen research requirements, but are not a scientifically universal definition of a useful probabilistic forecast.

## What remains unchanged

| Saved experiment | Original combined-later outcome |
|---|---|
| Joint attack/defence | Reject; all eight gates fail |
| Original odds strength | Reject; both extreme-bias gates fail |
| Joint baseline/odds calibration | Reject; both extreme-bias gates and every-season gate fail |

These are contractual outcomes, not proofs that every rejected candidate is inferior on every forecast objective. The shot reconstruction and all other saved artifacts are also left untouched. This audit does not apply its proposed standard to any old result.

## Findings: defects versus choices

| Criterion | Assessment |
|---|---|
| Same observations, chronological fitting, frozen specification | Sound. Preserve these requirements. Identical evaluation cohorts do not establish that missing-price cases are representative; coverage must also be reported. |
| Brier at four fixed thresholds | Proper for those event probabilities. Not sufficient to identify quality of an unrestricted full count distribution: many distributions share those four probabilities. Equal threshold weights are a use-dependent choice, not an error. |
| Brier delta <=−0.001 plus upper95 <0 | Shows a practically sized point estimate and evidence of some improvement, **not evidence that improvement exceeds0.001**. That distinction matters when calling the result “material.” The0.001 value is a policy choice without a documented utility rationale. |
| Improvement in every season | A conservative consistency preference, not a calibrated test of harmful seasonal instability. A tiny noisy positive delta vetoes a candidate; tiny noisy negative deltas pass. It ignores effect size and uncertainty. Use seasonal material non-inferiority if stability is required. |
| Halve extreme-band absolute mean bias | Baseline-relative and unstable near zero. A baseline bias estimate of0 would require exact candidate zero; a very biased baseline permits substantial residual bias. Cancellation within bands can satisfy it despite conditional errors. This is a poor universal calibration acceptance criterion, though it was an enforceable frozen target. |
| NLL point delta<=0 and upper95<=+0.005 | Combines an unnecessary sign restriction with an otherwise recognizable non-inferiority bound. It can reject tiny acceptable deterioration even when its upper bound is within the margin. The0.005 margin needs a use-based rationale. |
| Venue Brier deterioration<=+0.001 | A point-estimate guard, not evidence of non-inferiority. It can miss uncertain material harm or reject harmless noise. The size0.001 is a choice, not a demonstrated defect by itself. |
| Pointwise intervals, sample floors | Helpful description; not enough for simultaneous slice claims or precision guarantees. “100 observations”/“20 blocks” are rough eligibility floors, not a power analysis. |

Concrete evidence: the original low-band baseline bias is +0.018769 with95% interval [−0.210602,+0.277055], producing an absolute-bias target of only0.009384 corners. Its369 observations include just11 home cases. Joint calibration's 2023/24 Brier delta is +0.000371 [−0.002640,+0.003406]; the seasonal gate treats this as failure despite uncertainty about even its direction. Conversely, the high-band concern is substantive: original odds bias −0.480 [−0.645,−0.308], and joint calibration +0.351 [+0.194,+0.514]. Revising future criteria would not make those observed problems disappear. Sources: saved market diagnostic and joint-calibration reports/results.

## Match the measure to the forecast

Brier is appropriate for prespecified binary events; log loss evaluates the whole predicted count mass and strongly penalizes assigning very low probability to observed outcomes. A count ranked probability score, summing squared CDF errors over nonnegative integer thresholds, is another full-distribution option. Choose the primary score before outcomes, rather than switching to whichever favors a candidate. A proper score can improve through useful discrimination while aggregate calibration deteriorates. These distinctions follow proper-scoring-rule theory; the four-threshold limitation is its application to this repository. [Gneiting & Raftery](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf)

Mean residual zero is only a moment condition, not full distributional calibration. Tail-event reliability, probability reliability across fixed bins, and discrete-distribution calibration diagnostics address different errors. Global calibration can hide conditional errors; no finite collection of subgroup checks proves calibration everywhere. Sharpness is desirable subject to calibration, not instead of it. [Gneiting, Balabdaoui & Raftery](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jrssb.pdf)

The code reports MAE of the predicted **mean**. That is a descriptive error, but absolute loss targets a median; squared error targets a mean. Do not make MAE-of-mean a necessary condition for an accurate predictive distribution. If median point forecasts are the product, evaluate its predicted median explicitly in a future protocol. [Gneiting](https://arxiv.org/abs/0912.0902)

The fixed180-defined bands correctly preserve common membership and avoid moving observations between models. They diagnose errors conditional on the comparator's forecast, not calibration conditional on the candidate's own forecast. Preserve them for comparable slices; add separately frozen candidate-probability bins for reliability, without comparing different memberships as though paired. Boundaries4/6 are inherited choices, not natural scientific constants.

Forecast accuracy and betting decisions are separate estimands. Better Brier/NLL does not establish value at available prices. A betting assessment would additionally need the user's decision/staking policy, executable timestamped prices, transaction constraints and an appropriate utility/risk endpoint. The available 1X2 covariates are not team-corner execution prices. No profitability or risk preference is assumed here.

## Uncertainty and repeated use of data

Pairing both fixture sides within calendar blocks is preferable to treating3,198 team observations as independent. However33 combined28-day blocks cannot reliably represent arbitrary long-term team dependence or regime shifts. Block length needs justification and predeclared sensitivity checks; more bootstrap draws reduce simulation noise, not dependence or selection bias. Time-series bootstrap validity requires dependence assumptions, not merely choosing a block size. [Lunde & Shalizi](https://arxiv.org/html/1711.02834v2)

All later seasons have informed multiple design choices. Earlier-only coefficient fitting prevents direct training leakage, but does not restore a clean test after adaptive architecture selection. A prospective freeze or truly untouched outer evaluation is needed; a new specification on the same inspected outcomes is still exploratory. [Cawley & Talbot](https://www.jmlr.org/papers/v11/cawley10a.html)

Multiplicity needs nuance: requiring **all** correctly specified tests to pass is an intersection-union procedure and does not automatically require Bonferroni just because there are several gates. Choosing among candidates, periods or successful slices does create selection risk. Independent pointwise intervals also do not jointly cover every displayed subgroup. Use a single primary comparison and a small fixed safety family, with simultaneous intervals when making collective safety claims. Do not label every noisy slice deterioration a discovered defect.

## Proposed next-experiment standard — not yet an executable acceptance contract

1. **Define the use and target population.** Working research default: probabilities for team-corner over3.5/4.5/5.5/6.5, equal event weights and equal eligible team-observation weights. Under this scope, primary endpoint is mean four-line Brier difference, candidate minus the frozen incumbent. If the intended product is instead the whole count distribution, choose count ranked probability score *before registration* and derive its own effect size; do not retain Brier merely because today's results favor it. Freeze competition, horizon, coverage rules and incumbent version. Fixed180 remains a useful benchmark, but beating it alone cannot establish superiority to a different actual incumbent.

2. **Define meaningful superiority.** For the four-event research default, propose retaining delta=0.001 as a continuity benchmark, explicitly provisional: about0.48% of the observed baseline Brier0.209. It is not a utility or profitability threshold. Obtain agreement that this is worth added complexity, or derive a different delta from intended use before registration. Pass the primary endpoint only when the one-sided97.5% upper confidence bound for the mean difference is below **−delta**. This proves more than the old point-estimate-plus-sign rule, subject to inference assumptions; it will require more data. For binary Brier, expected excess score is squared probability error, but a0.001 score difference is not a universal percentage-point improvement in calibration.

3. **Define safety in absolute units.** Replace seasonal/venue sign vetoes with upper confidence bounds below approved non-inferiority margins m_score. Replace halving baseline bias with candidate bias equivalence: a simultaneous two-sided interval wholly inside [−epsilon_count,+epsilon_count] for each required forecast band. For required event-calibration cells, similarly bound observed-minus-predicted probability within approved epsilon_probability. Use NLL as a full-distribution guard with its own agreed margin. Include at most the predeclared two venues, two extreme baseline bands and scheduled seasonal slices as mandatory groups; other cuts are exploratory. Tail checks <=1 and >=10 are diagnostic unless the user identifies them as decision-critical. Numeric margins are **unresolved user/use decisions**, not values inferred from the candidates' errors. Require valid probabilities and horizon-available inputs regardless of score.

4. **Predeclare inference and size.** One candidate, one incumbent, one primary endpoint, one fixed future window and one final analysis. Record forecasts before outcomes and preserve complete fixture pairs. Proposed inference starts with paired28-day blocks, with14/56-day sensitivity analyses fixed in advance; use10,000 draws and a fixed seed. Use development-only dependence/variance checks and simulations to plan adequate precision/power for delta and the smallest mandatory cell, including rare events and missing quotes. Lock the resampling implementation and safety-family size K before collection; a transparent conservative option is Bonferroni-adjusted safety bounds. If dependence checks or sparse events make the intervals unreliable, classify as inconclusive. Neither arbitrary sample floors nor nonsignificance establish safety. A sensitivity disagreement also makes the conclusion inconclusive rather than allowing a favorable block length to be selected.

5. **Use three outcomes.** Accept for the declared research use only if the material primary bound and every prespecified safety bound pass with sufficient valid coverage. Reject for that use if the primary interval rules out the required gain, or a safety interval demonstrates violation of a material margin. Otherwise **inconclusive**: do not promote, declare equivalence, or claim harm. Invalid chronology/input provenance invalidates the evaluation. No outcome-dependent extension of the window; any new study requires a new registration. Failure to demonstrate success is not automatically evidence of inferiority.

6. **Use genuinely future outcomes.** Register only after the above decisions, power plan and timestamp/source feasibility are resolved. Start on a declared date after registration; choose the fixed end date using development-only precision planning. Archive source-matched pre-match snapshots at the agreed horizon; do not infer availability from historical “pre-closing” labels. Freeze whether coefficients are static or periodically refitted; if refitted, lock the entire earlier-only procedure. No monitoring-driven selection among candidates. All2023/24–2025/26 outcomes remain development/exploratory forever. No live collection or candidate run starts through this audit.

## Decisions needed and next action

Ask Steve first: **Are these forecasts intended primarily as probabilities at specified corner lines, a complete count distribution, point-count estimates, or inputs to a defined betting decision?** Then agree the relevant horizon, incumbent, minimum worthwhile score gain, acceptable subgroup/count/probability error and feasible evidence-collection duration. A research benchmark can be approved without claiming business value, but the distinction must be explicit.

Finish and register that prospective contract before another model experiment. Do not choose tolerances that happen to admit a previously rejected candidate. The audit itself is complete; intended use and acceptable margins block finalizing the future standard, not saving this assessment.

Audit deliverable only. No source edits, new analysis code, tests or candidate execution were needed; existing tracked artifacts were checksum-verified unchanged. No commit, push, PR, deployment or retroactive promotion was performed in this audit.
