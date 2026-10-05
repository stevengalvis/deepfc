# Championship 180-day prospective protocol

## Decision question

Does the frozen 180-day Championship team-corner model produce more accurate
probabilities than the current venue-opponent model on matches that occur after
the protocol is fixed?

This is a prospective model-quality evaluation. It is not a profitability test
and cannot establish a sportsbook edge.

## Frozen scope

- Competition: EFL Championship (`E1`).
- Market: full-match team corners only.
- Lines: 3.5, 4.5, 5.5 and 6.5.
- First eligible date: October 9, 2026.
- Baseline: current venue-opponent Negative Binomial model.
- Candidate: fixed 180-day venue-opponent Negative Binomial model.
- Candidate half-life: 180 days.
- Smoothing: five effective matches.
- One baseline and one candidate only.

Both models must score the same team observations using the same historical
data cutoff and outcome. Predictions must be recorded before kickoff with the
model version, data snapshot and creation timestamp.

## Metrics

The primary metric is mean Brier score across the four frozen lines and all
eligible team observations. Lower is better.

Safety metrics are:

- Negative Binomial count negative log-likelihood;
- mean absolute error of expected team corners;
- Brier score by line, venue and evaluation month; and
- missing, late or mismatched prediction counts.

Segment results are diagnostics. They cannot replace the primary metric or be
used to select a favorable subset after results are known.

## Checkpoints

- After 48 team observations, verify only that records, timestamps and outcomes
  are complete. Do not make a model decision.
- After 240 team observations, publish a descriptive interim report. Do not
  promote, reject, tune or replace either model.
- Make the final decision after 600 eligible team observations.

The 600-observation threshold is a predeclared operational minimum, not a claim
of guaranteed statistical power. If the season ends before reaching it, the
result is `INCONCLUSIVE`.

## Final decision

Calculate candidate-minus-baseline differences on paired observations. Use the
existing 28-day paired block bootstrap with 2,000 samples and seed 7.

The result is `PASS` only when all of the following are true:

1. The candidate has a lower overall mean Brier score.
2. The Brier difference's 95% interval is entirely below zero.
3. Candidate count negative log-likelihood is no worse than baseline.
4. Every scored prediction was created before kickoff from an allowed snapshot.

The result is `REJECT` when the candidate has worse overall Brier or count
negative log-likelihood after the final sample is reached. Other mixed or
uncertain results are `INCONCLUSIVE`.

`PASS` makes the candidate eligible for human promotion review. It does not
change a retained model, production model or Zeno configuration automatically.

## Guardrails

Until the final decision:

- do not change either model, half-life, smoothing or evaluated lines;
- do not backfill predictions after kickoff;
- do not add another live shadow candidate;
- do not search subgroups for a different promotion rule;
- do not treat odds, expected value or settled returns as model-quality metrics;
- do not let an agent choose a follow-up experiment; and
- do not merge experimental logic into retained model code.

An agent may validate records, calculate the frozen metrics and draft reports.
Only a human may approve a new experiment or model promotion.
