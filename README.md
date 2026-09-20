# DeepFC

DeepFC is a focused, public experiment in predicting full-match corner markets
in the EFL Championship.

V1 evaluates full-match totals and individual team totals using chronological
predictions made only from earlier matches.

## Full-match baseline

The baseline uses the expanding mean of all earlier Championship matches as
the expected corner total. It converts that expectation into probabilities
with a Negative Binomial distribution. The distribution's dispersion is also
estimated from earlier matches because observed corner totals vary more than a
Poisson distribution allows.

Evaluation is walk-forward. Matches played on the same date cannot influence
one another, preventing same-day data leakage. The 2017-18 season is intended
as warm-up history, with scoring beginning on July 1, 2018 by default.

Metrics include:

- mean absolute error;
- root mean squared error;
- Negative Binomial negative log loss;
- Brier score for each supported line;
- predicted probabilities and actual hit rates;
- input row-quality counts.

This is a baseline, not evidence of profitable predictions. DeepFC does not
calculate picks, expected value, return on investment, or betting performance
without verified historical market prices.

## Team-corner model

The team-corner comparison produces two predictions for every fixture: one
for the home team and one for the away team. Its baseline uses the historical
Championship home or away average. The challenger combines:

- the team's smoothed corners won in the same venue role; and
- the opponent's smoothed corners allowed in the opposite venue role.

Each history starts with a five-match prior at the corresponding league
average. This prevents one or two early observations from producing extreme
estimates. The expected count is the average of the team's attacking history
and the opponent's defensive history.

On the same 2017-18 through 2025-26 dataset, the challenger improved every
reported aggregate metric:

| Metric | Venue-average baseline | Team + opponent | Difference |
| --- | ---: | ---: | ---: |
| Mean absolute error | 2.1701 | 2.1258 | -0.0444 |
| Root mean squared error | 2.7323 | 2.6864 | -0.0459 |
| Negative Binomial negative log loss | 2.3757 | 2.3591 | -0.0166 |
| Mean Brier score | 0.2203 | 0.2158 | -0.0045 |

The direction of the improvement remained the same with smoothing priors of
2, 5, and 10 matches. In 2,000 paired fixture bootstrap samples, the
challenger beat the baseline in every sample for both MAE and mean Brier
score. The 95% bootstrap intervals for challenger-minus-baseline were
`[-0.0524, -0.0365]` for MAE and `[-0.0054, -0.0036]` for mean Brier score.

These results justify retaining the model, but they do not demonstrate an
edge against sportsbook prices.

## Real-data baseline

The first benchmark was run on September 18, 2026 using the EFL Championship
CSV files published in the
[Football-Data England archive](https://www.football-data.co.uk/englandm.php).
It covers 2017-18 through 2025-26. The 2017-18 season supplies warm-up history,
and evaluation begins on July 1, 2018.

| Evaluation result | Value |
| --- | ---: |
| Rows read | 4,968 |
| Completed matches loaded | 4,967 |
| Evaluated matches | 4,415 |
| Mean predicted total | 10.221 |
| Mean actual total | 10.170 |
| Mean absolute error | 2.714 |
| Root mean squared error | 3.388 |
| Negative Binomial negative log loss | 2.630 |

| Line | Brier score | Predicted over | Actual over |
| --- | ---: | ---: | ---: |
| 8.5 | 0.2208 | 67.70% | 67.11% |
| 9.5 | 0.2479 | 56.04% | 54.88% |
| 10.5 | 0.2458 | 44.28% | 43.60% |
| 11.5 | 0.2227 | 33.39% | 33.52% |

One fixture was excluded because the source contains no corner result:
Bolton vs Brentford on April 27, 2019. No malformed completed rows were found.

The aggregate predicted total is close to the actual average, but an MAE of
2.714 corners leaves substantial match-level error. Negative Binomial
probabilities modestly improved mean Brier score from 0.234465 to 0.234303 and
count negative log loss from 2.633579 to 2.629960 compared with Poisson on the
same fixtures. This result remains the no-team-strength benchmark that future
models must beat on the same evaluation window.

## Structure

```text
src/deepfc/
├── match_data.py          # canonical source-independent Match record
├── football_data_csv.py   # Football-Data CSV adapter
├── corner_distribution.py # shared count probabilities and loss functions
├── total_corners.py       # full-match total model and evaluation
└── team_corners.py        # team-total models, evaluation, and robustness
```

Raw Football-Data columns such as `HC` and `AC` are translated immediately to
`home_corners` and `away_corners`. Models consume canonical `Match` records and
do not depend on CSV column names.

## Run locally

```bash
python -m pip install -e ".[test]"
pytest
python -m deepfc.total_corners \
  data/E1_1718.csv \
  data/E1_1819.csv \
  data/E1_1920.csv \
  data/E1_2021.csv \
  data/E1_2122.csv \
  data/E1_2223.csv \
  data/E1_2324.csv \
  data/E1_2425.csv \
  data/E1_2526.csv

python -m deepfc.team_corners \
  data/E1_1718.csv \
  data/E1_1819.csv \
  data/E1_1920.csv \
  data/E1_2021.csv \
  data/E1_2122.csv \
  data/E1_2223.csv \
  data/E1_2324.csv \
  data/E1_2425.csv \
  data/E1_2526.csv
```

The command prints a short human-readable summary followed by the complete
JSON-serializable evaluation result.

## Scope

DeepFC currently supports only:

- EFL Championship historical data;
- completed full-match corner counts;
- full-match total-corners evaluation;
- individual full-match team-corner evaluation.

There is no frontend, API, database, LLM, live fixture provider, team-corner
production service, first-half model, or multi-league framework. Those should
be added only after evaluation demonstrates a justified next step.
