# Joint baseline and odds calibration: frozen historical experiment

**Reject under the frozen gates.** Joint calibration improves aggregate Brier, NLL and MAE against fixed180, but fails both extreme-band bias gates and the requirement that every later season improve Brier. The original odds candidate remains separately rejected; its artifacts have not been revised.

## Environment, design and fit

Execution availability was verified after the disconnect: clean research branch `research/shot-pressure-reconstruction` at `e85506a7f0d81e07ff69d786508e3c7de9571d29`, Python3.12.14, numpy2.5.3, scipy1.18.1 and pytest8.4.2. No startup or dependency blocker. No duplicate calibration implementation existed in this checkout.

One function was frozen before fitting: `log(mu_new)=log(5)+a_venue+gamma*log(mu_fixed180/5)+beta*s`. Two venue intercepts, shared baseline slope, shared signed normalized pre-closing 1X2 strength coefficient. The NB dispersion remains fixed180’s. Unit quadratic penalty around `(a_home,a_away,gamma,beta)=(0,0,1,0)`; no global intercept, redundant dummy, interactions, band switches or tuning. Ridge makes the four-parameter objective strictly convex and identifies a unique penalized solution.

This is distinct from a generic baseline-only calibration: odds strength and baseline slope are estimated jointly, so odds can explain conditional residual variation while the baseline spread can contract. No prior generic-calibration parameters or selection results were reused. It is also distinct from the earlier joint team attack/defence model, which estimated team effects. Without an ablation, this experiment cannot attribute gains uniquely to any one new parameter.

Historical fit: 4,224 observations dated before2023-07-01; last training outcome2023-05-08. Equal observation-weight summed NB NLL plus fixed penalty. The earlier diagnostic’s suggestion to use all nine seasons for future development training was explicitly superseded for this historical run to prevent training on its scored outcomes. No all-history refit was performed.

Coefficients: a_home=-0.008700478672, a_away=-0.018996804047, gamma=0.311629648602, beta=0.421563892072. Certified in 3 Newton iterations; independent score infinity norm 1.19e-09, minimum Hessian eigenvalue 184.783088. No fallback, variant search or later-period tuning.

All nine source hashes verified; finite AvgH/AvgD/AvgA triplets from2019/20 onward only, normalized inverse prices, zero invalid/missing triplets in this dataset. Earlier seasons provide corner warmup. Baseline and original-odds period checkpoints reproduce within1e-12. Identical ordered match/venue/outcome/dispersion pairs; 3,198 later observations (1,599 fixtures). Band membership always uses fixed180 means, including comparisons against original odds. Coefficient training and scoring use equal observation weights; fixed180 history itself retains 180-day weighting.

Intervals use paired28-day date-ordinal blocks,2,000 draws,seed7. CIs are conditional on fitted coefficients and pointwise; they neither correct previous research selection nor establish causal effects. There are33 combined blocks. All scored historical seasons were previously inspected.

## Aggregate metrics

| Period | Model | n | Brier | NLL | MAE |
|---|---|---:|---:|---:|---:|
| period=validation | fixed180 | 1048 | 0.210451 | 2.406443 | 2.200642 |
| period=validation | original_odds | 1048 | 0.209428 | 2.401594 | 2.196174 |
| period=validation | joint | 1048 | 0.210822 | 2.398647 | 2.180664 |
| period=test | fixed180 | 2150 | 0.208559 | 2.354073 | 2.120767 |
| period=test | original_odds | 2150 | 0.206683 | 2.348750 | 2.111618 |
| period=test | joint | 2150 | 0.204192 | 2.335888 | 2.062238 |
| all | fixed180 | 3198 | 0.209179 | 2.371235 | 2.146942 |
| all | original_odds | 3198 | 0.207583 | 2.366067 | 2.139327 |
| all | joint | 3198 | 0.206365 | 2.356455 | 2.101047 |

### Paired deltas: new joint candidate minus comparator

| Period | Comparator | Metric | Delta | 95% CI |
|---|---|---|---:|---|
| period=validation | fixed180 | brier_delta | +0.000371 | [-0.002640, +0.003406] |
| period=validation | fixed180 | nll_delta | -0.007796 | [-0.021427, +0.004468] |
| period=validation | fixed180 | mae_delta | -0.019978 | [-0.050038, +0.012151] |
| period=validation | original_odds | brier_delta | +0.001394 | [-0.001139, +0.003966] |
| period=validation | original_odds | nll_delta | -0.002947 | [-0.013291, +0.007001] |
| period=validation | original_odds | mae_delta | -0.015509 | [-0.041381, +0.011969] |
| period=test | fixed180 | brier_delta | -0.004367 | [-0.007032, -0.001865] |
| period=test | fixed180 | nll_delta | -0.018185 | [-0.025949, -0.010846] |
| period=test | fixed180 | mae_delta | -0.058528 | [-0.083298, -0.034040] |
| period=test | original_odds | brier_delta | -0.002491 | [-0.004873, -0.000075] |
| period=test | original_odds | nll_delta | -0.012862 | [-0.020031, -0.005434] |
| period=test | original_odds | mae_delta | -0.049379 | [-0.074542, -0.022611] |
| all | fixed180 | brier_delta | -0.002814 | [-0.005044, -0.000694] |
| all | fixed180 | nll_delta | -0.014780 | [-0.021710, -0.007803] |
| all | fixed180 | mae_delta | -0.045895 | [-0.066414, -0.025554] |
| all | original_odds | brier_delta | -0.001218 | [-0.003191, +0.000678] |
| all | original_odds | nll_delta | -0.009612 | [-0.016069, -0.003521] |
| all | original_odds | mae_delta | -0.038280 | [-0.059137, -0.018102] |

Combined Brier improves versus fixed180 with a negative interval; versus original odds, the combined Brier interval crosses zero. Test-only improvement versus original odds narrowly excludes zero. These are descriptive comparisons on previously inspected outcomes, not grounds to select the most favorable evaluation window.

## Every frozen gate

| Gate | Combined primary | Test-only |
|---|---|---|
| brier_material_improvement | PASS | PASS |
| brier_interval_below_zero | PASS | PASS |
| each_later_season_improves | FAIL | PASS |
| nll_not_worse | PASS | PASS |
| nll_upper_bound | PASS | PASS |
| venue_guardrail | PASS | PASS |
| halve_bias_lt4 | FAIL | FAIL |
| halve_bias_ge6 | FAIL | FAIL |

Brier materiality remains delta<=−0.001, paired upper<0; every later season must improve; NLL delta<=0 with upper<=+0.005; venue worsening<=+0.001; both extreme absolute biases must halve. Every gate is required. Test-only passes the season condition but still fails both bias gates. No tail metric substitutes for these conditions.

| Extreme band | n | Fixed180 bias | Original odds bias | Joint bias | Allowed joint absolute bias | Joint bias 95% CI | Bias gate margin 95% CI |
|---|---:|---:|---:|---:|---:|---|---|
| band=lt4 | 369 | +0.018769 | +0.137778 | -0.282712 | 0.009384 | [-0.497201, -0.039656] | [-0.096144, +0.394448] |
| band=ge6 | 717 | -0.288884 | -0.479872 | +0.351476 | 0.144442 | [+0.193552, +0.513528] | [-0.033855, +0.453440] |

Bias is actual minus predicted. The new model reverses both extremes: low means rise by0.301 corners and high means fall by0.640 on average, creating low-band overprediction and high-band underprediction. This is consistent with overly strong forecast compression on these later cohorts, but not proof that a different gamma would pass: no replacement gamma was tested. Low-band fixed180 bias is near zero, making its unchanged halving gate particularly stringent.

Gamma0.312 and beta0.422 represent a substantial redistribution of predictive weight, not simply a smaller odds coefficient. Aggregate MAE gains can coexist with signed subgroup bias because absolute error, NB likelihood and mean calibration measure different properties. Both fitted intercepts are negative; combined overall bias moves from−0.040 to+0.142 [+.040,+.239].

## Season, venue and baseline-band metrics and bias

Full periods, period×venue, period×band and season×band metrics/CIs are saved in results.json. The table below shows combined slices and later seasons for all three models.

| Slice | n | Model | Brier | NLL | MAE | Bias | Bias95% CI |
|---|---:|---|---:|---:|---:|---:|---|
| all | 3198 | fixed180 | 0.209179 | 2.371235 | 2.146942 | -0.039611 | [-0.143173, +0.061119] |
| all | 3198 | original_odds | 0.207583 | 2.366067 | 2.139327 | -0.063663 | [-0.167246, +0.037997] |
| all | 3198 | joint | 0.206365 | 2.356455 | 2.101047 | +0.141640 | [+0.039721, +0.239135] |
| season=2023 | 1048 | fixed180 | 0.210451 | 2.406443 | 2.200642 | +0.027966 | [-0.066658, +0.129408] |
| season=2023 | 1048 | original_odds | 0.209428 | 2.401594 | 2.196174 | +0.002577 | [-0.092692, +0.106043] |
| season=2023 | 1048 | joint | 0.210822 | 2.398647 | 2.180664 | +0.229937 | [+0.143512, +0.312671] |
| venue=home | 1599 | fixed180 | 0.214892 | 2.467561 | 2.343738 | -0.028901 | [-0.184900, +0.119436] |
| venue=home | 1599 | original_odds | 0.213274 | 2.462801 | 2.345194 | -0.128898 | [-0.284167, +0.020059] |
| venue=home | 1599 | joint | 0.212627 | 2.451417 | 2.287547 | +0.294453 | [+0.153227, +0.434055] |
| band=4to6 | 2112 | fixed180 | 0.216950 | 2.368323 | 2.136950 | +0.034814 | [-0.100458, +0.163236] |
| band=4to6 | 2112 | original_odds | 0.214839 | 2.360607 | 2.117589 | +0.042441 | [-0.091560, +0.169300] |
| band=4to6 | 2112 | joint | 0.212036 | 2.348480 | 2.084750 | +0.144544 | [+0.009588, +0.275279] |
| venue=away | 1599 | fixed180 | 0.203467 | 2.274909 | 1.950147 | -0.050322 | [-0.155627, +0.060574] |
| venue=away | 1599 | original_odds | 0.201892 | 2.269333 | 1.933460 | +0.001573 | [-0.103761, +0.112363] |
| venue=away | 1599 | joint | 0.200103 | 2.261492 | 1.914548 | -0.011173 | [-0.125189, +0.104901] |
| band=lt4 | 369 | fixed180 | 0.170646 | 2.125872 | 1.662493 | +0.018769 | [-0.210602, +0.277055] |
| band=lt4 | 369 | original_odds | 0.169287 | 2.120497 | 1.651259 | +0.137778 | [-0.089736, +0.394113] |
| band=lt4 | 369 | joint | 0.169017 | 2.115215 | 1.663303 | -0.282712 | [-0.497201, -0.039656] |
| band=ge6 | 717 | fixed180 | 0.206121 | 2.506088 | 2.425696 | -0.288884 | [-0.460338, -0.117276] |
| band=ge6 | 717 | original_odds | 0.205918 | 2.508532 | 2.454540 | -0.479872 | [-0.645438, -0.307815] |
| band=ge6 | 717 | joint | 0.208881 | 2.504098 | 2.374334 | +0.351476 | [+0.193552, +0.513528] |
| season=2024 | 1066 | fixed180 | 0.203762 | 2.340695 | 2.111709 | -0.192771 | [-0.370013, +0.024013] |
| season=2024 | 1066 | original_odds | 0.202052 | 2.335558 | 2.112237 | -0.219076 | [-0.397933, -0.001460] |
| season=2024 | 1066 | joint | 0.200060 | 2.324306 | 2.043801 | +0.023568 | [-0.155601, +0.252773] |
| season=2025 | 1084 | fixed180 | 0.213277 | 2.367229 | 2.129674 | +0.045672 | [-0.096293, +0.186901] |
| season=2025 | 1084 | original_odds | 0.211238 | 2.361722 | 2.111009 | +0.025131 | [-0.116854, +0.166318] |
| season=2025 | 1084 | joint | 0.208256 | 2.347279 | 2.080369 | +0.172386 | [+0.032950, +0.303148] |

2023/24 Brier worsens by+0.000371 [−0.002640,+0.003406] versus fixed180: uncertain statistically, but a failure of the prespecified point-estimate seasonal gate. Later seasons improve. High-band Brier worsens despite high-band MAE improvement; conclusions cannot be reduced to one aggregate score.

## Tail calibration

Events are <=1 and >=10 corners. Errors below are observed minus predicted probability. The original mean Brier uses different thresholds (3.5,4.5,5.5,6.5). Tail Brier and calibration-in-the-large are different measures; improving one need not improve the other.

| Slice | Event | n | Observed | Fixed180 p | Original odds p | Joint p | Joint error95% CI | Joint−fixed tail Brier95% CI |
|---|---|---:|---:|---:|---:|---:|---|---|
| all | low_tail | 3198 | 0.07223 | 0.07674 | 0.07859 | 0.08045 | [-0.016547, +0.000173] | [-0.001374, -0.000404] |
| all | high_tail | 3198 | 0.08161 | 0.08756 | 0.09162 | 0.07360 | [-0.002651, +0.018682] | [-0.001906, -0.000057] |
| period=validation | low_tail | 1048 | 0.07920 | 0.07392 | 0.07586 | 0.07900 | [-0.013799, +0.012422] | [-0.001846, +0.000174] |
| period=validation | high_tail | 1048 | 0.08683 | 0.08869 | 0.09302 | 0.07409 | [-0.005660, +0.027571] | [-0.002106, -0.000097] |
| period=test | low_tail | 2150 | 0.06884 | 0.07811 | 0.07992 | 0.08115 | [-0.022116, -0.002644] | [-0.001387, -0.000434] |
| period=test | high_tail | 2150 | 0.07907 | 0.08702 | 0.09094 | 0.07336 | [-0.006370, +0.018966] | [-0.002213, +0.000501] |
| band=lt4 | low_tail | 369 | 0.14634 | 0.16751 | 0.18038 | 0.14157 | [-0.035696, +0.047674] | [-0.005164, +0.000766] |
| band=lt4 | high_tail | 369 | 0.01355 | 0.01430 | 0.01219 | 0.02230 | [-0.020157, +0.005037] | [-0.000357, +0.000401] |
| band=4to6 | low_tail | 2112 | 0.07292 | 0.07670 | 0.07811 | 0.08216 | [-0.017802, +0.000535] | [-0.001456, -0.000421] |
| band=4to6 | high_tail | 2112 | 0.07055 | 0.06731 | 0.06794 | 0.06206 | [-0.004859, +0.021182] | [-0.001434, -0.000551] |
| band=ge6 | low_tail | 717 | 0.03208 | 0.03015 | 0.02761 | 0.04394 | [-0.026058, +0.001987] | [-0.000585, +0.000568] |
| band=ge6 | high_tail | 717 | 0.14923 | 0.18491 | 0.20226 | 0.13400 | [-0.010850, +0.047488] | [-0.005446, +0.002329] |

High-band 10+ observed frequency14.92% versus predicted18.49% fixed180,20.23% original odds,13.40% joint. Joint reduces that tail overprediction and crosses into underprediction, even while its high-band mean bias remains too large. Low-band <=1 observed14.63% versus16.75%,18.04%,14.16% respectively: better calibration for this event does not establish mean calibration or a passed bias gate. Tail improvements are secondary evidence, not a retroactive change to acceptance criteria.

## Prospective confirmation protocol — specified, not started

This historical candidate failed; no live challenger or data collection is authorized by this report. If a future confirmation study is approved, preregister the following contract before receiving any scored outcomes:

1. Freeze exactly these four coefficients, current feature/schema/normalization, unchanged fixed180 dispersion and chronological histories. No all-history refit, coefficient variants or outcome-dependent updates to the correction. Baseline histories continue to update from strictly earlier fixture dates.
2. Start scoring no earlier than2026-10-03 and no earlier than the first full UTC day after protocol registration and successful timestamp/source validation, whichever is later. End before2028-07-01. If setup cannot occur before2027-07-01, cancel this protocol and preregister a new window before observing its outcomes rather than silently shortening it.
3. Validate archived source-matched odds snapshots at kickoff−60 minutes with ±5-minute tolerance, including quote, capture and kickoff timestamps. Exclude unavailable/invalid snapshots identically for all comparators; report coverage against all eligible fixtures. Historical source files cannot establish that horizon, so source/timestamp verification is a prerequisite, not an assumption. No collection was started here.
4. Primary comparison joint versus fixed180; original odds frozen candidate secondary context. Use identical fixtures, fixed180-defined bands, full future window primary and each source season separately. Label2026/27 partial coverage. No peeking-driven stopping, window changes, model selection or alternative comparators.
5. Retain all eight gates in this specification, same paired28-day bootstrap,2000 draws,seed7, and report every metric and tail diagnostic. Require>=100 observations in each extreme band and>=20 total blocks; otherwise evidence insufficient at the fixed end date. No extending or changing the bias threshold after seeing results.
6. Outcome-based conclusions concern only the future window; historical performance and this design choice remain exploratory. Even a future statistical pass alone would not establish profitable betting or automatically authorize deployment.

## Verification, limitations and reproduction

98 tests passed. New tests check the four-parameter gradient against independent NB likelihood, Hessian via numerical derivatives, positive curvature, exact exclusion of future outcomes, the prediction-date guard, neutral-parameter baseline recovery, and explicit venue/strength design. Existing tests cover normalization, invalid prices, pairing, bands, and paired bootstrap behavior. Original odds code/spec/results and diagnostic artifacts remain unchanged.

No per-quote timestamps exist in historical data; current-match odds are historical covariates, not a proven fixed-time information set. Prior model experiments and extensive slice inspection create selection/multiple-comparison uncertainty. Pointwise block intervals do not capture all coefficient uncertainty, season shifts, repeated team dependence or source changes. Correlated baseline/odds features and architecture selection prevent causal attribution. The pronounced contraction is an observed fitted behavior, not an invitation to tune gamma using scored seasons.

From /workspace/deepfc-shot-reconstruction:

```bash
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.joint_market_calibration > experiments/results/joint_market_calibration/run.txt
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m pytest -q
```

Specification: experiments/joint_market_calibration_spec.md. Code/spec SHA256 values were saved before candidate execution in frozen_hashes.txt and match results.json. The executable prints numerical certificate and all gates; results.json preserves both comparator analyses and all slice intervals. No revision was fitted after observing these results.
