# Championship probability-forecast power feasibility

**Recommendation: do not register the full proposed acceptance package as a realistically powered two-season study.** A two-season fixed window can be informative for the primary endpoint under low loss variance and a true gain around0.002, but the proposed tight simultaneous calibration and extreme-band guards are likely to remain inconclusive. Agree an evidence duration and distinguish research diagnostics from mandatory qualification guarantees before proceeding. No candidate was fitted or collected.

## Data, scope and assumptions

Environment verified at commit3782ad73306f66c87a99cbf2c6ee66879b824cc2; prior audit/protocol remain locally uncommitted. Input: saved original-odds diagnostic predictions,1,599 fixtures /3,198 team observations from2023/24–2025/26. These previously inspected periods are now **development-only for variance planning**, not fresh confirmation or a pre2023 training sample. No candidate coefficient or outcome forecast was recalculated. Source checksum is embedded in results.json.

Average each fixture’s two saved team Brier differences, each already averaging four lines. Verify exactly one home and one away observation per fixture. Sample size below means complete eligible matches, not team observations or eight independent line outcomes. Future scope remains Championship over3.5/4.5/5.5/6.5 with equal weights.

Estimate effective variance with calendar-cluster sums: SE²=G/(G−1)*sum_g(sum_i_in_g(d_i−mean(d)))²/N², sigma_eff=SE*sqrt(N). Use14/28/56-day blocks. This retains fixture and within-block dependence, including repeated teams within a block; persistent team dependence across blocks is NOT fully identified. Explicit2×/4× variance scenarios stress unmodeled longer dependence and drift; they are assumptions, not confidence limits. Only three seasons are available, so fitting an elaborate dependence model would not supply reliable validation.

| Block days | Blocks | Effective sigma | Historical SE | Resampling range for sigma |
|---|---:|---:|---:|---|
| 14 | 61 | 0.012447 | 0.000311 | [0.010199, 0.014286] |
| 28 | 33 | 0.010841 | 0.000271 | [0.008455, 0.012678] |
| 56 | 18 | 0.009569 | 0.000239 | [0.006030, 0.011900] |

Ranges resample10,000 observed blocks and describe variability of the variance estimate under that empirical distribution; they are not robust bounds for future nonstationarity. Longer blocks happened to lower estimated variance; do not interpret that as stronger independence or choose the most favorable length. Seasonal28-day sigma estimates are0.00953,0.01047,0.01183 with only11 blocks each.

As a separate candidate-variability stress, the saved joint-calibration paired Brier interval implies sigma≈0.04437 using interval width/3.92*sqrt(1599), roughly16.8× the original-odds variance. This is only a normal approximation to an existing percentile interval, not a new fixture-level variance estimate. It shows why the original-odds variance must not be assumed for an unspecified future architecture.

## What is being powered

Let D>0 be assumed true Brier improvement and delta the required minimum. For a one-sided97.5% upper bound below−delta, normal-approximation power is Phi((D−delta)*sqrt(N)/sigma−1.96); N≈[(1.96+z_power)*sigma/(D−delta)]². All tables use80% and90% power and no observed gain is treated as the guaranteed future gain. Normal/asymptotic calculations are optimistic with few blocks; very small implied N is not a recommendation to stop after a handful of matches.

- **Detect any improvement at true gain0.001:** delta=0, gap0.001.
- **Demonstrate gain greater than0.001 at true gain0.002:** delta0.001, also gap0.001, hence the same N.
- **Demonstrate gain greater than0.001 when true gain is exactly0.001:** at the null boundary, acceptance probability is approximately2.5%, regardless of N. No finite N delivers80/90% power. If the true gain is smaller than the required minimum, more evidence increasingly rejects qualification.

0.001 remains a proposed research margin, not approved practical value. Scenarios hold variance fixed while shifting expected gain; they do not imply a real candidate can achieve an arbitrary gain at that variance.

## Required new eligible matches

| Variance case | True gain D | Target delta | N80 | N90 | Approx full-season equivalents at90% usable (N90) |
|---|---:|---:|---:|---:|---:|
| blocks_14 | 0.0010 | 0.0000 | 1,217 | 1,628 | 3.3 |
| blocks_14 | 0.0015 | 0.0010 | 4,865 | 6,512 | 13.1 |
| blocks_14 | 0.0020 | 0.0010 | 1,217 | 1,628 | 3.3 |
| blocks_14 | 0.0030 | 0.0010 | 305 | 407 | 0.8 |
| blocks_14 | 0.0050 | 0.0010 | 77 | 102 | 0.2 |
| blocks_28 | 0.0010 | 0.0000 | 923 | 1,235 | 2.5 |
| blocks_28 | 0.0015 | 0.0010 | 3,691 | 4,940 | 9.9 |
| blocks_28 | 0.0020 | 0.0010 | 923 | 1,235 | 2.5 |
| blocks_28 | 0.0030 | 0.0010 | 231 | 309 | 0.6 |
| blocks_28 | 0.0050 | 0.0010 | 58 | 78 | 0.2 |
| blocks_56 | 0.0010 | 0.0000 | 719 | 963 | 1.9 |
| blocks_56 | 0.0015 | 0.0010 | 2,875 | 3,849 | 7.7 |
| blocks_56 | 0.0020 | 0.0010 | 719 | 963 | 1.9 |
| blocks_56 | 0.0030 | 0.0010 | 180 | 241 | 0.5 |
| blocks_56 | 0.0050 | 0.0010 | 45 | 61 | 0.1 |
| variance_x2 | 0.0010 | 0.0000 | 1,846 | 2,470 | 5.0 |
| variance_x2 | 0.0015 | 0.0010 | 7,381 | 9,880 | 19.9 |
| variance_x2 | 0.0020 | 0.0010 | 1,846 | 2,470 | 5.0 |
| variance_x2 | 0.0030 | 0.0010 | 462 | 618 | 1.2 |
| variance_x2 | 0.0050 | 0.0010 | 116 | 155 | 0.3 |
| variance_x4 | 0.0010 | 0.0000 | 3,691 | 4,940 | 9.9 |
| variance_x4 | 0.0015 | 0.0010 | 14,761 | 19,760 | 39.8 |
| variance_x4 | 0.0020 | 0.0010 | 3,691 | 4,940 | 9.9 |
| variance_x4 | 0.0030 | 0.0010 | 923 | 1,235 | 2.5 |
| variance_x4 | 0.0050 | 0.0010 | 231 | 309 | 0.6 |
| joint_candidate_CI_proxy | 0.0010 | 0.0000 | 15,450 | 20,684 | 41.6 |
| joint_candidate_CI_proxy | 0.0015 | 0.0010 | 61,800 | 82,733 | 166.5 |
| joint_candidate_CI_proxy | 0.0020 | 0.0010 | 15,450 | 20,684 | 41.6 |
| joint_candidate_CI_proxy | 0.0030 | 0.0010 | 3,863 | 5,171 | 10.4 |
| joint_candidate_CI_proxy | 0.0050 | 0.0010 | 966 | 1,293 | 2.6 |

Conversion uses the standard24-team double round-robin size24×23=552 regular-season fixtures (also552 rows per archived season), excluding playoffs. These are season equivalents, not verified future fixture dates. Assume90% usable solely for planning, approximately497 eligible fixtures/season; realized coverage may differ. At100% usable, divide counts by552 instead. Historical eligible coverage1599/(3×552)=96.6% is not a future guarantee.

At the original28-day variance and gap0.001, N90=1,235; its descriptive sigma-resampling range translates to approximately751–1,689 matches. This range excludes architecture differences, long-lived team dependence and future shifts. Double variance gives2,470 and quadruple variance4,940. Very long horizons are arithmetic extrapolations: nonstationarity makes decades-long “confirmation” of a fixed model scientifically unattractive.

## Fixed-window illustration

| Variance case | True gain | Minimum gain | Power at2 seasons (~993 eligible) | Power at3 seasons (~1490) | Power at5 seasons (~2484) |
|---|---:|---:|---:|---:|---:|
| blocks_28 | 0.0015 | .001 | 30.6% | 42.9% | 63.3% |
| blocks_28 | 0.0020 | .001 | 82.8% | 94.5% | 99.6% |
| blocks_28 | 0.0030 | .001 | 100.0% | 100.0% | 100.0% |
| blocks_28 | 0.0050 | .001 | 100.0% | 100.0% | 100.0% |
| variance_x2 | 0.0015 | .001 | 17.6% | 24.2% | 36.9% |
| variance_x2 | 0.0020 | .001 | 53.8% | 71.1% | 90.2% |
| variance_x2 | 0.0030 | .001 | 98.4% | 99.9% | 100.0% |
| variance_x2 | 0.0050 | .001 | 100.0% | 100.0% | 100.0% |
| variance_x4 | 0.0015 | .001 | 10.9% | 14.2% | 20.9% |
| variance_x4 | 0.0020 | .001 | 30.6% | 42.9% | 63.3% |
| variance_x4 | 0.0030 | .001 | 82.8% | 94.5% | 99.6% |
| variance_x4 | 0.0050 | .001 | 100.0% | 100.0% | 100.0% |
| joint_candidate_CI_proxy | 0.0015 | .001 | 5.4% | 6.4% | 8.1% |
| joint_candidate_CI_proxy | 0.0020 | .001 | 10.6% | 13.8% | 20.1% |
| joint_candidate_CI_proxy | 0.0030 | .001 | 29.5% | 41.3% | 61.3% |
| joint_candidate_CI_proxy | 0.0050 | .001 | 81.1% | 93.6% | 99.4% |

A fixed **two full future regular seasons** after preregistration/input readiness is a reasonable bounded research window, not a promise of decisive acceptance. Under low variance, D0.002 gives83% power; three seasons give95%. With twice that variance, the same powers fall to54%/71%, reaching90% only near five seasons. If D is only0.0015, even the low-variance case needs about10 seasons for90% power beyond0.001. With joint-calibration-like variance and D0.002, the approximation exceeds40 seasons; D0.005 would instead need about2.6. Candidate identity and variability therefore need to be locked before a credible final power claim.

Choose and register start/end dates before any new scored outcomes; use full-season equivalents to plan, not a guessed calendar. Do not extend after seeing inconclusive results or stop early for success. A two-season window must honestly allow “inconclusive.” Three/five seasons are alternative plans to choose beforehand, not optional extensions.

## Secondary checks can dominate

Use the protocol’s two-season family K15 and Bonferroni bounds, proposed m_NLL=.005, m_Brier=.001, probability tolerance±.02. Below are per-check powers, not probability that ALL checks pass. For harm tests assume true candidate-minus-baseline harm0; for calibration equivalence assume true error0. These favorable centers do not assert actual future calibration. Near a tolerance boundary, requirements grow dramatically; at/beyond the boundary reliable acceptance is unavailable.

| Check | Historical cell observations | Eligible matches for80% | Eligible matches for90% |
|---|---:|---:|---:|
| calibration/home/3.5 | 1599 | 7,850 | 9,261 |
| calibration/home/4.5 | 1599 | 11,529 | 13,602 |
| calibration/home/5.5 | 1599 | 13,212 | 15,586 |
| calibration/home/6.5 | 1599 | 10,131 | 11,952 |
| calibration/away/3.5 | 1599 | 6,202 | 7,317 |
| calibration/away/4.5 | 1599 | 7,292 | 8,603 |
| calibration/away/5.5 | 1599 | 6,761 | 7,976 |
| calibration/away/6.5 | 1599 | 8,285 | 9,774 |
| NLL | 3198 | 996 | 1,258 |
| Brier/home | 1599 | 3,635 | 4,591 |
| Brier/away | 1599 | 2,473 | 3,123 |
| Brier/lt4 | 369 | 11,669 | 14,736 |
| Brier/ge6 | 717 | 11,016 | 13,912 |

These use cluster influence functions for subgroup means, retaining empty fixtures and each cell’s share of all eligible fixtures. Thus low-band369 observations are not treated as369 independent matches, and required totals are whole-cohort fixture counts. Forecast composition is assumed stable. Calibration sigma comes from original-odds forecast errors; other candidates may differ. No simultaneous equivalence was tested on historical outcomes.

For the eight line×venue calibration cells, the90% per-check requirement is7,317–15,586 matches, about15–31 season equivalents at90% coverage, even with true error zero. Worst-cell90% is necessary, not sufficient, for90% joint safety power. At±3pp those counts multiply by(2/3)²; at±5pp by(2/5)², but widening tolerance is a user/use decision, not a statistical repair. Under dependence inflation they increase further.

NLL guard alone is roughly1,258 matches at zero true harm. Extreme-band Brier non-inferiority needs about13,912–14,736, versus3,123–4,591 for venue checks. A truly improving subgroup could require fewer; do not assume historical gains repeat. Season-specific checks only have one season’s observations each: adding more seasons does not increase the sample within an individual season, and increases family size. They are especially likely to block acceptance near zero true seasonal harm. K15 calculations cannot be reused unchanged for a longer window with more mandatory season slices.

## Actionable conclusion

**The complete provisional protocol is not realistically powered for a short Championship-only study.** Keep its draft status. A primary Brier study can be useful over2–3 new seasons for a low-variance candidate with true gain around0.002, but guaranteeing tight simultaneous calibration and subgroup safety can demand implausibly long periods. A true gain only equal to the0.001 minimum cannot be certified beyond that minimum with high power at any duration.

Next decision for Steve: choose the maximum fixed evidence window and decide whether absolute2pp calibration and .001 subgroup harm bounds must be mandatory qualification guarantees or reported research diagnostics. Do not silently loosen them, lower the worthwhile margin, or remove gates to admit an old model. If all are mandatory, accept that qualification may remain inconclusive for many years; a wider justified scope would be a different population and need its own protocol. If a bounded2-season research study is preferred, explicitly approve its more limited claim and diagnostics before candidate registration. Candidate identity, assumed effect above the margin, practical margins and coverage/horizon remain open choices.

All2023/24–2025/26 outcomes are repeatedly inspected development evidence, including these variance estimates. Effective variance is estimated from one selected model and only three seasons; resampling cannot undo selection, recover unseen regimes or guarantee future team-dependence behavior. No claim of profitability, deployment suitability or a clean historical holdout is made.

## Reproduce and verification

```bash
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.power_planning > experiments/results/power_planning/run.txt
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m pytest -q
```

Code asserts complete fixture pairing; tests verify independent-block standard-error recovery, variance scaling, and the2.5% boundary-power distinction. Existing tests also run. No candidate fit, new forecasts, live collection, old outcome changes or publication. Raw numerical scenarios and assumptions are in results.json.
