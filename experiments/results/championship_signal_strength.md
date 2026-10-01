# Championship attack/concession signal-strength result

Run on October 1, 2026 using Football-Data E1 seasons 2017/18 through 2025/26.
**Decision: retain full-strength attack and concession effects.**

## Question and fixed design

The fixed 180-day model estimates expected corners as:

```text
league rate × (team attack / league rate)^attack strength
            × (opponent concessions / league rate)^concession strength
```

The retained model sets both strengths to 1.0. This experiment tests the
predeclared grid `{0.5, 0.75, 1.0}` for each signal, excluding the baseline pair.
Lower values damp a signal toward the venue-specific league rate.

All settings use identical fixtures, 180-day weighting, five-match smoothing,
eligibility rules and pooled all-history dispersion. Select one alternative by
mean Brier before 2023/24. Freeze that pair, then evaluate 2023/24 and
2024/25–2025/26. Those seasons were inspected in earlier research, so this is a
chronological retrospective split rather than a pristine holdout.

## Earlier-season selection

Lower is better. Each row contains 5,218 team observations.

| Attack | Concessions | Mean Brier | Count NLL | MAE |
| ---: | ---: | ---: | ---: | ---: |
| 0.50 | 0.50 | 0.216665 | 2.335058 | 2.066116 |
| 0.50 | 0.75 | 0.216783 | 2.335858 | 2.067546 |
| 0.50 | 1.00 | 0.217408 | 2.338662 | 2.074327 |
| **0.75** | **0.50** | **0.216261** | **2.333848** | **2.063014** |
| 0.75 | 0.75 | 0.216355 | 2.334594 | 2.064744 |
| 0.75 | 1.00 | 0.216949 | 2.337343 | 2.071057 |
| 1.00 | 0.50 | 0.216516 | 2.335300 | 2.065694 |
| 1.00 | 0.75 | 0.216581 | 2.335993 | 2.067611 |
| Baseline 1.00 | 1.00 | 0.217140 | 2.338689 | 2.073609 |

Attack 0.75 and concessions 0.50 is the frozen candidate. It is not replaced
after later results are inspected.

## Later-season evaluation

| Period and model | Team observations | Mean Brier | Count NLL | MAE |
| --- | ---: | ---: | ---: | ---: |
| 2023/24 baseline | 1,048 | **0.210451** | **2.406443** | **2.200642** |
| 2023/24 candidate | 1,048 | 0.212300 | 2.411431 | 2.210147 |
| 2024/25–2025/26 baseline | 2,150 | **0.208559** | **2.354073** | 2.120767 |
| 2024/25–2025/26 candidate | 2,150 | 0.209511 | 2.355018 | **2.118837** |

Candidate-minus-baseline paired 28-day block-bootstrap intervals (2,000 draws,
seed 7):

- 2023/24 Brier: +0.001849, 95% interval [+0.000858, +0.002864].
- 2023/24 count NLL: +0.004988, 95% interval [+0.001235, +0.008540].
- 2023/24 MAE: +0.009505, 95% interval [-0.001680, +0.021222].
- 2024/25–2025/26 Brier: +0.000952, 95% interval [-0.000082, +0.002095].
- 2024/25–2025/26 count NLL: +0.000945, 95% interval [-0.002679, +0.005089].
- 2024/25–2025/26 MAE: -0.001930, 95% interval [-0.014189, +0.011534].

The selected candidate worsens Brier at all four lines in validation and test,
both test seasons, and both venues. Its 2023/24 Brier and count-NLL intervals
are entirely above zero. The tiny two-season MAE improvement is uncertain and
does not compensate for worse market probabilities.

No historical sportsbook prices are available, so this experiment makes no
ROI, profitability, closing-line-value or betting-edge claim. No retained
DeepFC model or Zeno candidate changes.

## Reproduce

```bash
python -m experiments.signal_strength \
  data/E1_1718.csv data/E1_1819.csv data/E1_1920.csv \
  data/E1_2021.csv data/E1_2122.csv data/E1_2223.csv \
  data/E1_2324.csv data/E1_2425.csv data/E1_2526.csv
```

JSON stdout includes the full tuning grid, per-line results, season and venue
breakdowns, uncertainty intervals, data-quality counts and source hashes. Raw
CSVs remain outside Git.

| File | SHA-256 |
| --- | --- |
| E1_1718.csv | `04d07d578d818bdcd6b95d43e79f10a6a26be01b45be6190b09ebdeaeba0a7ce` |
| E1_1819.csv | `112eedf787e26e00aac1442ef86e7fee5d4a43f86552ff2dac31ceb95a849487` |
| E1_1920.csv | `f31450c623c0b74b89692584a85924cc652d33ec89757acf4b2dda5e26261d57` |
| E1_2021.csv | `cf93295e310c60e5b97ae7466d772f8ec6a908ad401e38fceb7e8617369d5073` |
| E1_2122.csv | `a181451be4801b9f838daf5f6aaf21e9f09d36042be9e6c15388e71001e772ea` |
| E1_2223.csv | `cd38ab0586ea8cb4d573c363ff70749117f116da5b2741e5b0ea37da05860b1b` |
| E1_2324.csv | `5737f6cc95c95092b28317f41d3123e2fb09345434efc1c84bbdf15830849ab3` |
| E1_2425.csv | `f34c340446c916374be66bdc2fb25b87ee7f2662712ca009653d03ac705535f9` |
| E1_2526.csv | `98954c319950f19158624b17a154ef1c56eb7b8d169ef317f28f06d11d0b9a74` |
