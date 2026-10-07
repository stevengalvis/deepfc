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

## Championship goals / BTTS

[`goals_btts.py`](goals_btts.py) is an isolated, date-batched walk-forward
comparison for full-match O/U 2.5 and BTTS Yes/No. It reuses canonical match
identities, the completed-match CSV adapter, team/venue smoothing and the fixed
180-day corner-experiment setting without changing retained corner models.

It compares 0.5/event-rate baselines, venue-average Poisson, arithmetic and
multiplicative team/opponent Poisson, fixed time decay, and corresponding
Dixon-Coles low-score corrections. Same-date results are excluded from every
prediction and dependence estimate. The recent two-season report is a
retrospective pseudo-holdout, not an untouched prospective test.

The repository does not distribute the nine gitignored source CSVs, so a clean
checkout cannot independently reproduce the recorded metrics. Authorized
holders of the exact files listed and hashed in the provenance manifest can
place them under `data/` and run:

```bash
python -m experiments.goals_btts \
  data/E1_1718.csv data/E1_1819.csv data/E1_1920.csv \
  data/E1_2021.csv data/E1_2122.csv data/E1_2223.csv \
  data/E1_2324.csv data/E1_2425.csv data/E1_2526.csv
```

See [results, uncertainty and limitations](results/championship_goals_btts.md)
and the [nine-file provenance manifest](results/championship_goals_btts_data.json).
No CSVs, provider calls, production integrations, profitability claims or
promotion are part of this experiment. Current recommendation: **CONTINUE RESEARCH**.
