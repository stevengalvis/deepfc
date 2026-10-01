# Championship team-prior shrinkage result

Run on October 1, 2026 using Football-Data E1 seasons 2017/18 through 2025/26.
**Decision: retain the fixed 180-day model's five-match team prior.**

## Question and fixed design

The 180-day model already shrinks venue-specific attacking and opposing
concession rates toward the corresponding league rate. Test team priors of
1, 2, 5, 10 and 20 weighted matches, changing only that strength. League-rate
smoothing stays at five matches; half-life, history eligibility, multiplicative
formula, historical moment dispersion and scored lines 3.5/4.5/5.5/6.5 stay fixed.

The 2017/18 season supplies warm-up history. Select one prior using mean Brier
on 2018/19 through 2022/23, then inspect 2023/24 validation and 2024/25–2025/26
test results without changing the selection. These later seasons were already
inspected in previous model research: this is a chronological retrospective
split, not a pristine untouched holdout or prospective validation.

All settings score the same 4,208 eligible fixtures / 8,416 team observations.
Loaded 4,967 of 4,968 rows; one row has no corner results. All predictions precede
same-date history updates. The baseline reproduces the previous recorded
180-day experiment: Brier 0.214115, NLL 2.351056, MAE 2.101475.

## Earlier-season selection

Lower is better. Tuning contains 5,218 team observations.

| Team prior | Mean Brier | Count NLL | MAE |
| --- | ---: | ---: | ---: |
| 1 | 0.219571 | 2.350820 | 2.097586 |
| 2 | 0.218638 | 2.346079 | 2.087935 |
| 5 | 0.217140 | 2.338689 | 2.073609 |
| 10 | 0.216382 | 2.334794 | 2.066011 |
| 20 | 0.216498 | 2.334545 | 2.066063 |

Ten weighted matches wins on tuning Brier and is therefore the fixed candidate.
No other setting is substituted after inspecting later results.

## Later-season comparison

| Period | Team observations | Prior | Mean Brier | Count NLL | MAE |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2023/24 validation | 1048 | 5 | 0.210451 | 2.406443 | 2.200642 |
| 2023/24 validation | 1048 | 10 | 0.210890 | 2.407164 | 2.197955 |
| 2024/25–2025/26 test | 2150 | 5 | 0.208559 | 2.354073 | 2.120767 |
| 2024/25–2025/26 test | 2150 | 10 | 0.208776 | 2.352789 | 2.116695 |

Candidate-minus-baseline Brier differences using paired 28-day block bootstraps
(2,000 draws, seed 7):

- 2023/24: +0.000438; 95% interval [-0.000323, +0.001178].
- 2024/25–2025/26: +0.000217; 95% interval [-0.000329, +0.000853].

Brier point estimates are worse in both test seasons (+0.000364 in 2024/25,
+0.000072 in 2025/26). Test home predictions worsen by +0.000511; away
predictions improve by -0.000077. These intervals include zero and provide no
clear probability-quality benefit. Slight overall count-error improvements
are insufficient to retain the stronger prior.

Fixed ten-bin mean calibration error is 0.029860 vs 0.030824 in validation,
and 0.020571 vs 0.020310 in the two test seasons (baseline vs candidate).
Calibration diagnostics are noisy and bin-dependent, not the selection metric.
At the half-lines scored here, Under is the complement of Over and has the same
Brier score; this comparison does not omit a distinct Under Brier result.

No historical sportsbook prices are available for this experiment, so no ROI,
profitability, closing-line value or betting-edge claim is made. No production
model, Zeno shadow candidate or opportunity policy is changed.

## Reproduce

```bash
python -m experiments.shrinkage \
  data/E1_1718.csv data/E1_1819.csv data/E1_1920.csv \
  data/E1_2021.csv data/E1_2122.csv data/E1_2223.csv \
  data/E1_2324.csv data/E1_2425.csv data/E1_2526.csv
```

The JSON stdout includes per-line metrics, ten-bin calibration diagnostics,
per-venue and per-season comparisons, uncertainty intervals and source hashes.
The research helper accepts an optional team prior; omitted arguments preserve
its original behavior. Existing retained model code under `src/deepfc` is unchanged.

Source fingerprints (raw CSVs remain outside Git):

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
