# Frozen goal-total probability extension

Frozen 2026-10-02 after schema/coverage audit, before any candidate fit or scores. One model only. Existing outcomes and production source remain untouched. Local commit only; no push/PR.

## Inputs and chronology

Use pinned existing E1/E0 files recorded in audit.json. Columns Avg>2.5 and Avg<2.5 are pre-closing market-average decimal odds in 2019/20 onward; never use AvgC, bookmaker, Max or imputed odds. Both must be finite >1, as must existing AvgH/D/A. Exclude the whole fixture from all model comparisons if either feature is invalid/missing. Abort duplicate/wrong-competition or hash mismatch. Earlier BbAv schema is audited but used only for historical corner warm-up, not features. Audit found 3,864 E1 and 2,660 E0 2019+ valid source fixtures, with no missing/invalid pairs or 1X2 triplets. Actual eligible cohorts still obey all existing history rules.

Provider documentation: https://football-data.co.uk/data.php (checked 2026-10-02) distinguishes non-C and C snapshots from 2019/20 and describes Betbrain to Oddsportal transition. Market-average bookmaker composition changed when Pinnacle was excluded from 2025-07-23. Columns are continuous, the quote-generating process need not be. Exact quote timestamps unavailable; no claim of verified kickoff-minus-N-minute availability. E1 archived-primary hashes verified previously; E0 is mirror-pinned without independent primary hash verification. No fresh historical data downloads.

## Single model and fitting

q=(1/Avg>2.5)/(1/Avg>2.5+1/Avg<2.5). Use g=q-0.5, with fixed centering and no fitted scale. This is a normalized market scoring-level proxy, not measured expected goals. Normalizing overround does not guarantee a fair probability. No inversion into expected goals or goal-to-corner causal interpretation.

mu = mu_fixed180 * exp(a_home I_home + a_away I_away + h log(mu_fixed180/5) + beta s + delta g). s is existing normalized AvgH/D/A home-minus-away probability, sign reversed for the away team. g has the SAME sign for both sides; one added coefficient, no interactions, splines or league coefficients. The original four coefficients and delta are jointly estimated; gamma=1+h. Fixed180 and its earlier-date-only local-league dispersion/history rules unchanged. Predict a full NB distribution using this mean and existing dispersion.

Fit summed team-observation NB NLL plus 0.5 times squared norm of all FIVE coefficients (unit ridge identical to joint model). No penalty search or dispersion fit. Use existing certified Newton algorithm with independent long-double score <1e-8 and positive Hessian; fail hard, no optimizer fallback.

One feature/transform/penalty selected a priori. Early chronological development folds: fit only eligible E1 dates before July 1, 2021 then score source 2021/22; fit before July 1, 2022 then score 2022/23. Each fold refits both the original four-parameter joint specification and the five-parameter extension on the same eligible earlier data. Report paired fold Brier/NLL/MAE descriptively; no fold-result gate or model/weight selection. No in-sample predictions used for selection. Then fit the single final extension on eligible E1 source seasons 2019/20 through 2022/23, dates <2023-07-01 (last match May 2023). Save fit coefficients/certificates and hashes BEFORE later/EPL evaluation. No later or EPL fitting/tuning.

## Evaluation and interpretation

Use the exact saved distribution_blend/predictions.csv fixture/venue cohort; compare fixed180, SAVED final joint and extension on identical quote-valid rows. Recompute fixed180/joint metrics against saved values within 1e-12. Saved joint was fitted on the same early E1 period. If missing quotes cause different training coverage, explicitly flag comparator training-cohort difference; no hidden joint refit. Evaluation E1 2023/24–2025/26; EPL 2019/20–2025/26. Split EPL through May 31, 2023 versus after that date; early EPL is retrospective application of later-estimated parameters. All inspected history exploratory, not independent confirmation.

Primary outcome equal mean Brier across four team-corner lines 3.5/4.5/5.5/6.5 and both fixture sides. Incremental contrast extension minus saved joint is primary; extension minus fixed180 also fully reported. Count NLL, mean MAE, actual-minus-mean bias secondary. Negative loss deltas favor extension. Report 28-day calendar-block paired bootstrap 10,000 resamples seed 7, pointwise 95% intervals preserving fixture sides/lines; 14/56-day overall sensitivity. Conditional intervals omit fit/selection uncertainty and research multiplicity. No new operational acceptance gate: an interval crossing zero is inconclusive for incremental directional improvement; favorable historical intervals alone do not promote a model. Proposed .001 Brier materiality is descriptive, not an approved threshold.

Report overall, season, venue, fixed180-mean bands <4/[4,6)/>=6, season×band, era, era×band and era×venue with Brier/NLL/MAE/bias and intervals. Include each line's observed frequency/prediction/error and tails <=1, >=10 with probability/error/Brier intervals. Coverage denominators and exclusions visible. Discuss conflicting seasons/calibration, not merely aggregate baseline gains. No every-season-sign veto or relative-bias-halving criterion. No variant search if unfavorable/inconclusive.
