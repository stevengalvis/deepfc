# Normalized pre-closing 1X2 strength: completed frozen test

**Reject promotion under frozen gates.** Material historical improvement in aggregate Brier/NLL/MAE, but BOTH extreme-bias gates fail. Retain fixed180 and leave Zeno unchanged. Do not relabel this as an all-gates pass or retune to repair the failures.

One coefficient beta=0.113765840001, fitted to 4224 earlier team observations; latest training date 2023-05-08. Candidate evaluation starts 2023-07-01. No coefficient updates or variant search. Scalar score residual 2.55e-13; curvature 879.415106; converged in 6 Brent iterations.

## Main results

| Period | Model | n | Brier | Count NLL | MAE |
| --- | --- | ---: | ---: | ---: | ---: |
| validation | baseline | 1048 | 0.210451 | 2.406443 | 2.200642 |
| validation | candidate | 1048 | 0.209428 | 2.401594 | 2.196174 |
| validation | retained main, context | 1048 | 0.216428 | 2.425427 | 2.244784 |
| test | baseline | 2150 | 0.208559 | 2.354073 | 2.120767 |
| test | candidate | 2150 | 0.206683 | 2.348750 | 2.111618 |
| test | retained main, context | 2150 | 0.210927 | 2.358525 | 2.130975 |
| combined_later | baseline | 3198 | 0.209179 | 2.371235 | 2.146942 |
| combined_later | candidate | 3198 | 0.207583 | 2.366067 | 2.139327 |
| combined_later | retained main, context | 3198 | 0.212730 | 2.380449 | 2.168271 |

Fixed180 validation and test checkpoints reproduce previous verified runs. Retained main is a different model, shown only as context. Earlier coefficient-fit data are not presented as out-of-sample candidate forecasts.

## Paired uncertainty

Candidate minus fixed180; paired28-day blocks,2000 draws,seed7. Pointwise intervals, no multiplicity adjustment.

| Period | Metric | Delta | Lower95 | Upper95 |
| --- | --- | ---: | ---: | ---: |
| validation | mean_brier_score | -0.001023 | -0.001808 | -0.000276 |
| validation | negative_binomial_negative_log_loss | -0.004849 | -0.009073 | -0.000948 |
| validation | mae | -0.004469 | -0.013712 | +0.004409 |
| test | mean_brier_score | -0.001876 | -0.002534 | -0.001253 |
| test | negative_binomial_negative_log_loss | -0.005323 | -0.007851 | -0.002957 |
| test | mae | -0.009149 | -0.018160 | -0.000507 |
| combined_later | mean_brier_score | -0.001596 | -0.002110 | -0.001089 |
| combined_later | negative_binomial_negative_log_loss | -0.005168 | -0.007337 | -0.002910 |
| combined_later | mae | -0.007615 | -0.014216 | -0.001168 |

## All frozen gates

| Gate | Combined later2023/24–2025/26 | Test2024/25–2025/26 |
| --- | --- | --- |
| brier_material_improvement | PASS | PASS |
| brier_interval_below_zero | PASS | PASS |
| each_later_season_improves | PASS | PASS |
| nll_not_worse | PASS | PASS |
| nll_upper_bound | PASS | PASS |
| venue_guardrail | PASS | PASS |
| halve_bias_lt4 | FAIL | FAIL |
| halve_bias_ge6 | FAIL | FAIL |

Failed gates: halve absolute bias in baseline-defined <4 and >=6 bands. Combined-later low-band bias moves +0.018769 -> +0.137778 (limit0.009384); high-band bias moves -0.288884 -> -0.479872 (absolute limit0.144442). The low-band baseline bias was already near zero; that makes its frozen gate stringent, not a reason to change it. High-band count NLL and MAE also worsen. Overall and both-venue Brier gains do not override these failures.

## Season, venue and fixed-band slices

| Slice | n | Baseline Brier | Candidate Brier | NLL delta | MAE delta | Baseline bias | Candidate bias |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| season/2023 | 1048 | 0.210451 | 0.209428 | -0.004849 | -0.004469 | +0.027966 | +0.002577 |
| season/2024 | 1066 | 0.203762 | 0.202052 | -0.005137 | +0.000528 | -0.192771 | -0.219076 |
| season/2025 | 1084 | 0.213277 | 0.211238 | -0.005507 | -0.018666 | +0.045672 | +0.025131 |
| validation/venue/home | 524 | 0.214808 | 0.214096 | -0.003418 | +0.007400 | +0.057183 | -0.042651 |
| validation/venue/away | 524 | 0.206094 | 0.204761 | -0.006279 | -0.016338 | -0.001251 | +0.047805 |
| validation/band/lt4 | 122 | 0.168570 | 0.166947 | -0.008607 | -0.010415 | -0.064905 | +0.056472 |
| validation/band/4to6 | 672 | 0.218617 | 0.216877 | -0.008000 | -0.019729 | +0.193251 | +0.205641 |
| validation/band/ge6 | 254 | 0.208964 | 0.210128 | +0.005292 | +0.038761 | -0.364716 | -0.560552 |
| test/venue/home | 1075 | 0.214933 | 0.212873 | -0.005414 | -0.001442 | -0.070861 | -0.170938 |
| test/venue/away | 1075 | 0.202186 | 0.200494 | -0.005233 | -0.016856 | -0.074242 | -0.020963 |
| test/band/lt4 | 247 | 0.171671 | 0.170444 | -0.003779 | -0.011639 | +0.060097 | +0.177938 |
| test/band/4to6 | 1440 | 0.216172 | 0.213889 | -0.007583 | -0.019189 | -0.039124 | -0.033720 |
| test/band/ge6 | 463 | 0.204562 | 0.203608 | +0.000882 | +0.023404 | -0.247283 | -0.435611 |
| combined_later/venue/home | 1599 | 0.214892 | 0.213274 | -0.004760 | +0.001456 | -0.028901 | -0.128898 |
| combined_later/venue/away | 1599 | 0.203467 | 0.201892 | -0.005576 | -0.016686 | -0.050322 | +0.001573 |
| combined_later/band/lt4 | 369 | 0.170646 | 0.169287 | -0.005375 | -0.011234 | +0.018769 | +0.137778 |
| combined_later/band/4to6 | 2112 | 0.216950 | 0.214839 | -0.007716 | -0.019361 | +0.034814 | +0.042441 |
| combined_later/band/ge6 | 717 | 0.206121 | 0.205918 | +0.002444 | +0.028844 | -0.288884 | -0.479872 |

All bands use baseline means; membership never moves with candidate predictions. Full slice metric and bias intervals are in results.json. Seasonal Brier improves consistently, but 2024/25 MAE and combined home MAE slightly worsen.

## Line checks

| Period | Line | Baseline Brier | Candidate Brier |
| --- | ---: | ---: | ---: |
| validation | 3.5 | 0.189090 | 0.187572 |
| validation | 4.5 | 0.230693 | 0.229958 |
| validation | 5.5 | 0.227270 | 0.225966 |
| validation | 6.5 | 0.194752 | 0.194218 |
| test | 3.5 | 0.203485 | 0.201683 |
| test | 4.5 | 0.229172 | 0.226796 |
| test | 5.5 | 0.218695 | 0.216675 |
| test | 6.5 | 0.182885 | 0.181580 |
| combined_later | 3.5 | 0.198768 | 0.197059 |
| combined_later | 4.5 | 0.229670 | 0.227832 |
| combined_later | 5.5 | 0.221505 | 0.219720 |
| combined_later | 6.5 | 0.186774 | 0.185722 |

## Materiality versus shots

Test-period Brier gain is0.001876 (about0.90% relative), versus0.000786 for the prior reconstructed shot feature on the same test cohort, approximately2.39times as large. The earlier unavailable original shot implementation was reported in chat as0.000513 improvement; this odds gain is approximately3.66times that reported value. These are descriptive comparisons of already-inspected periods, not a new paired odds-versus-shots test. No shots model was rerun.

## Data and timing limits

Exact archived nine-file hashes reverified. AvgH/D/A usable on all3864 fixtures from2019/20 onward; no invalid triplets excluded. Same3198 later team observations for both models. Historical corner warm-up retains earlier completed fixtures. No BbAv splice, bookmaker substitution, closing fallback, goal-total or handicap feature. Price normalization removes sum-of-inverse-odds overround mechanically; it does not establish perfectly fair probabilities.

Football-Data pre-closing snapshots lack per-quote timestamps. The model uses current-match prices as historical covariates, not a verified kickoff−60-minute information set. Provider/bookmaker mix and quote timing can drift across seasons. All later seasons were previously inspected and confidence intervals omit much research-selection uncertainty. This supports historical association/predictive value, not a pristine holdout, fixed-time deployability or a profitable betting edge. Zeno source/timestamp parity remains unverified.

## Reproduce

From /workspace/deepfc-shot-reconstruction:

```bash
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.market_strength > experiments/results/market_strength/results.json
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m pytest -q
```

91 tests passed in0.61s (80 inherited,11 added). Added checks cover normalization, invalid-price rejection/no closing fallback, analytic score/curvature vs independent NB likelihood, future-outcome exclusion from coefficient fitting, training-date inference guard, neutral feature/fit, symmetric venue adjustment and loader rules. Specification and code hashes were frozen before evaluation and are embedded in results.json; dependency versions and numerical certificate included.

## Decision and next step

Keep this result as research evidence but reject promotion under the agreed gates. Do not tune the feature or relax the extreme-band criteria after these results. If further work is selected, first resolve live-input timestamp/source parity with an existing Zeno payload and define a new prospectively frozen decision contract. No such work was executed. Production, retained main, Zeno and its existing challenger remain unchanged; no subscriptions, publication, merge or deployment.
