# Championship probability-calibration result

Run on October 1, 2026 using Football-Data E1 seasons 2017/18 through 2025/26.
**Decision: reject the calibration layer and retain the raw 180-day probabilities.**

## Question and design

The fixed 180-day model converts expected corners into over probabilities with
its Negative Binomial distribution. This experiment asks whether a simple
line-specific logistic correction makes those probabilities more reliable.

Fit one intercept and log-odds slope for each half-line (3.5, 4.5, 5.5 and 6.5)
using predictions before 2023/24. Freeze those four mappings, then score them on
2023/24 validation and 2024/25–2025/26 retrospective test data. No expected
corner count, dispersion estimate, eligibility rule or fixture cohort changes.

The fitted slopes ranged from 0.729 to 0.793, indicating that the earlier sample
favored less extreme probabilities. That relationship did not transfer to later
seasons.

## Results

Lower is better.

| Period and model | Team observations | Brier | Binary NLL | 10-bin ECE |
| --- | ---: | ---: | ---: | ---: |
| 2023/24 raw | 1,048 | **0.210451** | **0.607671** | **0.017887** |
| 2023/24 calibrated | 1,048 | 0.210992 | 0.609254 | 0.020696 |
| 2024/25–2025/26 raw | 2,150 | **0.208559** | **0.604495** | **0.015842** |
| 2024/25–2025/26 calibrated | 2,150 | 0.209295 | 0.606362 | 0.019626 |

Calibrated-minus-raw paired 28-day block-bootstrap intervals (2,000 draws,
seed 7):

- 2023/24 Brier: +0.000541, 95% interval [-0.000435, +0.001478].
- 2023/24 binary NLL: +0.001584, 95% interval [-0.000695, +0.003815].
- 2024/25–2025/26 Brier: +0.000735, 95% interval [-0.000038, +0.001598].
- 2024/25–2025/26 binary NLL: +0.001867, 95% interval [+0.000078, +0.003864].

The calibration layer worsened Brier and binary NLL at every evaluated line in
the two-season test. It also worsened both metrics in each test season and for
home and away predictions. The test-period binary-NLL interval is entirely
above zero, favoring the raw probabilities.

Count NLL and MAE are unchanged because calibration alters market probabilities
only. At these half-lines, Under is the complement of Over and has the same
Brier score. The later seasons had been inspected in earlier research, so this
remains chronological retrospective evidence rather than a pristine holdout.

No historical sportsbook prices are available, so this experiment makes no
ROI, profitability, closing-line-value or betting-edge claim. No retained
DeepFC model or Zeno candidate changes.

## Reproduce

```bash
python -m experiments.probability_calibration \
  data/E1_1718.csv data/E1_1819.csv data/E1_1920.csv \
  data/E1_2021.csv data/E1_2122.csv data/E1_2223.csv \
  data/E1_2324.csv data/E1_2425.csv data/E1_2526.csv
```

JSON stdout includes fitted coefficients, per-line metrics, season and venue
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
