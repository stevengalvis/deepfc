# Published research comparison and next-step recommendation

Publication authorized October2,2026. This summary accompanies the post-7e8ad0 experiments on `research/deepfc-2026-10-02`; no production promotion, merge or deployment. Historical reports saying “local/private only” record the scope at their execution time; the later publication authorization supersedes that restriction without altering their frozen methods, hashes or outcomes. Numerical risk/materiality references remain proposed research conventions.

## Findings

| Work | Main finding | Implication |
|---|---|---|
| [Distribution blend](distribution_blend/REPORT.md) | Early temporal OOF selection chose100% joint calibration,0% fixed180 | No effective blend or calibration remedy; no forced interior weight |
| [Goal-total odds](goal_total_extension/REPORT.md) | Incremental Brier gain vs joint .000370 E1 and .000576 later EPL; both paired intervals cross zero | No reliable added value; EPL MAE/low-band calibration worsened |
| [Residual persistence](residual_persistence/REPORT.md) | Later controlled attack/concession effects uncertain, fragile to team/dependence controls | Stop this particular feedback direction; no corrected candidate fitted |
| [Conditional dispersion](conditional_dispersion/REPORT.md) | Constant conditional-likelihood alpha improves Brier vs current dispersion by .000419 E1 and .000667 later EPL; odds conditioning adds only .000003/.000006 | Estimator insight, not useful demonstrated conditional signal; lower-tail EPL calibration worsens roughly2.5–2.7points, later EPL significance sensitive to block width |
| [D2 source audit](d2_coverage/REPORT.md) | Corner/shot counts present but market-average1X2 absent; team identity split | No D2 model transfer or bookmaker substitution; source gap remains |

Leading joint calibration remains the research reference, not an operationally promoted champion. Mean-fixed dispersion arms preserve every mean/MAE/bias; mean gates cannot improve. Full-versus-post-May2023 EPL interpretations remain separate: earlier EPL is retrospective use of later-trained coefficients. All histories were repeatedly inspected; intervals condition on fitted models and omit research-selection uncertainty. Quote timestamps remain unavailable. No betting-profit or causal claim follows.

Publication contains derived predictions/diagnostics (including observed team counts for reproducibility), code/specs and aggregate source inventories. It does not contain raw provider season files, credentials, private keys, local environment files or ModelFC private operational artifacts. Existing reports/coefficients were not rewritten. Separate independent-review work is not included or modified here.

## Next recommendation: audit event coverage before another model

**Do not start another candidate now.** Current evidence does not justify another calibration, blend, goal-total, residual or mean-fixed-shape variant. The most distinct hypothesis worth checking is whether **within-match state exposure and short corner bursts** account for conditional tail errors that aggregate prematch strength cannot describe. Goals/red cards can change game state, and corner sequences can cluster; this is a proposed mechanism, not an established explanation of our errors or a new claimed prediction signal.

Yip et al. motivate compound-count models through event clustering but study match totals; their work does not prove a team-specific state mechanism or forecast improvement. Inspecting event times would test that premise more directly than fitting another distribution to the same totals. [Primary manuscript](https://arxiv.org/html/2112.13001).

**Expected information gain:** distinguish sustained pre-match team characteristics from match-path effects and bursts, and determine whether a future state-aware count model has identifiable inputs. A posteriori state associations alone would not create a valid prematch predictor: actual current-match goals/cards/corners must never be supplied to a prematch forecast. Any later model would need to integrate over future states, not condition on their realized outcomes.

**Availability:** current Football-Data aggregates have no complete corner/goal/card event timeline. StatsBomb's official open-data repository exposes competition/match catalogs, event files and lineups with documented usage terms. Its catalog checked October2 lists EPL2015/16 and2003/04, and no Championship entry, so it does not furnish the required2019+ E1/E0 study. It is at most a schema/feasibility pilot, not a substitute validation league. [Provider repository](https://github.com/hudl/open-data), [competition catalog](https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json). No event dataset was downloaded or fitted for this recommendation.

**Prespecified bounded audit/comparison, if commissioned:**

1. Inventory authorized provider coverage for exactly the current E1/E0 seasons, with stable match/team IDs, corner timestamps, goals, dismissals, period/stoppage time and corrections. Verify permission for the intended analysis/publication separately. Compare event-derived team corner totals to existing counts for every matched fixture; report all mismatches and missingness by season, venue and existing baseline band. Stop if coverage/rights cannot support the same cohorts; do not silently switch competitions or select convenient fixtures.
2. If the audit succeeds, freeze one descriptive mechanism diagnostic before examining effects: team corner rate per minute while level, leading or trailing, with red-card state and match period; separately count consecutive same-team corners within a fixed120-second interval. Use a60-second threshold only as a declared sensitivity, not a search. Compare exposure-normalized rates within team-season/venue and pre-match strength strata, using fixture/time-block dependence-aware uncertainty. These are associations, not causal effects.
3. Discover definitions/estimates only on early Championship; apply unchanged to later Championship and post-May2023 EPL, preserving the retrospective label elsewhere. Compare saved joint model tail/calibration errors on the **identical event-covered subset** versus its full-cohort errors to expose coverage selection. Do not compare a new event-covered model to an unmatched baseline.
4. Only consistent, sizable and coverage-robust evidence would motivate a separately approved state-aware candidate. Its eventual comparator would be the saved joint distribution on identical fixtures, evaluated with Brier3.5–6.5 and count NLL/tail calibration; no realized future-state leakage. No such candidate or experiment is authorized or implemented by this recommendation.

This recommendation has a real data blocker: a suitable authorized E1/recent-EPL event source is not established. If it cannot be obtained, **pause new modeling rather than repeat variants merely to continue experiments**. No expected gain in Brier or profitability can responsibly be quantified before that audit.
