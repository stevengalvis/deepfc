# One mean-preserving conditional-dispersion ablation

**Status: plan only, 2026-10-02. No new parameters fitted or candidate scores run.** Starting checkout: `49544a9fb5c3c31bbc2909c979d9c5af0b25ba96`. Execution requires separate authorization. Numerical decision margins below are proposed research assumptions, not accepted operational risk tolerances.

## Motivation and boundary of the evidence

Yip, Zou, Hung and Yiu study **match-total corners**, with NB shape regressed on log absolute market-implied goal supremacy. Their market inversion uses a goal model; it is not the normalized 1X2 feature proposed here. Varying-shape NB improved their LOO density comparison, which is not chronological validation. Their historical betting simulation reports 5.785% ROI, with negative results in EPL and Champions League. Neither result establishes team-corner accuracy or a transferable edge. This plan extrapolates their conditional-dispersion idea, not their coefficients, market timing, or profitability. [Full manuscript, §§2.4, 3.1.2, 3.3, 4–5](https://arxiv.org/html/2112.13001); [JORS 2024 publication](https://doi.org/10.1080/01605682.2024.2306170).

**Hypothesis:** after holding the leading joint-calibration means fixed, residual count spread may vary with pre-match competitive imbalance. A conditional NB shape could improve line probabilities without changing expected counts. This is a predictive hypothesis, not proof of corner clustering or a causal strength effect. No claim that a public practitioner model outperforms DeepFC is needed.

Prior work checked: commit `8ab1074e17651f620e166573d2812883c2fae04e`, `experiments/dispersion.py` and `experiments/results/championship_dispersion.md`, compared pooled/venue and equal/180-day **marginal moment** estimates. The selected alternative failed later; that decision stands. This is distinct because it estimates shape from conditional likelihood given fixed means. The recent goal-total and residual-persistence failures also stand. Geometric-Poisson and NGBoost are deferred, not additional candidates in this study.

## Three arms, one feature, immutable means

| Arm | Mean for every row | Dispersion alpha | Purpose |
|---|---|---|---|
| A: saved joint/current dispersion | Saved leading joint mean | Saved earlier-history pooled moment alpha | Existing comparator |
| B: constant conditional likelihood | Exact same mean | exp(a), one fitted scalar | Isolates estimator change |
| C: conditional likelihood | Exact same mean | exp(a+b z), two fitted scalars | Isolates incremental conditioning versus B |

Normalize pre-closing `AvgH,AvgD,AvgA`: p_j=(1/odds_j)/sum_k(1/odds_k). Define **z=abs(p_H−p_A)−0.5**. This fixed center gives z in [−0.5,0.5]; no empirical scaling. One unsigned imbalance feature shared by both teams, no venue interaction, splines, log alternatives, league effects, or goal-market inversion. b has no imposed sign. This is a probability-imbalance proxy, **not measured or inferred goal supremacy**. Require finite prices >1 and complete paired fixture forecasts. Exclude an invalid fixture from every arm, report it, never substitute bookmaker/closing odds. No new data sources or downloads.

For all arms Y~NB(mu,k), k=1/alpha:

`E[Y]=mu; Var[Y]=mu+alpha*mu²`

`log P(Y=y)=lgamma(y+k)−lgamma(k)−lgamma(y+1)+k log(k/(k+mu))+y log(mu/(k+mu))`.

Compute the **full** count likelihood: terms involving k cannot be dropped while fitting alpha. Changing shape must never alter mu or imply a mean refit. Mean bias, mean MAE and RMSE are consequently identical row by row; assert this and do not apply the old mean-bias gates. Dispersion may partially mask mean misspecification rather than solve it; discuss that limitation explicitly.

## Fit rule, regularization and numerical guardrails

B minimizes summed full NB NLL over eligible team observations, equally weighted. C minimizes the same sum plus **0.5*(b/0.25)²**, with unpenalized a. Thus B is the exact b=0 nested control; its intercept is not differently regularized. The fixed Normal(0,0.25²) slope penalty is a strong shrinkage assumption: a 95% prior span corresponds approximately to a 0.61–1.63 dispersion ratio across the entire imbalance range. It is not estimated from later scores. No penalty search.

Use alpha in **[1e−4,1]** throughout z∈[−0.5,0.5]: impose log(1e−4)≤a−0.5b and a+0.5b≤0, and the corresponding other endpoint inequalities. These deliberately broad numerical limits span near-Poisson to substantial overdispersion; they are engineering assumptions, not empirical estimates. A retains its saved alpha even if outside this candidate domain. Never clip candidate predictions after fitting.

For execution: bounded scalar optimization for B; constrained two-parameter optimization for C. Fixed numerical starts at the B optimum with b=0,+0.25,−0.25, projected into the feasible domain; choose lowest **training objective** only. These are numerical checks of one model, not candidate variants. Require finite likelihood/probabilities, independent finite-difference gradient agreement, projected/KKT score norm≤1e−6, and objective agreement across successful starts within1e−8 per observation. Record parameters, objective, convergence, constraints and bound distances. No claim of convexity/global uniqueness. Failure, unresolved starts or a bound within1e−6 makes the fit numerically inconclusive; stop without expanding limits or changing model form. Use stable log/gamma calculations and verify against the existing NB implementation and Poisson limit before any fit.

## Leakage-safe early chronology

Use saved artifacts under `experiments/results/distribution_blend`, `joint_market_calibration`, `market_strength`, and E0 transfer; verify all inherited raw/derived hashes.

1. Reconstruct fixed180 forecasts using strictly earlier dates, and **saved joint fold coefficients** from `distribution_blend/selection.json`: the 2021/22 mean component was fitted before July1,2021; the 2022/23 component before July1,2022. Neither component saw its scored season. Reset only the component by its already-saved fold rule, not the baseline histories.
2. Development fit B/C dispersion on the **2021/22 out-of-fold** means/outcomes (expected1,064 team observations). Compare all three arms on **2022/23 out-of-fold** means/outcomes (expected1,084), keeping the dispersion coefficients fitted on2021/22 fixed. Mean-component refresh before2022/23 may use2021/22 outcomes; no2022/23 outcome enters either component or dispersion fitting for those predictions.
3. There is **no feature, penalty or arm winner selection**: all three constitute the one predeclared ablation. The early comparison is the only development assessment. Report unfavorable results unchanged; no tuning. For the final frozen dispersion estimates, pool the two early OOF seasons (expected2,148 team observations) and refit B/C once with identical objectives. This is calibration training on out-of-fold means, not a later evaluation result.
4. Save coefficients, source/code/spec hashes and numerical certificates **before** later evaluation. Apply B/C unchanged to the saved final joint means, whose component was fitted on early E1 dates<2023-07-01 (last training date May8,2023). Those final means are immutable. The transfer from early fold mean fits to the final mean fit is an explicit calibration-transfer assumption, not validation of identical fitted mean parameters. Do not fit dispersion using the final joint model's in-sample training residuals.

No fitting or choice on later Championship or any EPL outcomes. No new joint-mean component fit is needed. The available OOF fit population is smaller than the final mean model's training population; quantify resulting uncertainty rather than silently adding in-sample residuals.

## Frozen evaluation and inference

Use exact paired fixture/venue identities from `distribution_blend/predictions.csv`, subject only to the declared quote validity check: E1 **2023/24–2025/26,3,198 team observations/1,599 fixtures**; E0 **2019/20–2025/26,5,142/2,571**. EPL through May31,2023:2,922/1,461, retrospective. EPL after May31,2023:2,220/1,110, chronology-qualified transfer. Do not pool early retrospective EPL with later EPL for a confirmation claim. Existing data have already been inspected, so even later windows are exploratory validation.

Primary endpoint: equal-weight Brier over team-corner lines3.5,4.5,5.5,6.5, averaging eight events per fixture. Report **C−B** to test conditioning, **B−A** for estimation, and **C−A** for total change. Negative loss differences favor the first arm. Report count NLL, individual line calibration, zero count and tails<=1/>=10 (observed frequency, predicted probability, calibration error and event Brier). Mean MAE/bias invariance is a correctness check, not a target.

Show season, home/away, fixed180-mean bands<4/[4,6)/>=6, and fixed imbalance bands abs(p_H−p_A)<.2/[.2,.5)/>=.5. Preserve membership across arms. Sparse cells get counts and wide intervals, not collapsed thresholds selected after scoring. Include each season and EPL era; report full alpha ranges and boundary rates by cohort to detect extrapolation/source shifts.

Paired calendar-block bootstrap:28days,10,000 resamples, seed7, preserving both fixture sides and all lines; fixed56/84-day overall sensitivities. Reuse paired draws for every arm contrast. Intervals are conditional on frozen fits and omit component/dispersion fitting and research-selection uncertainty. Report block counts and low-precision cells; do not use iid team observations. A dependence-sensitivity disagreement is inconclusive. No league-specific rescue tuning or repeated peeking.

## Proposed interpretation, not approved deployment gates

**Working assumptions for discussion:** worthwhile Brier gain delta=0.001 (consistent with the earlier research proposal, roughly0.5% of a .20 Brier); overall NLL harm margin0.005 nats/team observation (a small tolerance, not an economically justified cost); subgroup Brier harm margin0.001 and worsening absolute line/tail calibration error margin0.02 (two probability points). These values are judgments, not supplied by Yip or approved by Steve. Report point estimates and intervals relative to both zero and these references; do not convert them into official pass/fail gates without agreement.

- Conditioning support requires favorable C−B evidence as well as C−A. If only B improves A, the evidence supports conditional-likelihood estimation, **not odds-conditioned shape**.
- A stricter provisional research-qualification reading would require upper95% bounds of both C−B and C−A below−0.001 in E1 and post-May EPL, no established material NLL/calibration harm, and stable dependence checks. Requiring all contrasts/cohorts prevents a favorable-arm/league choice; it may be underpowered. Subgroup intervals remain exploratory, not simultaneous safety certification.
- A lower bound above−0.001 rules out that proposed gain at the stated interval level; it does not establish general inferiority. Clear positive harm beyond the proposed margin is a reason not to advance. Overlapping bounds, sparse calibration cells or conflicting league/dependence evidence mean **inconclusive**. Do not equate failure to show harm with noninferiority or declare equivalence.
- No every-season point-sign veto, no mean-bias-halving gate, and no revision of prior experiment rejections. No profitability/edge claim: executable corner prices, fixed quote timestamps and an independently tested betting policy are absent.

## Requirements and execution checklist

Existing local data/derived forecasts and saved Python3.12 environment with pinned NumPy/SciPy/pytest suffice. CPU only; two paired scalar/two-parameter fit stages plus vectorized bootstrap, no MCMC/GPU or new vendor data. A modest minutes-scale run is expected, not benchmarked. Keep provider rows out of Git. Steve describes current work as private/noncommercial; that description alone does not establish dataset permissions. This plan neither obtains a new license nor authorizes redistribution/publication; before any later use beyond existing authorized scope, resolve rights for that use.

1. Obtain separate execution authorization; agree whether proposed margins remain descriptive or become research decision rules. No additional feature-choice decision is required.
2. Freeze code/spec/input manifest, exact cohort keys and saved mean arrays; confirm licenses/usage scope for the intended execution without inferring rights from noncommercial status.
3. Test PMF normalization/expectation, C at b=0 equals B, gradients/constraints, invalid odds/no closing fallback, chronology, and exact mean/MAE/bias equality across arms. No scored experiment until these pass.
4. Run early fit/assessment then final OOF dispersion fits; save all numerical certificates and hashes before later scores. Stop on integrity/numerical failure; no silent fallback.
5. Run frozen E1/E0 comparisons and slices once; report counts, uncertainty, failures/inconclusive outcomes and calibration tradeoffs. Preserve prior results.
6. Save private local code/results/report; no push, PR, merge, deployment or public paper/data release without separate authorization.

**Deliverable now:** this plan only. No new candidate implementation, fitting, scoring, data download or publication was performed. The pending decision is execution authorization and, if formal qualification is desired, explicit approval of numerical margins.
