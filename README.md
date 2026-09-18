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
python -m deepfc.total_corners E1_1718.csv E1_1819.csv E1_1920.csv
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
