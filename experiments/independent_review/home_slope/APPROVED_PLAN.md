# One home slope correction for the frozen joint corner model

Prepared 2 October 2026. Status: design for approval and later execution, not an executed experiment. No new candidate has been fitted, generated or scored. This plan is deliberately limited to one scalar correction and its exact no-change control. Nothing here authorizes publication, live collection or promotion.

## Recommendation and hypothesis

Test whether a modest home-specific expansion of the frozen joint model's predicted mean around five corners improves its four-line probabilities. Leave away forecasts unchanged. This asks whether the shared response to forecast strength is too compressed for home teams, not whether venue was omitted or whether every home probability should increase.

The completed diagnostic motivates the question: home probabilities are low on average at all four lines, while away averages are closer and some low-probability home cells already overpredict. Those observations do not prove a slope error, identify an optimal pivot, or establish that a correction will transfer. A pure intercept shift, distribution-shape error, input drift or transient regime could instead explain the pattern. The proposed correction deliberately cannot fix every such alternative.

Family choice is now fixed from the existing diagnostic and structural constraints. No additional later-period residual analysis, pivot search, family comparison or coefficient evaluation is allowed before execution approval. The design remains adaptively motivated by inspected history; an earlier training cutoff cannot make its later evaluation independent.

## What the existing model already contains

Let b be the fixed180 mean and s the signed normalized inverse AvgH/D/A strength. The frozen joint model is

`log(mu_J / 5) = a_venue + gamma * log(b / 5) + beta * s`.

It already has distinct home and away intercepts, a_home = −0.00870047867223288 and a_away = −0.01899680404719811. Its shared slopes are gamma = 0.3116296486016443 and beta = 0.4215638920715592. Therefore another home indicator would not supply previously absent information. The new degree of freedom is a venue-by-existing-predictor slope interaction; it introduces no new raw feature or data source.

The earlier rejected calibration at commit 10dba725 fitted eight essentially unregularized parameters: a separate logistic intercept and slope per line on fixed180 probabilities. It did not enforce a common count distribution. Its reported deterioration was in Brier and binary log loss; count NLL and means were unchanged. Do not call those binary losses count NLL. Other reviewed failures involved team-prior selection, marginal dispersion changes and attack/concession exponent damping. Their failures caution against assuming generic calibration will work; they do not establish that this distinct one-parameter conditional correction will succeed. Source snapshots and immutable links are bundled in references_manifest.json.

## The only candidate

For each forecast define `h = 1(venue is home)` and `x = h * log(mu_J / 5)`. Use

`mu_C = mu_J * exp(delta * x)`.

Equivalently, home `mu_C = 5 * (mu_J / 5)^(1 + delta)`; away `mu_C = mu_J` exactly. Fix delta to the constrained interval [−0.5, +0.5], with a zero-centered Gaussian regularizer of standard deviation 0.25. These conservative design constants are proposed a priori, not estimated or tuned from diagnostic bins. Five is the existing model's reference scale, not a newly optimized crossover. No additional intercept, per-line coefficient, away parameter, team effect, dispersion fit, clipping, blend or candidate search.

The exact null is delta = 0 and recovers the saved joint model. For positive delta, home means above five rise and those below five fall. At five they are unchanged. Thus the rule is not a blanket home increase. A pivot on expected corners is not the same as a fixed probability boundary for every line; it does not guarantee improvement in the diagnostic's below-20% cells. The earlier sample must contain useful support on both sides of the pivot; otherwise stop rather than extrapolate a one-sided uplift.

In original predictor coordinates, home a_home, gamma and beta are multiplied by the same factor (1 + delta); away coefficients retain their original values. The induced home intercept and slope changes are tied, not independently fitted. This restriction is intentional: it is a small falsifiable shape correction, not a general venue refit. It cannot isolate baseline-slope versus odds-slope causes, or distinguish them causally from intercept drift.

Keep each forecast's baseline alpha unchanged. Construct the complete NB distribution with shape r = 1/alpha and success probability r/(r + mu_C), using the existing Poisson limit for alpha <= 1e−12. Derive all probabilities from it: P(Y >= 4), P(Y >= 5), P(Y >= 6), P(Y >= 7). This guarantees decreasing coherent exceedances and valid count NLL. Keeping alpha fixed does not keep variance fixed: variance becomes mu_C + alpha * mu_C^2.

Home mean ranking is preserved because 1 + delta > 0. At the same alpha, probability ranking is also preserved. Across dates with different alpha, probability rankings and AUC need not be identical; measure them rather than asserting preservation. Correct absolute probability levels and discrimination are different targets.

## Earlier E1 training only

Use the same nine hash-verified E1 files, source-season labels, corner history eligibility, valid AvgH/D/A rules and strictly earlier-date fixed180 means/dispersion. Odds features start in source season 2019/20; earlier rows provide corner warmup only. Do not splice odds families or use closing fallback. Retain all valid prior corner results in history even when the current quote is invalid. Preserve complete fixture pairs for calibration input and eventual comparison. No EPL outcome or feature is used for any fit, selection or preprocessing.

Do not fit the correction on in-sample predictions from the saved four-parameter joint fit. Construct temporal out-of-fold first-stage joint forecasts on these fixed date folds:

| First-stage training dates | OOF forecast dates |
|---|---|
| Eligible dates before 2020-07-01 | [2020-07-01, 2021-07-01) |
| Eligible dates before 2021-07-01 | [2021-07-01, 2022-07-01) |
| Eligible dates before 2022-07-01 | [2022-07-01, 2023-07-01) |

Each first-stage fit uses the original joint design, unit penalty and certified objective/solver, replacing only the training cutoff explicitly. No outcomes on or after that fold's start enter its four coefficients. Baseline histories and dispersion continue to update from dates strictly earlier than each forecast date, as in the saved rolling algorithm. July 2020 fixtures belong to their actual date fold even when their source season is 2019/20; do not silently redefine calendar folds as source-season folds.

The three first-stage fits are nuisance fits for OOF construction, not alternative candidates to select. They must not replace the published final joint coefficients. Fit the one delta using pooled home OOF rows only, with equal observation weights and no extra recency weight. Away rows contribute no delta-dependent likelihood and cannot tune the home correction. Use all three fixed folds; no fold selection, early-stop based on later scores or hyperparameter grid. The correction's fitting objective is in-sample for delta and must never be reported as out-of-sample evidence of its quality. A nested selection loop is unnecessary because there is no tuning or family selection inside this execution.

Development support checks, proposed as execution floors rather than power claims: at least 200 complete eligible fixtures for each first-stage training fit; at least 500 home OOF rows in total, 100 on each side of mu_J = 5, and 15 occupied 28-day blocks in each side. If any fails, stop and report inadequate support; do not adjust pivot, merge folds or relax floors after seeing results. Report counts by fold and side. OOF models have shorter training histories than the final base model; this transfer mismatch is a limitation, not a reason to retune against later data.

## Scalar fit and numerical stopping rules

Minimize over delta in [−0.5, +0.5]:

`sum_home_OOF NB_NLL(y_i; mu_Ji * exp(delta*x_i), alpha_i) + 0.5 * (delta / 0.25)^2`.

This retains the parent's coherent likelihood fit; Brier remains the evaluation objective, and a likelihood-fit improvement need not improve Brier. There is no second Brier-fitted candidate.

For mu = mu_J * exp(delta*x), gradient is `sum x*(mu-y)/(1+alpha*mu) + 16*delta`. Curvature is `sum x^2*mu*(1+alpha*y)/(1+alpha*mu)^2 + 16`, strictly positive, with the correct Poisson limit. Solve the monotone score by a bracketed scalar method on the fixed interval, using endpoint KKT signs if the minimizer is on a boundary. Require finite objective/coefficient/forecasts, derivative agreement with an independent NB implementation and, for an interior solution, absolute score <= 1e−8. Freeze solver tolerances in implementation tests; no automatic numerical fallback to another family.

Stop before opening later candidate scores if any nuisance fit fails certification, support fails, or the delta solution is nonpositive or boundary-limited. Nonpositive delta does not support the prespecified home expansion hypothesis; a boundary optimum suggests this deliberately modest family is inadequate. Record the fitted value and reason, keep the null, and do not expand the interval or try a different pivot/intercept. A positive interior delta is not evidence of future benefit—it only allows the one frozen historical comparison to proceed after execution has been authorized.

## Lock before later scoring

Freeze a manifest containing the base commit, original coefficient file hash, input hashes, fold dates, nuisance fit certificates, OOF prediction hashes, scalar coefficient/certificate, transform, penalty and output-schema hashes. The final joint base stays exactly as published at 7e8ad0acdcea13f5778e107882c36e5d6922fbd3; its coefficient training ended 2023-05-08. No final-base refit, retraining on later E1, EPL refit or correction update.

Mandatory null check: delta = 0 reproduces every saved joint mean, dispersion, probability and count score to numerical precision. Every away prediction must remain exactly unchanged for any delta. Keep the saved original odds adjustment and fixed180 as secondary context, never substitute either for the primary no-change joint control.

## Fixed historical comparisons

Primary comparison: candidate minus saved joint on the 1,599 eligible E1 fixtures / 3,198 team observations in source seasons 2023/24–2025/26, with exact published identity/order and exclusions. Report 2023/24 and 2024/25–2025/26 separately as prespecified context, but neither can replace the combined primary endpoint. Also report each source season descriptively; no every-season sign veto.

Secondary transfer: same frozen delta and original saved coefficients on EPL 2023/24–2025/26, 1,110 fixtures / 2,220 team observations, using the published EPL-only strictly earlier fixed180 histories. No EPL selection. Report full EPL 2019/20–2025/26 only as an explicitly overlapping supplementary retrospective application; it includes dates before coefficient and correction training, so cannot count as forward evidence or a replication. Require identity/order/observed-count/alpha agreement across candidate, joint and fixed180. Any discrepancy stops scoring; no silent fixture drops.

All these outcomes were repeatedly inspected and helped motivate this family. Call the exercise historical exploratory evaluation even though parameters are estimated using earlier dates. Neither a favorable E1 result nor EPL transfer repairs the original frozen rejections or qualifies for deployment.

## Metrics and compact safety assessment

Primary endpoint: fixture average of eight Brier losses, equal weights over home/away and lines 3.5–6.5, then equal weight per fixture. Compare with the unchanged joint model, not fixed180. Since away is identical, the all-fixture gain is exactly half the home-only four-line gain; show both so scale is clear. Under complements duplicate the same Brier information and are not extra independent endpoints.

Use the following compact outputs. The numerical continuation package below is proposed, not approved practical value:

| Quantity | Purpose | Proposed interpretation |
|---|---|---|
| Overall paired Brier difference | Primary incremental usefulness | Report 95% CI against both 0 and −0.001. Historical evidence of gain beyond the continuity benchmark requires upper bound < −0.001; a point gain of 0.001 and upper < 0 is weaker. |
| Overall count-NLL difference | Detect loss in full-distribution quality | Proposed safety upper bound < +0.005. No confusion with binary log loss. |
| Candidate home calibration-in-the-large at each of four lines | Test the motivating absolute probability error | Proposed safety intervals entirely inside ±0.02 probability. Report null errors and paired absolute-error changes too; do not halve a near-zero baseline error. |
| Brier difference on fixed low-probability home events | Guard against hiding damage to low probabilities | Membership frozen by saved joint p_line < 0.20, pooling the declared four line events with equal weight per included event. Same event rows for both models. Proposed safety upper bound < +0.001; report fixtures, event count and line composition. |
| Home AUC by line and macro average | Distinguish probability levels from risk ranking | Descriptive paired intervals; no invented approved tolerance. If declines are evident, withdraw any claim of preserved discrimination even if Brier improves. Away AUC is unchanged. |

The low-probability guard has an event-conditional estimand; it is not the primary equal-fixture estimand. Keep the forecast-dependent membership fixed to the null, not the candidate. A fixture with multiple qualifying lines stays intact in resampling. Support requires at least 100 distinct fixtures and 10 occupied blocks to interpret its interval; these floors alone do not demonstrate adequate power. If sparse or unstable, safety is unestablished and continuation is inconclusive.

Additional descriptive plots are limited to the already frozen five probability bins, separately by four lines and venue, for E1 later and post-training EPL. Show counts, mean probabilities, observed rates and error intervals for both models. Flag n<100 or <10 blocks; never merge or retune bins. Mean calibration can hide opposite errors, so show curves even if calibration-in-the-large improves. Report Brier decomposition with within-bin remainder and descriptive AUC; do not treat a coarse empirical calibration term as unbiased population miscalibration. No exploratory team, odds-strength, cutoff or betting-opportunity searches. Count MAE, RMSE and tails <=1/>=10 are secondary descriptions only.

## Uncertainty and multiplicity

Use complete fixture-paired date-ordinal//28-day blocks, 20,000 draws, seed 7, and ratio-of-resampled-totals means. Both venues, all lines and all models use shared draws within a cohort. Prespecify 14/56-day sensitivities for primary Brier and the safety package. Undefined empty-cell draws remain undefined; >1% undefined draws or materially different conclusions across block lengths makes the relevant conclusion inconclusive. Never select a favorable block width.

For the E1 safety claim only, define K=6: count NLL, four home calibration errors, and pooled low-probability Brier. Use Bonferroni family error 0.05: one-sided bounds at 1−0.05/6 for harm differences, and two-sided intervals with tails 0.05/12 for calibration. Shared draw vectors include all six quantities. The primary Brier endpoint is one prespecified comparison; descriptive line, AUC, seasonal, bin and EPL results receive pointwise intervals and no simultaneous claims. Adding more compulsory cells later requires a new plan, not post-result gate expansion.

These intervals remain conditional on fixed fitted models and the calendar-block assumptions. They do not account for architecture selection, all fitting uncertainty, long-lived team dependence or unknown drift. The family adjustment does not rehabilitate reused history. Conservative simultaneous bounds can leave this small experiment inconclusive; do not relax margins after seeing that result.

## Failure and decision rules

Before later scoring: stop for invalid provenance/cohorts, support failure, numerical failure, delta <= 0 or a constrained boundary optimum. Do not switch to another correction. A near-zero positive delta may proceed but is expected to behave like the null; do not amplify it manually.

After the one locked comparison, if the proposed numerical package is approved: classify as historically promising for future confirmation only when primary U < −0.001 and all six safety requirements pass robustly to block sensitivity, with adequate support. No deployment or historical-gate rewrite follows. If the primary lower bound exceeds −0.001, the declared incremental target is not supported at that precision; retire this candidate for that target. A simultaneous harm lower bound above its approved margin, or a simultaneous calibration interval wholly beyond the approved tolerance, likewise stops it. Borderline intervals, weak support or dependence sensitivity are inconclusive, not permission for another fit. A changed objective would require separate approval and a new study.

If the user instead authorizes a descriptive research run without approving practical margins, produce the same frozen estimates and intervals, label it diagnostic-only and make no pass/fail or safety-qualification claim. That is a pre-run scope choice, not a post-result escape route. In either mode the hypothesis can fail; improved count likelihood, one favorable line, an EPL gain or a bin-specific success cannot rescue a failed primary E1 result.

## Required approval and implementation handoff

Preparing this plan is authorized; executing it is not yet authorized. Before execution approve: (1) this home-only pivoted slope hypothesis rather than a pure intercept correction; (2) fixed pivot five, penalty SD 0.25, delta range and support/early-stop rules; (3) temporal OOF nuisance fits and the fixed final-base reuse; (4) the proposed numerical historical continuation package versus descriptive-only interpretation. The thresholds have continuity or conservative design rationales, not established user utility. They must not be selected to admit the existing candidate.

The original implementation agent should implement in an isolated research checkout, with an explicit data root and a train-before-cutoff API for nuisance fits. Do not run the published fit helper unchanged: it hardcodes the final cutoff, which would contaminate earlier OOF folds. First verify synthetic chronology, same-date exclusion, exact null recovery, unchanged away forecasts, coherent NB probabilities, stable derivatives and fold provenance. Run the existing clean-install suite. These are implementation prerequisites after authorization, not work executed by this planning task.

Deliver coefficient and training certificates; OOF and later prediction files; paired metric/safety intervals; all exclusion/support counts; plots; a report distinguishing exploratory from prospective evidence; and source/config/input hashes. No push, publication, live collection, new odds source or production-model edit is authorized by this plan.

Missing evidence for eventual qualification remains a separate prospective protocol with practical margins, adequate power and timestamped pre-outcome forecasts using source-matched odds. Nothing in this plan establishes executable corner prices, a betting strategy or profitability.
