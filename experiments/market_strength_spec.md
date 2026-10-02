# Frozen single-feature pre-closing 1X2 experiment

Frozen 2026-10-02 before candidate evaluation. Historical exploratory association/
predictive test only: source collection windows do NOT establish per-row quote
availability at a fixed prediction horizon. No live-readiness or betting-edge claim.

Use verified E1 source files 2017/18–2025/26. Build unchanged fixed180 corner
history with all completed fixtures. Use AvgH/AvgD/AvgA only from source seasons
2019/20 onward; earlier fixtures are corner warm-up only. Never splice BbAv,
Max, bookmaker or closing odds. Require all three finite decimal prices>1;
reject missing/invalid triplet for BOTH baseline/candidate scoring and coefficient
training. Do not impute or fall back. Keep valid rows regardless of overround;
normalize inverse odds q_i=1/o_i; p_i=q_i/SUM(q); home s=pH-pA, away s=-home s.
No goals/AH, clipping, nonlinear transforms, interactions or alternative features.

Single model mu=mu_fixed180*exp(beta*s), no new intercept, same baseline NB alpha.
Fit one real-valued beta ONCE using eligible source-season>=2019 observations
with match_date<2023-07-01. Minimize SUM of NB count NLL plus beta^2/2 (unit
Gaussian prior), equal training-observation weights. Baseline retains its own
180-day weighting; no extra recency weighting in coefficient estimation. Beta
then frozen forever for this run. No coefficient selection/refitting on validation
or test. Development fit objective is in-sample, never a forecast-quality claim;
candidate evaluation starts2023-07-01 so every scored outcome follows fit cutoff.

Convex scalar objective. Solve analytic score=0 with Brent root solver, expanding
symmetric bracket1,2,4,8,16,32,64 (numeric bracketing, not model search), xtol1e-12,
rtol1e-12, maxiter200. Require solver converged, finite beta, score magnitude<=1e-8,
and positive analytic curvature. Fail hard, no fallback. Stable NB expit/logaddexp;
Poisson limit alpha<=1e-12. Check analytic derivatives independently in tests.

Validation2023/24 [2023-07-01,2024-07-01), test2024/25–2025/26 thereafter.
Primary gates on combined later2023/24–2025/26. Also show test-only gates, never
substitute whichever is favorable. Source CSV defines season labels. Fixed180
mu ALWAYS defines extreme bands (<4, [4,6), >=6). Compare identical ordered
fixtures/venues/outcomes/alpha; pair blocks by date ordinal//28,2000 resamples,
seed7, inherited metric and bias helpers. Report Brier,count NLL,MAE,RMSE,
seasons/venues/bands/lines and paired intervals. Retained main is separate context.

Unchanged practical gates, ALL required:
Brier delta<=-0.001 and paired95%upper<0; improvement in each later season;
halve absolute bias in BOTH extreme bands; NLL delta<=0 and paired95%upper<=+0.005;
no venue Brier deterioration>+0.001. Failure means reject promotion of this
candidate. Passing means research-only pending timestamp-matched prospective
validation. Do not retune after seeing results. Pointwise intervals do not account
for all prior exploratory research or source-composition/timing drift.

Compare test-only Brier gain with the earlier reconstructed shots gain0.000786
(and prior-chat shot gain0.000513); historical comparison is descriptive, not an
independent selection contest. No new shots fit or additional candidate.
