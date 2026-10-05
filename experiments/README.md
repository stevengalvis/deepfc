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

## Championship shot pressure

[`shot_pressure.py`](shot_pressure.py) tests whether venue-specific historical
shots and shots on target add information beyond the fixed 180-day corner
model. It uses only results from dates strictly before each prediction, selects
one predeclared adjustment strength before 2023/24, and freezes it for later
evaluation. The retained model is not changed by this research experiment.

Run `python -m experiments.shot_pressure` with the same nine CSV paths above.
The [recorded result](results/championship_shot_pressure.md) is inconclusive:
the weak 0.25-strength signal improved later retrospective periods but did not
beat the baseline during selection. It is not approved for a Zeno shadow or
the retained model.
