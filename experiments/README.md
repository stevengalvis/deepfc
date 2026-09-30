# Championship team-corner comparison

This isolated experiment compares the unchanged DeepFC model, the Zeno model
at `06cf7c0d84ca671c3e1a0d0ba57ab050b3f5164a`, and that Zeno model with a fixed
180-day half-life. It imports the pinned Zeno implementation directly. It does
not add a dependency to DeepFC's package or change either production model.

## Protocol fixed before running

- Championship full-match team corners, both venues, lines 3.5/4.5/5.5/6.5.
- Over and under are complements at these half-lines and have identical Brier
  loss, so they are not counted as independent evidence.
- 2017/18 warm-up; score from July 1, 2018. All supplied earlier seasons remain
  available as history. No same-date outcomes can influence a prediction.
- Common Zeno gates: 100 earlier team observations, five venue matches for
  both teams, five-match smoothing. Ineligible matches still enter subsequent
  history. Report coverage lost to these gates rather than claiming identical
  coverage to DeepFC's original ungated benchmark.
- Fix 180 days from the earlier experiment. No parameter search. Keep Zeno's
  pooled expanding-history dispersion unchanged for the decay candidate.
- Check every Zeno baseline prediction against its production forecast function.
- Primary score: mean Brier across the four lines. Secondary: count NLL,
  MAE/RMSE, venue and season slices, line bias, and five fixed calibration bins.
- Paired 28-day block bootstrap, 2,000 samples, seed 7. Preserve both teams and
  all lines together. Intervals measure retrospective sampling uncertainty,
  not uncertainty from repeated model selection or every form of dependence.
- A candidate warrants prospective testing if aggregate Brier improves with
  its paired interval below zero, count NLL also improves, and improvement is
  present in both venues and a majority of seasons. Examine individual lines
  and exceptions before deciding. Historical success never automatically
  replaces the live model.
- These seasons have already informed model development. Label this as
  retrospective evidence, not a fresh holdout or proof of profitable pricing.

## Run

From the DeepFC root, prepare a separate reference checkout once:

```bash
git clone https://github.com/stevengalvis/modelfc.git ../zeno-reference
git -C ../zeno-reference checkout 06cf7c0d84ca671c3e1a0d0ba57ab050b3f5164a
python -m pip install -e '.[test]'
PYTHONPATH=src:../zeno-reference/src python -m experiments.compare_team_corners \
  data/E1_1718.csv data/E1_1819.csv data/E1_1920.csv \
  data/E1_2021.csv data/E1_2122.csv data/E1_2223.csv \
  data/E1_2324.csv data/E1_2425.csv data/E1_2526.csv \
  --output experiments/results/championship_comparison.json
PYTHONPATH=src:../zeno-reference/src python -m pytest tests experiments/test_compare_team_corners.py
```

Use the Football-Data England archive's nine season files. Data stays in the
ignored `data/` directory. The report records each input's SHA-256 hash, source
filename, code revision and experiment hash. Season slices use source files,
not July boundaries, because the 2019/20 season finished in July 2020.

The experiment does not fetch data, call an odds provider, use live state,
select opportunities, or calculate ROI. Production availability and data
freshness gates are not reproduced by this historical model comparison.
