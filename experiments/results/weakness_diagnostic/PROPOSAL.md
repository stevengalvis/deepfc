# One proposed next experiment: jointly estimate opponent-adjusted corner strength

Status: diagnostic only; no candidate implemented, fitted, or evaluated. Reconstruction preserved in local commit b9a6fe97bbfddcbc30972111f457c91e1f01d616. No raw datasets or credentials staged; src/, production and Zeno unchanged.

## Recommendation and hypothesis

Test one joint venue-specific attack/defence count model against fixed180: estimate team attack and opponent concession effects together from historical fixtures, rather than multiply two separately averaged marginal rates. Hypothesis: explicitly accounting for which opponents generated each rate improves extreme expected counts and tail forecasts. The present diagnostic demonstrates miscalibration at extremes; it does NOT demonstrate that schedule confounding causes it. This proposed experiment would test that explanation and can be rejected.

## Evidence

On identical 4208 fixtures (8416 team observations), fixed180 Brier is 0.214115 versus retained DeepFC 0.215789; paired difference interval [-0.002888,-0.000467]. Overall mean bias is small, masking conditional errors.

| Fixed180 mean band | n | Predicted | Observed | Actual minus predicted | Pointwise 95% interval |
| --- | ---: | ---: | ---: | ---: | --- |
| mean/lt4 | 894 | 3.691 | 3.985 | +0.295 | [0.123, 0.462] |
| mean/4to6 | 6053 | 4.968 | 4.950 | -0.018 | [-0.089, 0.053] |
| mean/ge6 | 1469 | 6.584 | 6.294 | -0.290 | [-0.424, -0.142] |

Below four, <=1-corner probability is 15.8% versus 11.5% observed. At six-plus, >=10-corner probability is 17.7% versus 14.2% observed. Their calibration-error intervals exclude zero pointwise. Fixed180 still beats retained DeepFC in both extreme bands: this is a targeted improvement opportunity, not a reason to revert or blend models. Bands were defined by fixed180 forecasts for both models.

Entrant/early-season cuts were also examined, but are smaller and noisier; entry combines promotion and relegation and cannot identify either mechanism. The common eligibility cohort excludes many truly cold-start fixtures. No claim about those omitted fixtures can be made from this analysis.

## All predefined cuts

| Cut | n | Fixed bias | Bias 95% interval | Fixed minus retained Brier |
| --- | ---: | ---: | --- | ---: |
| all | 8416 | -0.032 | [-0.093, 0.031] | -0.001674 |
| season/2018 | 994 | +0.008 | [-0.209, 0.254] | +0.000203 |
| venue/home | 4208 | -0.029 | [-0.124, 0.069] | -0.001222 |
| mean/ge6 | 1469 | -0.290 | [-0.424, -0.142] | -0.003457 |
| phase/first10 | 1508 | +0.010 | [-0.123, 0.135] | +0.000349 |
| membership/incumbent | 6454 | -0.056 | [-0.126, 0.017] | -0.002329 |
| transition/incumbent/first10 | 1272 | -0.047 | [-0.205, 0.107] | +0.000175 |
| venue/away | 4208 | -0.036 | [-0.109, 0.041] | -0.002127 |
| mean/4to6 | 6053 | -0.018 | [-0.089, 0.053] | -0.000592 |
| mean/lt4 | 894 | +0.295 | [0.123, 0.462] | -0.006069 |
| phase/later | 6908 | -0.041 | [-0.111, 0.030] | -0.002116 |
| transition/incumbent/later | 5182 | -0.059 | [-0.139, 0.031] | -0.002943 |
| membership/entrant | 1962 | +0.047 | [-0.058, 0.149] | +0.000479 |
| transition/entrant/later | 1726 | +0.010 | [-0.103, 0.121] | +0.000369 |
| season/2019 | 1046 | -0.024 | [-0.106, 0.065] | -0.002462 |
| transition/entrant/first10 | 236 | +0.319 | [0.016, 0.681] | +0.001289 |
| season/2020 | 1030 | -0.237 | [-0.335, -0.096] | +0.000080 |
| season/2021 | 1064 | +0.067 | [-0.092, 0.222] | +0.001032 |
| season/2022 | 1084 | +0.043 | [-0.078, 0.171] | -0.001424 |
| season/2023 | 1048 | +0.028 | [-0.067, 0.129] | -0.005977 |
| season/2024 | 1066 | -0.193 | [-0.370, 0.024] | -0.003082 |
| season/2025 | 1084 | +0.046 | [-0.096, 0.187] | -0.001665 |

Full Brier/count-NLL/MAE, low/high tail rates, and paired uncertainty for both baselines are in results.json. Season labels come from source CSVs, including July 2020 in 2019/20; fixed chronological historical splits in prior work are not relabeled or rerun.

## Why this is not a repeat of rejected experiments

- Shrinkage tested prior counts 1/2/5/10/20; selected 10 worsened later Brier.
- Calibration fitted static line-wise logistic mappings; later Brier/NLL worsened.
- Dispersion tested venue/time weighting of marginal variance; later metrics worsened.
- Signal strength damped marginal attack/concession exponents; later Brier worsened.
All kept the marginal mean-estimation structure. Joint opponent-adjusted effects change that structure rather than choosing another half-life, exponent or calibration slope. Those failed experiments also warn against interpreting extreme-bin bias as proof that generic shrinkage or static calibration will help.

## Proposed frozen evaluation plan (requires selection before implementation)

1. One candidate only: log mean = venue intercept + team venue attack effect + opponent opposite-venue concession effect. Fit jointly by 180-day-weighted NB likelihood to dates strictly before prediction, with the baseline prior-history pooled dispersion held fixed. Zero-centered Gaussian team effects, fixed unit log-scale variance, and sum-to-zero constraints per effect family; no penalty grid or later-period tuning. Refit before each prediction date. Unseen effects are zero. These are proposed design choices, not empirically optimized settings.
2. Use the exact nine verified E1 files, dates, teams, venue and corner counts. No shots, prices or additional data are required for the initial comparison. Freeze the source hashes, model/objective, solver tolerances and convergence failure policy in the implementation specification before fitting. A fit failure is an explicit failed run, never a silent fixture exclusion.
3. Keep fixed180 eligibility and identical fixtures, 3.5/4.5/5.5/6.5 lines, pooled dispersion and all same-date exclusion rules. Fixed180 is primary comparator; retained DeepFC is secondary context. Use pre-2023/24 for development/debugging, 2023/24 validation and 2024/25–2025/26 retrospective confirmation, with no reselection. These periods are all inspected; none is an untouched holdout.
4. Primary endpoint: mean Brier. Secondary: count NLL, MAE, and bias in the unchanged baseline-defined <4 and >=6 bands. Report every season, venue, line and paired 28-day bootstrap intervals (2000 draws, seed7); no extra subgroup searches.
5. Proposed practical bar, a decision policy rather than a measured power result: at least 0.001 absolute Brier reduction in combined later periods, paired 95% upper bound below zero, and improvement in each later season. Reduce absolute bias in BOTH extreme bands by at least half; count-NLL point estimate must not worsen and its paired upper bound must be <=+0.005. No venue may worsen Brier by more than 0.001. Reject if these gates fail; do not retune to salvage it.
6. Even passing is research evidence only. Before promotion, freeze a prospective window of the next 1000 eligible fixtures, collect immutable timestamped pre-match predictions and later verified outcomes, and apply the same overall Brier/NLL gates without interim tuning. Assess power before starting; a wide interval means inconclusive, not a reason to move the finish line. Zeno remains unchanged.

## Limitations and reproducibility

This is exploratory evidence from many already-inspected seasons. Cuts were fixed before this diagnostic, but intervals are pointwise and not multiplicity-adjusted. Prediction-conditioned bins can expose estimation noise; they do not isolate a causal flaw. 28-day blocks preserve short-range pairing but not all team/season dependence. Entrant classification is only a membership proxy. No betting-edge or profitability claim follows.

Run from /workspace/deepfc-shot-reconstruction:

```bash
PYTHONPATH=src:. /workspace/.venvs/deepfc/bin/python -m experiments.weakness_diagnostic > experiments/results/weakness_diagnostic/results.json
PYTHONPATH=src:. /workspace/.venvs/deepfc/bin/python -m pytest -q
```

70 tests passed in 0.37s after preservation. Diagnostic post-run checks verify 8416 observations and complete disjoint partitions for every cut family. Design and source hashes are saved with results. No candidate run was made.
