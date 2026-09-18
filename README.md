# DeepFC

DeepFC is a focused, public experiment in predicting full-match total corners
in the EFL Championship.

V1 deliberately answers one question: how well does a simple, chronological
baseline estimate full-match corner totals and over/under probabilities at
8.5, 9.5, 10.5, and 11.5 corners?

## Current model

The baseline uses the expanding mean of all earlier Championship matches as
the expected corner total. It converts that expectation into probabilities
with a Poisson distribution.

Evaluation is walk-forward. Matches played on the same date cannot influence
one another, preventing same-day data leakage. The 2017-18 season is intended
as warm-up history, with scoring beginning on July 1, 2018 by default.

Metrics include:

- mean absolute error;
- root mean squared error;
- Poisson negative log loss;
- Brier score for each supported line;
- predicted probabilities and actual hit rates;
- input row-quality counts.

This is a baseline, not evidence of profitable predictions. DeepFC does not
calculate picks, expected value, return on investment, or betting performance
without verified historical market prices.

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
| Poisson negative log loss | 2.634 |

| Line | Brier score | Predicted over | Actual over |
| --- | ---: | ---: | ---: |
| 8.5 | 0.2211 | 69.14% | 67.11% |
| 9.5 | 0.2482 | 56.93% | 54.88% |
| 10.5 | 0.2458 | 44.46% | 43.60% |
| 11.5 | 0.2228 | 32.87% | 33.52% |

One fixture was excluded because the source contains no corner result:
Bolton vs Brentford on April 27, 2019. No malformed completed rows were found.

The aggregate predicted total is close to the actual average, but an MAE of
2.714 corners leaves substantial match-level error. This result is the
no-team-strength benchmark that future models must beat on the same evaluation
window.

## Structure

```text
src/deepfc/
├── match_data.py          # canonical source-independent Match record
├── football_data_csv.py   # Football-Data CSV adapter
└── total_corners.py       # baseline, probabilities, evaluation, and CLI
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
```

The command prints a short human-readable summary followed by the complete
JSON-serializable evaluation result.

## Scope

DeepFC currently supports only:

- EFL Championship historical data;
- completed full-match corner counts;
- full-match total-corners evaluation.

There is no frontend, API, database, LLM, live fixture provider, team-corner
model, first-half model, or multi-league framework. Those should be added only
after the baseline demonstrates a justified next step.
