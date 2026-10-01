# Championship dispersion result

Run on October 1, 2026 using Football-Data E1 seasons 2017/18 through 2025/26.
**Decision: retain pooled all-history dispersion.**

## Question and fixed design

The fixed 180-day model gives recent matches more weight when estimating each
team's expected corners. Its Negative Binomial dispersion is estimated from all
earlier home and away team-corner observations pooled together. This experiment
compares that baseline with:

- separate all-history home and away dispersion;
- pooled dispersion with 180-day exponential weights;
- separate home and away dispersion with 180-day exponential weights.

Every method scores the same fixtures with exactly the same expected-corner
means and actual counts. Only dispersion and the probabilities derived from it
change. Weighted sample variance uses the reliability-weight denominator
`sum(w) - sum(w²) / sum(w)`, which reduces to the ordinary `n - 1` denominator
when weights are equal.

Select one alternative by mean Brier before 2023/24. Freeze that choice, then
score 2023/24 validation and 2024/25–2025/26 retrospective test data. These
seasons were previously inspected, so the split is chronological retrospective
evidence rather than a pristine holdout.

## Earlier-season selection

Lower is better. All rows contain 5,218 team observations.

| Dispersion method | Mean Brier | Count NLL | MAE |
| --- | ---: | ---: | ---: |
| Pooled all history, baseline | 0.217140 | 2.338689 | 2.073609 |
| Venue-specific all history | 0.217159 | **2.338246** | 2.073609 |
| Pooled 180-day | **0.217125** | 2.339132 | 2.073609 |
| Venue-specific 180-day | 0.217150 | 2.338758 | 2.073609 |

Pooled 180-day dispersion wins the predeclared Brier selection among the three
alternatives, by 0.000015 versus the baseline. It becomes the frozen candidate.

## Later-season evaluation

| Period and method | Team observations | Mean Brier | Count NLL | MAE |
| --- | ---: | ---: | ---: | ---: |
| 2023/24 baseline | 1,048 | **0.210451** | **2.406443** | 2.200642 |
| 2023/24 pooled 180-day | 1,048 | 0.210551 | 2.407342 | 2.200642 |
| 2024/25–2025/26 baseline | 2,150 | **0.208559** | **2.354073** | 2.120767 |
| 2024/25–2025/26 pooled 180-day | 2,150 | 0.208602 | 2.357254 | 2.120767 |

Candidate-minus-baseline paired 28-day block-bootstrap intervals (2,000 draws,
seed 7):

- 2023/24 Brier: +0.000100, 95% interval [-0.000064, +0.000286].
- 2023/24 count NLL: +0.000899, 95% interval [-0.000602, +0.003110].
- 2024/25–2025/26 Brier: +0.000043, 95% interval [-0.000175, +0.000267].
- 2024/25–2025/26 count NLL: +0.003180, 95% interval [+0.001459, +0.004928].

The candidate's Brier point estimate is worse in validation, both test seasons,
and both venues. Its count NLL is worse in both test seasons and both venues.
The combined test-period count-NLL interval is entirely above zero, favoring the
current pooled all-history dispersion. MAE and RMSE are identical by design.

No historical sportsbook prices are available, so this experiment makes no
ROI, profitability, closing-line-value or betting-edge claim. No retained
DeepFC model or Zeno candidate changes.

## Reproduce

```bash
python -m experiments.dispersion \
  data/E1_1718.csv data/E1_1819.csv data/E1_1920.csv \
  data/E1_2021.csv data/E1_2122.csv data/E1_2223.csv \
  data/E1_2324.csv data/E1_2425.csv data/E1_2526.csv
```

JSON stdout includes full tuning metrics, per-line results, season and venue
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
