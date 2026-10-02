# Frozen joint baseline / odds calibration — one exploratory candidate

Locked 2026-10-02 before fitting or evaluating this candidate. Parent diagnostic commit e85506a7f0d81e07ff69d786508e3c7de9571d29. Prior odds rejection unchanged. All later historical seasons already inspected: no independent holdout claim.

Function log(mu_new)=log(5)+a_venue+gamma*log(mu_fixed180/5)+beta*s.
Four real coefficients: a_home,a_away,gamma,beta. Implement theta=(a_home,a_away,gamma-1,beta), eta=log(mu_fixed180)+X*theta, X=(home indicator,away indicator,log(mu_fixed180/5),s). No global intercept, interactions, clipping, fitted dispersion, team effects or band switches. Unit ridge on all theta makes the convex objective strictly convex and uniquely identified even with correlated predictors. Baseline recovered at theta=0.

s = normalized inverse AvgH/AvgD/AvgA probability(home)-probability(away), signed oppositely for away. Same verified nine E1 datasets; only source seasons>=2019 provide odds features, earlier seasons corner warmup. Finite decimal triplet>1 required; drop fixture from every training/evaluation comparator if missing/invalid. No imputation, older BbAv splice, closing fallback or other features.

Fit ONCE on eligible dates<2023-07-01, equal observation weights, sum NB count NLL + .5*theta dot theta, fixed per-observation baseline dispersion (Poisson for alpha<=1e-12). No later refitting, tuning or variant search. Retain fixed180 earlier-date-only histories and original eligibility. This historical cutoff supersedes diagnostic's proposed use of all nine seasons for a future development fit: using all nine here would contaminate historical evaluation. No additional all-history fit in this task.

Use existing certified damped Newton solver from joint_strength.solve_newton: start theta0,100 iterations,60 step halvings, Armijo1e-4, stable exact objective differences. Require finite parameters, positive Hessian eigenvalues, analytic gradient max<=1e-8, Newton step max<=1e-8,decrement<=1e-12; independently recompute score with long-double accumulation and require max<=1e-8. Fail hard, no fallback or model change. Validate gradient/Hessian against numerical independent NB likelihood in tests.

Chronology: validation2023/24, test2024/25–2025/26; primary decision combined later; also report test-only all gates. Identical ordered fixture/venue/outcome/dispersion cohort for fixed180, unchanged saved original odds(beta=0.11376584000060998), new candidate. Verify original aggregate checkpoints. Baseline-defined bands <4,[4,6),>=6 for ALL comparisons. Bias actual−predicted. Evaluation weights equal per team observation, Brier average lines3.5,4.5,5.5,6.5.

Paired date-ordinal//28 blocks,2000 resamples seed7, pointwise95 percentile CIs. Reuse diagnostic bootstrap. Report Brier,NLL,MAE, means/bias, season/venue/band, <=1 and >=10 tail probabilities/errors/Brier, and intervals, versus BOTH comparators. Fixed180 sole primary comparator. Tail metrics prespecified secondary; no new gate replacing failed bias gates.

ALL primary practical gates required, unchanged from original odds experiment:
Brier delta<=-.001; Brier CI upper<0; every later season Brier improves;
NLL delta<=0 and upperCI<=+.005; each venue Brier worsening<=+.001;
abs(candidate bias)<=.5*abs(fixed180 bias) in BOTH extreme bands.
Failure=>reject under frozen gates. Pass=>research-only result requiring genuinely future confirmation, not deployment approval. No choosing favorable period/comparator. No score-driven early stopping or retuning. Historical missing exact quote timestamps and prior repeated inspection remain limitations.

This differs from a baseline-only generic recalibration by jointly estimating the conditional odds coefficient and baseline slope with venue intercepts; no reuse of a prior rejected calibration's parameters. No claim of isolating which new parameter causes changes without an ablation (none authorized/run). Future protocol will be stated separately, not executed.
