# Fixed 180-day weighting improves retrospective Championship team-corner scores

Run September 30, 2026 UTC (September 29 in New York). Retain this candidate
for prospective comparison. Do not replace the production model from these
results alone. No parameter search or production changes were performed.

## Data and comparison

Downloaded Football-Data E1 seasons 2017/18 through 2025/26 directly from
`https://www.football-data.co.uk/mmz4281/{season}/E1.csv`, with season codes
`1718` through `2526`. Source-file hashes are in the accompanying
[machine-readable report](championship_comparison.json).

- 4,968 source rows; 4,967 matches with corner results.
- One missing corner result is excluded by the existing CSV loader.
- 2017/18 supplies warm-up history. The scoring period is August 3, 2018
  through May 2, 2026.
- 4,415 candidate fixtures after warm-up; 4,208 pass common history gates.
- All three models score exactly those 4,208 fixtures / 8,416 team observations.
- The 207 excluded fixtures lack the common minimum history. Their results
  remain available as history for later predictions.
- Every baseline prediction was compared with Zeno's actual forecast function.
  Largest absolute difference in means, dispersion or probabilities:
  `2.17e-15`, floating-point rounding only.

The comparison reuses the unchanged DeepFC model and pinned Zeno code. It
does not reproduce the precise history-file selection or availability of a
particular deployed VPS. Both research variants receive the same nine-season
history, and freshness/operational failures are outside this benchmark.

## Overall results

Lower is better for every metric below.

| Model | Mean Brier | Count NLL | MAE |
| --- | ---: | ---: | ---: |
| Current DeepFC | 0.215789 | 2.355377 | 2.116355 |
| Current Zeno | 0.216489 | 2.359650 | 2.127341 |
| Zeno with fixed 180-day weighting | **0.214115** | **2.351056** | **2.101475** |

The decay model reduces mean Brier by 0.002374 relative to Zeno and 0.001674
relative to DeepFC. These are probability-score improvements, not percentage
point gains in prediction accuracy or estimates of betting returns.

## Consistency

| Scoring slice | DeepFC | Zeno | Zeno with decay |
| --- | ---: | ---: | ---: |
| Home teams | 0.218899 | 0.219207 | **0.217677** |
| Away teams | 0.212679 | 0.213770 | **0.210553** |
| Line 3.5 | 0.206168 | 0.206882 | **0.204731** |
| Line 4.5 | 0.238287 | 0.238790 | **0.236747** |
| Line 5.5 | 0.228075 | 0.228682 | **0.225754** |
| Line 6.5 | 0.190626 | 0.191601 | **0.189228** |

These are mean Brier scores. Under and over have the same score at half-lines
because both the probabilities and outcomes are complements.

| Season | DeepFC | Zeno | Zeno with decay |
| --- | ---: | ---: | ---: |
| 2018/19 | **0.218855** | 0.222075 | 0.219058 |
| 2019/20 | 0.218096 | 0.218683 | **0.215633** |
| 2020/21 | **0.218935** | 0.220971 | 0.219014 |
| 2021/22 | **0.214489** | 0.214738 | 0.215521 |
| 2022/23 | 0.218065 | 0.219335 | **0.216641** |
| 2023/24 | 0.216428 | 0.216419 | **0.210451** |
| 2024/25 | 0.206844 | 0.205355 | **0.203762** |
| 2025/26 | 0.214941 | 0.214878 | **0.213277** |

Decay wins seven of eight seasons against Zeno and five of eight against
DeepFC. It does not win universally. 2023/24 contributes the largest gain.

## Uncertainty and calibration

Paired 28-day block bootstrap: 2,000 resamples, seed 7, 87 occupied blocks.
Differences are challenger minus baseline; negative favors the challenger.

| Comparison | Brier difference, 95% interval | Count NLL difference, 95% interval |
| --- | --- | --- |
| Decay minus Zeno | [-0.003435, -0.001352] | [-0.012455, -0.004705] |
| Decay minus DeepFC | [-0.002888, -0.000467] | [-0.008955, +0.000387] |
| DeepFC minus Zeno | [-0.001506, +0.000138] | [-0.007381, -0.001059] |

The decay model's Brier interval is below zero against both baselines.
Its count-NLL advantage over DeepFC is less certain: that interval includes
zero. A bootstrap win fraction is not the probability the model is truly better.

Better Brier does not imply perfect calibration. At line 3.5, the decay
model's average over probability is 68.00%, while the observed rate is 69.11%.
The JSON contains fixed-bin calibration, line rates, MAE/RMSE and count NLL
for every venue and season, including empty bins.

These seasons have been inspected during earlier research, and the 180-day
choice came from a prior experiment. This result is retrospective evidence,
not an untouched test. The intervals do not account for that model-selection
history, source revisions, or every form of time dependence. Do not quote
8,416 team observations or four lines per team as independent matches.

## Decision

The candidate meets the predeclared screen for a prospective trial: lower
aggregate Brier with an interval below zero, lower aggregate count NLL,
improvement in both venues and a majority of seasons. Keep its parameters
fixed. The next implementation decision is how to record it alongside the
existing model before kickoff using the same captured inputs and full
version provenance. This PR implements only the research comparison.

There are no verified historical corner prices in this dataset, so this
report makes no ROI, market-beating, or opportunity-selection claim.
