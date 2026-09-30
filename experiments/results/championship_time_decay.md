# Championship time-decay result

Run on September 30, 2026 UTC using Football-Data E1 seasons 2017/18 through
2025/26. The 2017/18 season supplies warm-up history. All three models scored
the same 4,208 fixtures, or 8,416 team observations.

Lower is better:

| Model | Mean Brier | Count NLL | MAE |
| --- | ---: | ---: | ---: |
| Current DeepFC | 0.215789 | 2.355377 | 2.116355 |
| Equal-weight venue/opponent | 0.216489 | 2.359650 | 2.127341 |
| Fixed 180-day weighting | **0.214115** | **2.351056** | **2.101475** |

The time-weighted model improved Brier score for home and away predictions,
at lines 3.5, 4.5, 5.5 and 6.5, and in seven of eight seasons versus its direct
equal-weight baseline. It beat current DeepFC in five of eight seasons.

A paired 28-day block bootstrap used 2,000 samples with seed 7:

| Comparison | Brier difference, 95% interval |
| --- | ---: |
| Time weighted minus equal weight | [-0.003435, -0.001352] |
| Time weighted minus current DeepFC | [-0.002888, -0.000467] |

Negative differences favor time weighting. The intervals preserve predictions
from nearby dates in blocks, but they do not account for every form of time
dependence or the earlier selection of the 180-day setting.

This is retrospective evidence from seasons already inspected during model
development. It justifies testing the fixed candidate on future fixtures. It
does not prove a sportsbook edge, profitability or future improvement.
