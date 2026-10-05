# Championship shot-pressure result

Run on October 1, 2026 using Football-Data E1 seasons 2017/18 through 2025/26.
**Decision: INCONCLUSIVE. Do not promote to a Zeno shadow or retained model.**

## Question and design

The experiment asks whether prior shots and shots on target add information
beyond the fixed 180-day team-corner model. For each team prediction it uses:

- the team's venue-specific shots and shots on target;
- the opponent's opposite-venue shots and shots on target allowed;
- five-match smoothing toward the corresponding venue league rate; and
- the same 180-day time weighting as the corner model.

The four rate ratios are combined as one geometric shot-pressure signal. A
predeclared strength grid `{0.25, 0.50, 0.75, 1.00}` controls its influence on
the existing expected-corner count. Every input precedes the prediction date.

Strength is selected before 2023/24. The selected value is frozen for 2023/24
validation and a retrospective 2024/25–2025/26 test. The later seasons have
already been inspected in other DeepFC research, so this is not a pristine
holdout and cannot justify production replacement by itself.

## Data quality

- 4,968 rows read and 4,967 completed corner results loaded.
- Bolton–Brentford on April 27, 2019 is absent because the source row has no
  corner or shot results.
- Burnley–Swansea on November 10, 2024 remains an evaluation target, but its
  impossible `2 shots / 7 shots on target` home observation is quarantined and
  cannot enter later shot histories.

## Earlier-season selection

Lower is better. Each row contains 5,218 team observations.

| Shot strength | Mean Brier | Count NLL | MAE |
| ---: | ---: | ---: | ---: |
| Baseline 0.00 | **0.217140** | **2.338689** | **2.073609** |
| **0.25 selected** | 0.217152 | 2.339028 | 2.073742 |
| 0.50 | 0.217405 | 2.340376 | 2.076270 |
| 0.75 | 0.217888 | 2.342730 | 2.081216 |
| 1.00 | 0.218590 | 2.346088 | 2.088300 |

No shot-adjusted setting beat the baseline during selection. Strength 0.25 was
the least harmful predeclared challenger and was frozen without using later
results. This weak early evidence is why the result is not a retained-model
decision even though later performance is encouraging.

## Later-season evaluation

| Period and model | Observations | Mean Brier | Count NLL | MAE |
| --- | ---: | ---: | ---: | ---: |
| 2023/24 baseline | 1,048 | 0.210451 | 2.406443 | **2.200642** |
| 2023/24 shot challenger | 1,048 | **0.210277** | **2.405287** | 2.200780 |
| 2024/25–2025/26 baseline | 2,150 | 0.208559 | 2.354073 | 2.120767 |
| 2024/25–2025/26 shot challenger | 2,150 | **0.208046** | **2.352916** | **2.118482** |

The challenger-minus-baseline Brier difference was `-0.000174` in 2023/24 and
`-0.000513` in 2024/25–2025/26. On the final two seasons, its paired 28-day
block-bootstrap 95% interval was `[-0.000825, -0.000192]`, with 99.9% of draws
below zero.

The final-period Brier improvement appeared in both seasons and both venues.
It also improved all four evaluated lines from 3.5 through 6.5 when those two
seasons were pooled. The effect is small, and some season, venue, and metric
intervals still include zero.

## Decision

The shot feature improved later retrospective Brier and count NLL while
preserving a strict pre-match information boundary. However, no nonzero
strength beat the baseline during selection. The result is therefore
inconclusive rather than an approved challenger.

Do not promote it to Zeno shadow or production use because:

- no nonzero strength improved the earlier selection cohort;
- the later seasons are retrospective and previously inspected;
- the absolute improvement is small; and
- no historical market prices support an edge or profitability claim.

The implementation and recorded metrics remain useful as a reproducible
research artifact. Any future reconsideration requires a new, predeclared
prospective evaluation rather than another search over these seasons.

## Reproduce

```bash
python -m experiments.shot_pressure \
  data/E1_1718.csv data/E1_1819.csv data/E1_1920.csv \
  data/E1_2021.csv data/E1_2122.csv data/E1_2223.csv \
  data/E1_2324.csv data/E1_2425.csv data/E1_2526.csv
```
