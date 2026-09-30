# Experiments

Experiments answer one model question without changing DeepFC's retained model.
Reusable code belongs in `src/deepfc/` only after the evidence supports keeping it.

## Championship time decay

[`time_decay.py`](time_decay.py) asks whether full-match Championship team-corner
predictions improve when older matches gradually receive less weight.

The comparison is intentionally narrow:

- current DeepFC team/opponent model;
- the equal-weight venue-attack × opponent-concession formula used as the
  decay model's direct baseline;
- the same formula with a fixed 180-day half-life.

All models score the same eligible fixtures. Predictions use strictly earlier
dates. The 180-day setting was fixed before this comparison; the experiment
does not search for a better value.

Run it with the nine locally downloaded Championship files:

```bash
python -m experiments.time_decay \
  data/E1_1718.csv data/E1_1819.csv data/E1_1920.csv \
  data/E1_2021.csv data/E1_2122.csv data/E1_2223.csv \
  data/E1_2324.csv data/E1_2425.csv data/E1_2526.csv
```

The command prints the complete metrics as JSON. Raw data remains outside Git.
The concise recorded result and its limitations are in
[`results/championship_time_decay.md`](results/championship_time_decay.md).

Normal `pytest` runs the experiment's focused tests with the rest of DeepFC.
