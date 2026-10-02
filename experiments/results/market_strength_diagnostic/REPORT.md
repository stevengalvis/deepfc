# Why the frozen odds feature fails the bias gates

**Keep the rejection. The strongest diagnostic concern is systematic high-forecast overprediction, not a uniformly excessive odds coefficient.** The middle band supplies most aggregate gains. Low-band failure is less conclusive statistically and depends on season and strength composition. No new coefficient was fitted and no original gate was changed.

## Verification and estimand

- Source: local commit `13116f9ab650f23275bdb28b645678fea7e192f3`. The original artifact saved aggregate results, not row predictions. Reconstructed fixed180 predictions using the existing nine verified CSVs and applied saved beta=0.11376584000060998; code/spec/data hashes checked and all period aggregate metrics reproduced within 1e-12. `predictions.csv` now preserves the 3,198 later team observations (1,599 fixtures).
- Ordered baseline/candidate match, venue, outcome and NB dispersion pairs are identical. No missing-price exclusions occurred. Bands use baseline mean only: <4, [4,6), >=6. No moving-band selection.
- Bias is mean(actual minus predicted): positive is underprediction; negative is overprediction. Candidate-minus-baseline bias equals minus the mean adjustment exactly. Tail calibration uses observed event frequency minus predicted probability, with the same sign convention.
- Training ended before 2023-07-01; last training outcome 2023-05-08; 4,224 equal-weight training observations and unit Gaussian beta penalty. Candidate evaluation begins after this cutoff. Validation is 2023/24 (1,048 observations), test is 2024/25–2025/26 (2,150); primary gate period combines all three. Season labels come from CSV files.
- Predictions retain fixed180 recency-weighted history and earlier-date-only updates. Evaluation, coefficient objective and slice means weight observations equally; seasons and venues are not reweighted in the original result. Brier averages over lines 3.5, 4.5, 5.5, 6.5.
- Uncertainty: 2,000 paired date-ordinal//28 block draws, seed 7, retaining both fixture sides and observation-count denominators. There are 33 blocks overall and in each main band. New bootstrap implementation matches the original helper on an unequal-block-size test. Intervals are pointwise and conditional on the frozen coefficient, not coefficient-estimation intervals.

## Aggregate gains versus band failures

Combined later deltas: Brier −0.001596 [−0.002110, −0.001089], count NLL −0.005168 [−0.007337, −0.002910], MAE −0.007615 [−0.014216, −0.001168]. Test-only results and all gates remain in the original report.

| Baseline band | n | Mean strength | Mean adjustment | Baseline bias | Candidate bias | Candidate bias 95% CI | Gate margin 95% CI |
|---|---:|---:|---:|---:|---:|---|---|
| lt4 | 369 | -0.303255 | -0.119010 | +0.018769 | +0.137778 | [-0.089736, +0.394113] | [-0.054828, +0.254081] |
| 4to6 | 2112 | -0.028306 | -0.007627 | +0.034814 | +0.042441 | [-0.091560, +0.169300] | Not a gate |
| ge6 | 717 | +0.239448 | +0.190988 | -0.288884 | -0.479872 | [-0.645438, -0.307815] | [+0.250310, +0.417798] |

Gate margin is |candidate bias| − 0.5|baseline bias|; positive fails. Original gates use the point estimate, not these added intervals. High-band margin stays positive throughout its interval; low-band margin includes zero. Low baseline bias itself has CI [−0.210602, +0.277055], so its near-zero pooled mean is not evidence of precise calibration.

| Band | Share of observations | Contribution to total Brier delta | Contribution to NLL delta | Contribution to MAE delta |
|---|---:|---:|---:|---:|
| lt4 | 11.54% | -0.000157 | -0.000620 | -0.001296 |
| 4to6 | 66.04% | -0.001394 | -0.005096 | -0.012786 |
| ge6 | 22.42% | -0.000046 | +0.000548 | +0.006467 |

The middle band contributes 87.32% of net Brier improvement. High-band NLL increases +0.002444 [−0.003030, +0.007614] and MAE increases +0.028844 [+0.005371, +0.050932]. Its tiny Brier improvement −0.000203 [−0.001691, +0.001170] does not establish a high-band gain. Its adverse MAE contribution cancels roughly half the middle-band contribution.

## Mechanism, heterogeneity and composition

For the unchanged model, adjustment = mu*(exp(beta*s)−1). Low-band strength averages −0.303, high-band +0.239. The linear term beta*mean(mu*s) accounts for −0.122 of the −0.119 low-band change and +0.186 of the +0.191 high-band change. Exponential convexity adds only +0.003/+0.005 respectively. Correlation between existing corner strength and odds strength, rather than exponential curvature alone, drives expansion of the forecast extremes. Aggregate strength is exactly zero because fixture sides have opposite signs, yet the mean forecast rises +0.024: mu and s are correlated.

High-band overprediction exists in all three seasons before the adjustment (bias −0.365, −0.271, −0.217) and increases after it (−0.561, −0.459, −0.405). All three candidate bias intervals exclude zero. It also worsens in both venues (home n=639, away n=78). The adverse adjustment persists after standardizing to common venue×strength-bin composition; it is not explained by changing broad season mix alone. However high-band NLL/MAE improve in 2025/26, so the claim is persistent bias, not universal loss deterioration.

Low-band seasons differ: 2023/24 bias −0.065→+0.056; 2024/25 −0.215→−0.083 (improves and passes that seasonal point bias criterion); 2025/26 +0.366→+0.468. These seasonal candidate intervals all include zero. Low-band n=369 includes 358 away observations and only 11 home observations, so a general home conclusion would be weak. Strong underdogs (n=225) improve bias −0.259→−0.088 and NLL −0.009934; mild underdogs (n=113) worsen +0.338→+0.402 and NLL +0.004726. Seven low-band strong favourites provide essentially no reliable standalone evidence.

At the high end, mild favourites (n=263) worsen bias −0.576→−0.683; strong favourites (n=355) move +0.152→−0.185. Underdogs in the high band instead improve bias. This pattern supports a missing conditional calibration adjustment, not the rule that all extreme observations should receive zero odds adjustment.

The mean unpenalized NLL derivative at the saved beta is +0.047655 in the high band (95% CI approximately [−0.000168,+0.092279]), versus −0.057506 in the middle band and −0.027 in the low band. A positive derivative implies that a small coefficient reduction would locally improve that slice’s NLL, but the high-band interval touches zero. No optimum was estimated. The negative overall derivative and strongly negative middle-band derivative argue against interpreting the result as universal over-adjustment. NB NLL training has no intercept or baseline-calibration slope and does not optimize the two absolute mean-bias gates.

Double-counting correlated strength, corner-specific baseline miscalibration, team mix, and quote/provider timing drift are plausible hypotheses. This observational decomposition cannot establish any of them causally. Conditioning on a baseline forecast band can also create selection effects; these are the prescribed diagnostic/gate bands, not randomly assigned populations.

### Composition-standardized seasonal bias

Pooled within-band weights for venue×four strength bins, restricted to cells present in all seasons. This is an arithmetic sensitivity check, not causal adjustment; within-bin odds, teams and outcomes can still differ. Values below are descriptive point estimates without additional intervals. Small common cells make especially the low-band standardization unstable.

| Band | Common-support n / original n | Season | Standardized baseline bias | Standardized candidate bias | Mean adjustment |
|---|---:|---|---:|---:|---:|
| lt4 | 359 / 369 | 2023 | -0.148317 | -0.010900 | -0.137417 |
| lt4 | 359 / 369 | 2024 | -0.137089 | -0.015684 | -0.121405 |
| lt4 | 359 / 369 | 2025 | +0.303984 | +0.420482 | -0.116498 |
| 4to6 | 2112 / 2112 | 2023 | +0.215275 | +0.223161 | -0.007886 |
| 4to6 | 2112 / 2112 | 2024 | -0.154107 | -0.147902 | -0.006205 |
| 4to6 | 2112 / 2112 | 2025 | +0.057241 | +0.065941 | -0.008700 |
| ge6 | 705 / 717 | 2023 | -0.379949 | -0.585478 | +0.205529 |
| ge6 | 705 / 717 | 2024 | -0.269126 | -0.458961 | +0.189834 |
| ge6 | 705 / 717 | 2025 | -0.220540 | -0.413220 | +0.192680 |

The low-band 2025/26 shift remains after broad composition adjustment; high-band negative bias remains every season. This rules out only this coarse composition explanation, not finer team/odds/timing changes or sampling noise.

## Tail calibration is a different target from mean Brier

Events are <=1 and >=10 corners, inherited from the earlier diagnostic. These events are outside the four thresholds averaged by the original Brier gate. Even a tail-specific Brier score mixes discrimination and calibration; its improvement does not require the group mean calibration error to shrink.

| Group / event | n | Observed | Baseline probability | Candidate probability | Candidate observed−predicted 95% CI | Tail Brier delta 95% CI |
|---|---:|---:|---:|---:|---|---|
| all / low_tail | 3198 | 0.07223 | 0.07674 | 0.07859 | [-0.014938, +0.002345] | [-0.000375, +0.000004] |
| all / high_tail | 3198 | 0.08161 | 0.08756 | 0.09162 | [-0.020514, +0.000630] | [-0.000451, +0.000297] |
| band=lt4 / low_tail | 369 | 0.14634 | 0.16751 | 0.18038 | [-0.075224, +0.009022] | [-0.001477, +0.001371] |
| band=lt4 / high_tail | 369 | 0.01355 | 0.01430 | 0.01219 | [-0.009757, +0.015381] | [-0.000056, +0.000017] |
| band=4to6 / low_tail | 2112 | 0.07292 | 0.07670 | 0.07811 | [-0.014413, +0.005029] | [-0.000428, -0.000094] |
| band=4to6 / high_tail | 2112 | 0.07055 | 0.06731 | 0.06794 | [-0.010250, +0.014931] | [-0.000627, -0.000185] |
| band=ge6 / low_tail | 717 | 0.03208 | 0.03015 | 0.02761 | [-0.009982, +0.018427] | [-0.000098, +0.000024] |
| band=ge6 / high_tail | 717 | 0.14923 | 0.18491 | 0.20226 | [-0.079434, -0.021338] | [-0.000735, +0.002243] |

High-band >=10 outcomes occur 14.92% of the time; probabilities rise from 18.49% to 20.23%. Candidate calibration error is −5.30 percentage points [−7.94, −2.13], versus baseline −3.57 points [−6.25, −0.40]. Low-band <=1 probability rises 16.75%→18.04% against 14.63% observed, but its error interval includes zero. Aggregate tail Brier changes are tiny and uncertain. Thus aggregate central-threshold gains coexist with a concrete high-tail calibration concern.

## Decision and one proposed next design

Preserve `reject_candidate_under_frozen_gates`: all six aggregate/season/venue safeguards passed, but BOTH extreme-band bias point gates failed. The low gate’s instability is a limitation of the original contract, not permission to reinterpret it as a pass. Retain fixed180 pending new research. A single global reduction of beta is not supported as the next design because it could discard useful middle-band and strong-underdog information.

One defensible next candidate is **joint regularized calibration of baseline and odds strength**: log(mu_new)=log(5)+a_venue+gamma*log(mu_fixed180/5)+beta*s, unchanged baseline dispersion. Four coefficients (home/away intercepts, shared gamma, shared beta), prior center (0,0,1,0), sum NB NLL plus 0.5*(a_home²+a_away²+(gamma−1)²+beta²). It can estimate whether baseline spread should contract while retaining incremental odds strength, without post-hoc band switches. This is a hypothesis motivated by this diagnostic, not an evaluated improvement.

Proposed fresh contract, to be formally locked before any candidate fitting:

1. Keep the nine existing source files and all availability, normalization, missing-triplet, unchanged-dispersion and identical-cohort rules. Use all eligible 2019/20–2025/26 observations as development training; all those outcomes and all these slices are already inspected, so no historical result will be labelled independent validation.
2. Fit those four coefficients once, jointly, with equal observation weights and the fixed unit penalties; no search, interactions, clipping, feature alternatives or seasonal refits. Use a convex damped Newton solve with analytic score/Hessian, gradient infinity norm <=1e-8 and positive Hessian certificate; fail on nonconvergence rather than changing model/penalties.
3. Prospective evaluation starts with fixtures dated 2026-10-03 or the day after actual formal registration, whichever is later, and ends before 2028-07-01. No intermediate performance-driven tuning or early stopping. Keep baseline updating strictly from prior dates while freezing correction coefficients. Score partial 2026/27 and full 2027/28 separately, explicitly labelling partial-season coverage.
4. Before collection, establish archived pre-match prices at a declared horizon (proposed kickoff−60 minutes, tolerance ±5 minutes) and matching sources; otherwise the prospective fixed-time protocol cannot start. Do not substitute closing odds. A separately described historical-source study would require its own registration and retain the timestamp limitation.
5. Primary comparator fixed180. Carry over every original gate unchanged on the full prospective cohort, including halving both baseline-defined extreme biases, the −0.001 Brier requirement and paired interval, each evaluation season improving, NLL and venue safeguards. Also report the frozen original odds candidate as descriptive secondary context; no choosing the more favorable comparator.
6. Same paired28-day bootstrap, 2000 draws, seed7; report Brier/NLL/MAE, bias, and <=1/>=10 tail calibration with n/blocks. Require >=100 observations in each extreme band and >=20 overall date blocks; otherwise classify evidence insufficient, do not extend end date after looking. Tail diagnostics remain prespecified secondary outcomes; they do not retroactively replace original gates.
7. No revised candidate was fitted or evaluated in this task. A future pass would still need careful interpretation because this architecture was selected after inspecting historical results; only the future outcomes provide new validation.

## Limits and reproduction

All three later seasons have been inspected repeatedly in shots, joint-strength, odds and now diagnostic analyses. Sixty overlapping slices and many metrics generate multiple-comparison risk; intervals are pointwise without selection correction. Few home low-band observations and some fine strength cells are especially unstable. Block resampling approximates time dependence but does not guarantee independence across teams or seasons. Quote timestamps are absent from historical files; this remains historical predictive evidence, not fixed-time deployability or betting-edge proof.

Run from the research checkout:

```bash
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.market_strength_diagnostic
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m pytest -q
```

95 tests passed, including boundary definitions, same-observation/sign identities, equivalence to the original paired bootstrap with unequal block sizes, and composition-standardization behavior. Original code/spec/results were not changed. Full numerical slices and intervals are in `results.json`, reconstructed observations in `predictions.csv`.

## Slice appendix

| Slice | n / blocks | Baseline bias | Candidate bias | Candidate bias 95% CI | Mean adjustment | Brier delta | NLL delta | MAE delta |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| all | 3198 / 33 | -0.039611 | -0.063663 | [-0.167246, +0.037997] | +0.024051 | -0.001596 | -0.005168 | -0.007615 |
| band=4to6 | 2112 / 33 | +0.034814 | +0.042441 | [-0.091560, +0.169300] | -0.007627 | -0.002111 | -0.007716 | -0.019361 |
| band=4to6/season=2023 | 672 / 11 | +0.193251 | +0.205641 | [+0.069034, +0.350557] | -0.012391 | -0.001740 | -0.008000 | -0.019729 |
| band=4to6/season=2023/venue=away | 362 / 11 | +0.061284 | +0.113683 | [-0.071759, +0.273791] | -0.052400 | -0.001399 | -0.006046 | -0.021688 |
| band=4to6/season=2023/venue=home | 310 / 11 | +0.347354 | +0.313025 | [+0.143121, +0.494545] | +0.034330 | -0.002139 | -0.010281 | -0.017441 |
| band=4to6/season=2024 | 675 / 11 | -0.158218 | -0.152436 | [-0.397892, +0.131880] | -0.005782 | -0.002195 | -0.007402 | -0.016537 |
| band=4to6/season=2024/venue=away | 385 / 11 | -0.235635 | -0.199539 | [-0.408361, +0.017727] | -0.036096 | -0.001894 | -0.005817 | -0.018683 |
| band=4to6/season=2024/venue=home | 290 / 11 | -0.055440 | -0.089903 | [-0.472136, +0.381303] | +0.034462 | -0.002594 | -0.009506 | -0.013689 |
| band=4to6/season=2025 | 765 / 11 | +0.065960 | +0.071030 | [-0.127209, +0.270967] | -0.005070 | -0.002362 | -0.007743 | -0.021529 |
| band=4to6/season=2025/venue=away | 416 / 11 | +0.030424 | +0.078453 | [-0.130024, +0.316373] | -0.048028 | -0.002215 | -0.007228 | -0.027101 |
| band=4to6/season=2025/venue=home | 349 / 11 | +0.108317 | +0.062183 | [-0.166304, +0.290009] | +0.046135 | -0.002538 | -0.008357 | -0.014887 |
| band=4to6/strength_bin=mild_favourite | 717 / 33 | +0.204890 | +0.141689 | [-0.089016, +0.375251] | +0.063201 | -0.000668 | -0.002432 | +0.000439 |
| band=4to6/strength_bin=mild_underdog | 801 / 33 | -0.090388 | -0.030267 | [-0.225686, +0.158795] | -0.060122 | -0.000230 | +0.000106 | -0.007802 |
| band=4to6/strength_bin=strong_favourite | 238 / 32 | +1.108856 | +0.874354 | [+0.484760, +1.201045] | +0.234502 | -0.008309 | -0.030124 | -0.048252 |
| band=4to6/strength_bin=strong_underdog | 356 / 32 | -0.744063 | -0.550025 | [-0.784664, -0.302883] | -0.194038 | -0.005104 | -0.020975 | -0.065930 |
| band=4to6/venue=away | 1163 / 33 | -0.048047 | -0.002608 | [-0.138932, +0.127577] | -0.045439 | -0.001855 | -0.006393 | -0.022629 |
| band=4to6/venue=home | 949 / 33 | +0.136359 | +0.097648 | [-0.084364, +0.269614] | +0.038712 | -0.002425 | -0.009336 | -0.015355 |
| band=ge6 | 717 / 33 | -0.288884 | -0.479872 | [-0.645438, -0.307815] | +0.190988 | -0.000203 | +0.002444 | +0.028844 |
| band=ge6/season=2023 | 254 / 11 | -0.364716 | -0.560552 | [-0.772264, -0.339259] | +0.195836 | +0.001165 | +0.005292 | +0.038761 |
| band=ge6/season=2023/venue=away | 46 / 9 | -0.198705 | -0.355000 | [-1.179036, +0.269008] | +0.156295 | +0.000381 | +0.001015 | +0.019966 |
| band=ge6/season=2023/venue=home | 208 / 11 | -0.401430 | -0.606011 | [-1.001745, -0.229295] | +0.204581 | +0.001338 | +0.006238 | +0.042917 |
| band=ge6/season=2024 | 261 / 11 | -0.270937 | -0.459278 | [-0.791085, -0.032062] | +0.188342 | -0.000299 | +0.002702 | +0.052378 |
| band=ge6/season=2024/venue=away | 22 / 9 | -0.437440 | -0.573837 | [-1.684859, +1.003027] | +0.136397 | +0.002666 | +0.008050 | +0.071440 |
| band=ge6/season=2024/venue=home | 239 / 11 | -0.255610 | -0.448733 | [-0.808997, -0.027382] | +0.193123 | -0.000572 | +0.002210 | +0.050623 |
| band=ge6/season=2025 | 202 / 11 | -0.216720 | -0.405031 | [-0.590200, -0.204161] | +0.188311 | -0.001800 | -0.001470 | -0.014033 |
| band=ge6/season=2025/venue=away | 10 / 7 | -1.117815 | -1.304424 | [-2.095980, -0.617238] | +0.186610 | +0.005067 | +0.022709 | +0.114231 |
| band=ge6/season=2025/venue=home | 192 / 11 | -0.169788 | -0.358188 | [-0.577033, -0.110963] | +0.188400 | -0.002157 | -0.002730 | -0.020713 |
| band=ge6/strength_bin=mild_favourite | 263 / 33 | -0.575806 | -0.682582 | [-1.052525, -0.320190] | +0.106776 | +0.001414 | +0.007385 | +0.030715 |
| band=ge6/strength_bin=mild_underdog | 80 / 23 | -1.215027 | -1.140249 | [-1.562617, -0.761134] | -0.074778 | -0.001931 | -0.008650 | -0.035682 |
| band=ge6/strength_bin=strong_favourite | 355 / 33 | +0.151555 | -0.185450 | [-0.477251, +0.117558] | +0.337005 | -0.000784 | +0.001890 | +0.045557 |
| band=ge6/strength_bin=strong_underdog | 19 / 13 | -0.646973 | -0.394446 | [-1.860608, +1.528459] | -0.252527 | -0.004462 | -0.008887 | -0.037630 |
| band=ge6/venue=away | 78 / 25 | -0.383875 | -0.538444 | [-1.114056, +0.008761] | +0.154569 | +0.001626 | +0.005781 | +0.046570 |
| band=ge6/venue=home | 639 / 33 | -0.277289 | -0.472722 | [-0.686462, -0.270494] | +0.195434 | -0.000427 | +0.002037 | +0.026680 |
| band=lt4 | 369 / 33 | +0.018769 | +0.137778 | [-0.089736, +0.394113] | -0.119010 | -0.001358 | -0.005375 | -0.011234 |
| band=lt4/season=2023 | 122 / 11 | -0.064905 | +0.056472 | [-0.183841, +0.215781] | -0.121377 | -0.001624 | -0.008607 | -0.010415 |
| band=lt4/season=2023/venue=away | 116 / 11 | -0.118101 | +0.001951 | [-0.249690, +0.188978] | -0.120051 | -0.001810 | -0.009899 | -0.014035 |
| band=lt4/season=2023/venue=home | 6 / 5 | +0.963543 | +1.110554 | [+0.028809, +1.883229] | -0.147011 | +0.001981 | +0.016377 | +0.059586 |
| band=lt4/season=2024 | 130 / 11 | -0.215248 | -0.082838 | [-0.385513, +0.276238] | -0.132410 | -0.002029 | -0.009111 | -0.014963 |
| band=lt4/season=2024/venue=away | 126 / 11 | -0.194505 | -0.063226 | [-0.393788, +0.308816] | -0.131278 | -0.002007 | -0.008384 | -0.012759 |
| band=lt4/season=2024/venue=home | 4 / 4 | -0.868677 | -0.700618 | [-1.982777, +1.380778] | -0.168059 | -0.002727 | -0.032014 | -0.084398 |
| band=lt4/season=2025 | 117 / 11 | +0.366037 | +0.467690 | [-0.110833, +1.047528] | -0.101652 | -0.000337 | +0.002145 | -0.007945 |
| band=lt4/season=2025/venue=away | 116 / 11 | +0.375538 | +0.476607 | [-0.105233, +1.058357] | -0.101069 | -0.000214 | +0.002356 | -0.006553 |
| band=lt4/season=2025/venue=home | 1 / 1 | -0.736064 | -0.566688 | [-0.566688, -0.566688] | -0.169376 | -0.014625 | -0.022273 | -0.169376 |
| band=lt4/strength_bin=mild_favourite | 24 / 14 | +0.884504 | +0.850281 | [-0.256213, +1.811950] | +0.034222 | -0.001499 | -0.005748 | -0.010675 |
| band=lt4/strength_bin=mild_underdog | 113 / 33 | +0.337827 | +0.402432 | [-0.090884, +0.913569] | -0.064605 | +0.000939 | +0.004728 | +0.004227 |
| band=lt4/strength_bin=strong_favourite | 7 / 6 | +0.839699 | +0.681671 | [-1.171970, +2.547885] | +0.158028 | -0.005597 | -0.020686 | -0.023498 |
| band=lt4/strength_bin=strong_underdog | 225 / 33 | -0.259355 | -0.088058 | [-0.304007, +0.157702] | -0.171297 | -0.002365 | -0.009933 | -0.018677 |
| band=lt4/venue=away | 358 / 33 | +0.014958 | +0.132810 | [-0.097450, +0.391628] | -0.117852 | -0.001362 | -0.005395 | -0.011162 |
| band=lt4/venue=home | 11 / 10 | +0.142771 | +0.299469 | [-0.784028, +1.194655] | -0.156698 | -0.001240 | -0.004734 | -0.013587 |
| period=test | 2150 / 22 | -0.072552 | -0.095950 | [-0.237809, +0.043167] | +0.023399 | -0.001876 | -0.005323 | -0.009149 |
| period=validation | 1048 / 11 | +0.027966 | +0.002577 | [-0.092692, +0.106043] | +0.025389 | -0.001023 | -0.004849 | -0.004469 |
| season=2023 | 1048 / 11 | +0.027966 | +0.002577 | [-0.092692, +0.106043] | +0.025389 | -0.001023 | -0.004849 | -0.004469 |
| season=2024 | 1066 / 11 | -0.192771 | -0.219076 | [-0.397933, -0.001460] | +0.026305 | -0.001710 | -0.005137 | +0.000528 |
| season=2025 | 1084 / 11 | +0.045672 | +0.025131 | [-0.116854, +0.166318] | +0.020541 | -0.002039 | -0.005507 | -0.018666 |
| strength_bin=mild_favourite | 1004 / 33 | +0.016631 | -0.057292 | [-0.274210, +0.161369] | +0.073923 | -0.000142 | +0.000060 | +0.008104 |
| strength_bin=mild_underdog | 994 / 33 | -0.132222 | -0.070411 | [-0.226051, +0.097585] | -0.061811 | -0.000234 | -0.000073 | -0.008679 |
| strength_bin=strong_favourite | 600 / 33 | +0.539313 | +0.245055 | [-0.003049, +0.488366] | +0.294257 | -0.003825 | -0.011072 | +0.007540 |
| strength_bin=strong_underdog | 600 / 33 | -0.559223 | -0.371861 | [-0.543739, -0.179197] | -0.187362 | -0.004057 | -0.016452 | -0.047314 |
| venue=away | 1599 / 33 | -0.050322 | +0.001573 | [-0.103761, +0.112363] | -0.051895 | -0.001575 | -0.005576 | -0.016686 |
| venue=home | 1599 / 33 | -0.028901 | -0.128898 | [-0.284167, +0.020059] | +0.099997 | -0.001618 | -0.004760 | +0.001456 |
