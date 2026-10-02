# Independent review of the frozen joint corner model

The joint model deserves to remain a leading research candidate, but the evidence does not justify promotion. No critical implementation or arithmetic defect was found in the audited path. The published reports generally state the limitations accurately.

The audited branch was research/deepfc-2026-10-02 at commit `7e8ad0acdcea13f5778e107882c36e5d6922fbd3`. This review is preserved separately and does not update that branch's source, historical results or decisions.

## Personally reproduced

A fresh environment passed all 102 existing tests and pip check. All 18 E1/E0 source files were retrieved from their pinned public mirror and matched their published hashes. An independent vectorized fixed180 implementation and SciPy NB probabilities/log likelihood reproduced Brier, count NLL, MAE, means and tail probabilities across 30 E1 and 36 EPL groups within 1e-12. The main paired bootstrap intervals and EPL 14/56-day sensitivities also reproduced. Complete fixture pairing and quote exclusions were checked.

Without refitting, the saved joint parameters gave gradient infinity norm about 1.18e-9 and minimum Hessian eigenvalue 184.783088. The original odds coefficient's score was about −2.06e-13. Original spec/code/coefficient hashes agreed with the frozen manifests. Replicating resampling arithmetic does not independently validate its statistical assumptions.

| Cohort | Fixtures | Fixed180 Brier | Joint Brier | Joint minus fixed 95% block interval |
|---|---:|---:|---:|---|
| E1 2023/24–2025/26 | 1,599 | 0.209179 | 0.206365 | −0.002814 [−0.005044, −0.000694] |
| EPL 2019/20–2025/26 | 2,571 | 0.208713 | 0.204667 | −0.004046 [−0.005515, −0.002609] |
| EPL 2023/24–2025/26 | 1,110 | 0.210068 | 0.206135 | −0.003934 [−0.006328, −0.001651] |

Numerical evidence is in results.json and slice_checks.json. The independently reconstructed derived arrays are retained under ../reliability; raw provider CSVs are not published here.

## Prioritized findings

**High importance for interpretation. Independent confirmation is absent.** Training used 4,224 eligible observations through 8 May 2023. Earlier EPL applications are retrospective forecasts made with later-trained coefficients, not historically available forecasts. Later EPL evaluation follows training chronologically but prior EPL exposure and repeated architecture selection prevent an untouched-holdout interpretation. Freezing each successive specification does not undo selection on inspected outcomes. The reports correctly disclose this. See [training code](../../joint_market_calibration.py#L32) and [transfer qualification](../../results/e0_transfer/REPORT.md).

**High importance for calibration claims. Better proper scores do not establish calibrated probabilities.** Joint pooled over-event frequencies were underpredicted at all four lines by about 1.04–2.18 percentage points in later E1 and 1.47–3.02 points in post-training EPL. E1 extreme-band count biases reproduced as low-band −0.283 versus baseline +0.019, and high-band +0.351 versus −0.289. Tail behavior is mixed. The subsequent [reliability diagnostic](../reliability/REPORT.md) separates the predominant home-team offset from away averages and range-dependent errors. Calling the procedure calibration is reasonable; calling the resulting probabilities well calibrated would overstate the evidence.

**High importance for operational claims. Timing and provenance remain unresolved.** Hash verification identifies reproducible mirror bytes, not original-provider authentication of EPL data or quote availability at an exact forecast horizon. Historical AvgH/D/A has no quote-capture timestamp and cannot establish kickoff−60-minute source parity. It is match-result odds, not executable corner-market prices. No betting-profit evidence exists. See [odds audit](../../results/odds_audit/AUDIT.md) and [EPL inventory](../../results/e0_feasibility/inventory.json).

**Medium importance. Bootstrap inference is descriptive and conditional.** Fixture sides and lines are correctly preserved within calendar blocks, and resampled means are observation-weighted. E1 has only 33 primary blocks. Repeated teams, overlapping histories and regime changes can induce longer dependence. EPL block-width agreement is reassuring but does not remove those limitations. Pointwise intervals do not account for adaptive model selection or support collective claims over all displayed subgroups. See [bootstrap code](../../market_strength_diagnostic.py#L24).

**Medium importance. Original gates were enforceable but imperfect definitions of usefulness.** Paired cohorts, chronology and a proper score were sound. Every-season point-estimate wins ignore uncertainty. Halving near-zero baseline bias produced an E1 low-band tolerance of only about 0.0094 corners. A point gain of 0.001 plus a confidence interval excluding zero does not establish a gain exceeding 0.001. The [acceptance audit](../../results/acceptance_criteria_audit/AUDIT.md) correctly explains these issues. Preserve historical rejections without interpreting them as proof of uselessness.

**Medium importance. The prospective contract remains a draft.** Its estimand, materiality distinction, calibration checks and inconclusive category improve on the original gates. Candidate, margins, horizon, coverage and dates require resolution. Tight simultaneous subgroup requirements can make a short study uninformative. The saved power report explicitly warns of this; its tables were inspected, not independently reproduced in this audit. Adding seasons does not enlarge a particular season's safety cell. See [protocol](../../protocols/team_corner_probability_confirmation.md) and [power report](../../results/power_planning/REPORT.md).

**Low importance. Original reproduction paths were machine-specific.** EPL execution hardcodes a former mirror root and the original joint E1 artifact lacks a dedicated prediction CSV. The independent reconstruction recovered the necessary evidence. This publication adds portable CLI paths and compressed derived arrays while leaving historical implementations unchanged. The old missing-NumPy CI caveat was already resolved at the audited commit, confirmed by the clean installation.

## Mathematical and leakage checks

NB shape is 1/alpha, success probability is shape/(shape+mu), and variance is mu+alpha*mu². Holding alpha fixed does not hold variance fixed when a correction changes mu. Arithmetic and scoring agree with this parameterization. Fixed180 uses strictly earlier dates and updates only after the whole date. Its pooled dispersion uses earlier counts. No full-sample normalization or same-day outcome leakage was found in the audited path. Pooled marginal dispersion remains a modeling approximation.

Four-line Brier uses equal line and team weights. Complete fixture pairs make this equivalent to equal fixture weighting. MAE of the predictive mean is descriptive and is not a calibration test. The saved objective uses correct NB derivatives and an identifying ridge penalty. See [history construction](../../time_decay.py#L143), [distribution code](../../../src/deepfc/corner_distribution.py) and [metric implementation](../../../src/deepfc/team_corners.py#L210).

## Verdict and evidence limits

Historical aggregate gains are verified. Research-candidate ranking is justified. Uniform superiority, untouched forward validation, calibrated probabilities, live readiness and profitability are not established. Later local-only blend, goal-market, residual and dispersion experiments were not inspected in this independent audit and are not evidence claimed by it.

The recommended next work was a focused reliability diagnostic and better independent evidence rather than another broad search. That diagnostic is now included, along with the subsequently approved one-parameter home slope plan and its [stopped execution](../home_slope/REPORT.md). The stopped experiment does not alter this audit's original assessment of the frozen joint model.
