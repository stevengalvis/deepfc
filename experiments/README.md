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

## Championship attack/concession signal strength

[`signal_strength.py`](signal_strength.py) keeps the fixed 180-day model and
tests a small grid of exponents controlling how strongly team attack and
opponent concessions move the expected count away from the league rate. It
selects before 2023/24 and freezes one candidate for later evaluation.

Run `python -m experiments.signal_strength` with the same nine CSV paths above.
The [recorded result](results/championship_signal_strength.md) retains the
original full-strength formula because the selected damped candidate worsened
later Brier and count NLL.

## Research test environment

The full suite includes NumPy/SciPy research tests. Use Python 3.12 and install
the pinned research requirements in addition to the lightweight package/test extra:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[test]" -r experiments/joint_strength_requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
```

CI uses the same dependency inputs. Production dependencies remain unchanged.
Raw provider datasets are not needed for tests; reproducing historical experiments
requires the separately documented source files and hashes. The EPL transfer is
documented in [its report](results/e0_transfer/REPORT.md), including the separate
2023/24-onward analysis and the limitations of earlier retrospective application.
