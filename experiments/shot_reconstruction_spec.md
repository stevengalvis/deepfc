# Shot-pressure reconstruction — frozen design

Frozen 2026-10-02 before any reconstruction metric evaluation. This is not recovered
commit 98762bd and implementation equivalence is not established. Parent code is
8af3712a132e97b35acdc56ddbdd0732f77eb815 (signal-strength research). Production
src/ is unchanged. Existing fixed-180 compare_models supplies the baseline,
eligibility, five-match corner smoothing and pooled all-history NB dispersion.

Recovered facts: E1 2017/18–2025/26, warm-up 2017/18, selection before 2023-07-01,
validation 2023/24, retrospective test 2024/25–2025/26; same-date results excluded;
venue-specific team shots/SOT produced and opponent shots/SOT allowed, 180-day
weights, reported shot strength 0.25. Later periods already inspected, not holdouts.
Existing code supplies 28-day paired bootstrap, 2000 draws, seed 7, and corner lines
3.5,4.5,5.5,6.5. Prior reported metrics are comparison checkpoints, never targets.

## Explicit reconstruction assumptions (not recovered facts)

For each feature (shots, SOT), compute weighted venue league mean L from valid
shot rows only. Team-for and opponent-allowed rates each receive a five-weighted-
match prior at L. Opponent-allowed uses the opponent's opposite venue history.
Feature ratio = (team-for/L)*(opponent-allowed/L). Combined pressure is geometric
mean of shots and SOT ratios. Candidate mean = fixed180 mean * pressure**strength.
Zero league mean or absent valid history gives neutral ratio 1. No clipping.
No additional shot-history eligibility filter: preserve baseline cohort exactly.
Grid fixed now: strengths 0.25,0.5,1.0. Select best shot candidate by earlier-period
Brier only (ties lower strength); retain baseline if no candidate beats it.
Also report predeclared 0.25 as a historical-checkpoint diagnostic if not selected.
The original grid, feature combination, smoothing, clipping and missingness rules
are unknown; therefore different results cannot establish failure of original code.

Validate integer nonnegative HS/AS/HST/AST, SOT <= shots, E1 and unique fixtures.
Missing/invalid shot rows are excluded from both venues' future shot histories,
never from corner evaluation. Explicitly quarantine Burnley–Swansea 2024-11-10
regardless of later source correction; preserve raw values and reason in output.
Use only completed matches known to corner loader for shot histories.

## Reproduction

From this checkout with the saved virtualenv:

```bash
/workspace/.venvs/deepfc/bin/python -m experiments.fetch_shot_data
PYTHONPATH=src:. /workspace/.venvs/deepfc/bin/python -m pytest
PYTHONPATH=src:. /workspace/.venvs/deepfc/bin/python -m experiments.shot_reconstruction data/E1_*.csv > experiments/results/shot_reconstruction/results.json
```

Data fetch writes raw CSVs to ignored data/ and records source URLs, retrieval UTC,
SHA256 and comparison with archived research hashes. Runner embeds source hashes,
row quality, specification hash, code hashes and all period/season/venue/line
metrics plus paired Brier/NLL/MAE intervals. Raw files must be retained for exact
reproduction if the public source changes. No profitability claim is supported.
