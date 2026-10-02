# Joint attack/defence experiment result

Decision: **reject_candidate**. One candidate; historical evaluation remains exploratory. No production or Zeno changes.

## Periods

| Period | Model | n | Brier | Count NLL | MAE |
| --- | --- | ---: | ---: | ---: | ---: |
| development | baseline | 5218 | 0.217140 | 2.338689 | 2.073609 |
| development | candidate | 5218 | 0.220991 | 2.357729 | 2.109191 |
| development | retained main (context) | 5218 | 0.217664 | 2.340010 | 2.084538 |
| validation | baseline | 1048 | 0.210451 | 2.406443 | 2.200642 |
| validation | candidate | 1048 | 0.213056 | 2.423172 | 2.240407 |
| validation | retained main (context) | 1048 | 0.216428 | 2.425427 | 2.244784 |
| test | baseline | 2150 | 0.208559 | 2.354073 | 2.120767 |
| test | candidate | 2150 | 0.211349 | 2.372274 | 2.155232 |
| test | retained main (context) | 2150 | 0.210927 | 2.358525 | 2.130975 |
| combined_later | baseline | 3198 | 0.209179 | 2.371235 | 2.146942 |
| combined_later | candidate | 3198 | 0.211908 | 2.388954 | 2.183144 |
| combined_later | retained main (context) | 3198 | 0.212730 | 2.380449 | 2.168271 |
| all | baseline | 8416 | 0.214115 | 2.351056 | 2.101475 |
| all | candidate | 8416 | 0.217539 | 2.369594 | 2.137292 |
| all | retained main (context) | 8416 | 0.215789 | 2.355377 | 2.116355 |

## Paired uncertainty

Candidate minus fixed180; 28-day blocks, 2000 draws, seed7. Pointwise intervals, not multiplicity-adjusted.

| Period | Metric | Difference | Lower 95% | Upper 95% |
| --- | --- | ---: | ---: | ---: |
| development | mean_brier_score | +0.003851 | +0.002774 | +0.005022 |
| development | negative_binomial_negative_log_loss | +0.019040 | +0.014414 | +0.023878 |
| development | mae | +0.035581 | +0.025408 | +0.045435 |
| validation | mean_brier_score | +0.002605 | +0.001197 | +0.004017 |
| validation | negative_binomial_negative_log_loss | +0.016730 | +0.010041 | +0.024369 |
| validation | mae | +0.039764 | +0.018207 | +0.067036 |
| test | mean_brier_score | +0.002789 | +0.001349 | +0.004246 |
| test | negative_binomial_negative_log_loss | +0.018201 | +0.011780 | +0.025618 |
| test | mae | +0.034465 | +0.020741 | +0.048889 |
| combined_later | mean_brier_score | +0.002729 | +0.001687 | +0.003789 |
| combined_later | negative_binomial_negative_log_loss | +0.017719 | +0.012930 | +0.023083 |
| combined_later | mae | +0.036202 | +0.024191 | +0.050131 |
| all | mean_brier_score | +0.003425 | +0.002607 | +0.004287 |
| all | negative_binomial_negative_log_loss | +0.018538 | +0.015097 | +0.022251 |
| all | mae | +0.035817 | +0.027945 | +0.044073 |

## Predeclared gates

Primary gate cohort is combined later periods (2023/24–2025/26), fixed before running. All gates must pass. Test-only gates are reported separately, not substituted.

| Gate | Combined later | Test only |
| --- | --- | --- |
| brier_material_improvement | FAIL | FAIL |
| brier_interval_below_zero | FAIL | FAIL |
| each_later_season_improves | FAIL | FAIL |
| nll_not_worse | FAIL | FAIL |
| nll_upper_bound | FAIL | FAIL |
| venue_guardrail | FAIL | FAIL |
| halve_bias_lt4 | FAIL | FAIL |
| halve_bias_ge6 | FAIL | FAIL |

## Season slices

| Source season | n | Brier baseline | Brier candidate | NLL delta | MAE delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2018/2019 | 994 | 0.219058 | 0.224478 | +0.024942 | +0.047423 |
| 2019/2020 | 1046 | 0.215633 | 0.218675 | +0.015699 | +0.028232 |
| 2020/2021 | 1030 | 0.219015 | 0.223454 | +0.020216 | +0.044240 |
| 2021/2022 | 1064 | 0.215521 | 0.218401 | +0.016042 | +0.026812 |
| 2022/2023 | 1084 | 0.216641 | 0.220228 | +0.018678 | +0.032196 |
| 2023/2024 | 1048 | 0.210451 | 0.213056 | +0.016730 | +0.039764 |
| 2024/2025 | 1066 | 0.203762 | 0.206194 | +0.015254 | +0.041610 |
| 2025/2026 | 1084 | 0.213277 | 0.216418 | +0.021099 | +0.027439 |

## Venue and baseline-defined bands

| Period | Slice | n | Baseline bias | Candidate bias | Brier delta | NLL delta | MAE delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| development | venue/home | 2609 | -0.028354 | -0.009329 | +0.003993 | +0.017812 | +0.039108 |
| development | venue/away | 2609 | -0.026911 | -0.003421 | +0.003710 | +0.020268 | +0.032055 |
| development | band/lt4 | 525 | +0.489000 | +0.850201 | +0.011359 | +0.070315 | +0.077196 |
| development | band/4to6 | 3941 | -0.046349 | +0.008245 | +0.002678 | +0.010572 | +0.014704 |
| development | band/ge6 | 752 | -0.290225 | -0.681006 | +0.004756 | +0.027620 | +0.115944 |
| validation | venue/home | 524 | +0.057183 | +0.027844 | +0.003680 | +0.021361 | +0.055112 |
| validation | venue/away | 524 | -0.001251 | +0.030023 | +0.001530 | +0.012098 | +0.024417 |
| validation | band/lt4 | 122 | -0.064905 | +0.346206 | +0.001314 | +0.017345 | +0.016108 |
| validation | band/4to6 | 672 | +0.193251 | +0.268104 | +0.001453 | +0.009421 | +0.005058 |
| validation | band/ge6 | 254 | -0.364716 | -0.756223 | +0.006271 | +0.035771 | +0.142950 |
| test | venue/home | 1075 | -0.070861 | -0.033120 | +0.002741 | +0.020494 | +0.031553 |
| test | venue/away | 1075 | -0.074242 | -0.055530 | +0.002838 | +0.015908 | +0.037378 |
| test | band/lt4 | 247 | +0.060097 | +0.411391 | +0.001869 | +0.024563 | +0.006899 |
| test | band/4to6 | 1440 | -0.039124 | +0.036392 | +0.003187 | +0.016881 | +0.020821 |
| test | band/ge6 | 463 | -0.247283 | -0.538480 | +0.002043 | +0.018913 | +0.091608 |
| combined_later | venue/home | 1599 | -0.028901 | -0.013142 | +0.003048 | +0.020778 | +0.039273 |
| combined_later | venue/away | 1599 | -0.050322 | -0.027494 | +0.002409 | +0.014659 | +0.033130 |
| combined_later | band/lt4 | 369 | +0.018769 | +0.389840 | +0.001685 | +0.022177 | +0.009944 |
| combined_later | band/4to6 | 2112 | +0.034814 | +0.110118 | +0.002635 | +0.014507 | +0.015805 |
| combined_later | band/ge6 | 717 | -0.288884 | -0.615616 | +0.003541 | +0.024885 | +0.109796 |
| all | venue/home | 4208 | -0.028562 | -0.010778 | +0.003634 | +0.018939 | +0.039171 |
| all | venue/away | 4208 | -0.035807 | -0.012568 | +0.003216 | +0.018137 | +0.032464 |
| all | band/lt4 | 894 | +0.294911 | +0.660186 | +0.007366 | +0.050446 | +0.049438 |
| all | band/4to6 | 6053 | -0.018030 | +0.043791 | +0.002663 | +0.011945 | +0.015088 |
| all | band/ge6 | 1469 | -0.289571 | -0.649090 | +0.004163 | +0.026285 | +0.112943 |

Bias = actual minus expected corners. Band membership ALWAYS uses fixed180 mu, never candidate mu. JSON includes pointwise paired metric and bias intervals for every slice.

## Line checks

| Period | Line | Brier difference |
| --- | ---: | ---: |
| development | 3.5 | +0.004136 |
| development | 4.5 | +0.004201 |
| development | 5.5 | +0.003740 |
| development | 6.5 | +0.003327 |
| validation | 3.5 | +0.001982 |
| validation | 4.5 | +0.002505 |
| validation | 5.5 | +0.002947 |
| validation | 6.5 | +0.002984 |
| test | 3.5 | +0.002970 |
| test | 4.5 | +0.002060 |
| test | 5.5 | +0.003195 |
| test | 6.5 | +0.002932 |
| combined_later | 3.5 | +0.002647 |
| combined_later | 4.5 | +0.002206 |
| combined_later | 5.5 | +0.003114 |
| combined_later | 6.5 | +0.002949 |
| all | 3.5 | +0.003570 |
| all | 4.5 | +0.003443 |
| all | 5.5 | +0.003502 |
| all | 6.5 | +0.003184 |

## Fit audit and reproducibility

895 forecast-date fits passed. Maximum projected gradient 9.66102065e-09; maximum iterations 5. No omitted fixtures or fallback forecasts.

Three earlier generic-solver attempts failed in development and were not accepted. The authorized repair kept the statistical objective fixed, used identifiable orthonormal coordinates, and computed exact objective differences with expm1/log1p. Final convergence requires gradient<=1e-8, Newton step<=1e-8, decrement squared<=1e-12, positive curvature and an independent long-double score check. Full development finite-difference, independent BFGS and different-start checks are in numerical_repair/development_checks.json. The revised numerical contract was frozen before the successful evaluation; statistical gates were never changed.

80 tests passed. Coverage includes NB objective/analytic-gradient agreement, identifiability, unseen teams, strict prior dates, venue structure, hard failure, and same/future-outcome invariance. Original 70 tests remain passing.

Python/numpy/scipy versions: {"numpy": "2.5.3", "scipy": "1.18.1", "python": "3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]"}.

From /workspace/deepfc-shot-reconstruction:

```bash
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.joint_strength > experiments/results/joint_strength/results.json 2> experiments/results/joint_strength/run.log
PYTHONPATH=src:. /workspace/.venvs/deepfc/bin/python -m pytest -q
```

All nine source hashes are verified against the archived manifest. Source/spec hashes and every forecast-date convergence record are in results.json. Diagnostic code/design/results and proposal are preserved alongside this experiment. No raw CSVs enter Git.

No later-period tuning was performed. Failed gates reject this candidate; do not retune using these later results. Passing all gates would still mean research-only pending the proposed frozen prospective evaluation, not adoption or evidence of a profitable betting edge.
