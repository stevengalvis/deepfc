from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parent;x=json.loads((R/'results.json').read_text())
p=lambda v:f'{100*v:.2f}%'
interval=lambda v:'—' if v is None else '['+', '.join(f'{100*z:+.2f}' for z in v)+']'
text='''# Frozen joint corner model reliability review

The joint model ranks corner-event risk better than fixed180 on these historical cohorts, but its pooled underprediction is concentrated in home-team forecasts. Later Championship home errors are about 3.6–4.8 percentage points across all four lines; post-training EPL shows a similar, less precise pattern. Away-team calibration-in-the-large is much closer, with heterogeneous errors across probability ranges. A global upward correction is not supported. A focused home-forecast correction is a defensible future research hypothesis, not a validated change to apply now.

This independent diagnostic uses frozen predictions reproduced from DeepFC commit `7e8ad0acdcea13f5778e107882c36e5d6922fbd3`. No model fitting, changed coefficients, live collection, betting selection or publication occurred. Both models use identical fixtures. `protocol.txt` was saved before slicing; its hash and input hashes are in `manifest.json`.

## Scope and frozen reporting rules

Primary cohorts are Championship 2023/24–2025/26 (1,599 fixtures, 33 occupied 28-day blocks) and EPL 2023/24–2025/26 (1,110 fixtures, 35 blocks). The latter follows May 2023 coefficient training. Full EPL 2019/20–2025/26 (2,571 fixtures, 80 blocks) is supplementary: it overlaps the primary EPL cohort and includes retrospective applications of later-trained coefficients. None is an untouched confirmation sample.

Cuts were fixed to league/cohort, home/away and lines 3.5, 4.5, 5.5, 6.5. Bins are [0,.2), [.2,.4), [.4,.6), [.6,.8), [.8,1]. Bins with fewer than 100 observations or 10 occupied blocks are marked sparse, never merged, and do not drive conclusions. These floors are reporting rules, not power guarantees. Bins are model-specific: comparing two dots does not mean comparing identical bin membership. Overall model comparisons do use identical rows.

We resample complete nonoverlapping calendar blocks (`date ordinal // 28`) 20,000 times, seed 7, sharing draws across models, lines and venues. Means are resampled totals divided by counts. Both fixture sides stay within their original block; eight event outcomes are not eight independent fixtures. Bin draws with zero observations are undefined; intervals are omitted if more than 1% of draws are undefined. Complete bin counts, occupied blocks, observed/predicted intervals and error intervals are in the `curves` section of `results.json` (also exported as `reliability_bins.csv` when regenerated). NumPy multinomial block counts implement the same resampling law as sampling blocks with replacement, but a different random-number stream from the earlier audit.

Positive error means observed frequency exceeds predicted probability. Tables use percentage points for error intervals. Main uncertainty is pointwise 95%; an additional Bonferroni family covers the 16 joint-model line/venue cells across the two primary cohorts, with 99.6875% two-sided intervals per cell. Bin comparisons and the supplementary cohort are exploratory. The adjusted intervals have only about 31 simulation draws per tail, so fine distinctions near zero should not be overinterpreted.

## Calibration in the large

These checks average all forecasts for one venue and line. They can reveal broad offsets but cannot establish calibration within probability ranges.
'''
for co,title in [('E1_later','Later Championship'),('E0_post_training','Post training EPL'),('E0_full_history','Supplementary full EPL history')]:
 text+=f'\n### {title}\n\n| Venue | Over line | Actual rate | Fixed180 predicted | Joint predicted | Joint error pp | Joint 95% error interval pp | Joint family interval pp |\n|---|---:|---:|---:|---:|---:|---|---|\n'
 for v in ['home','away']:
  for l in [3.5,4.5,5.5,6.5]:
   rows=[r for r in x['overall'] if (r['cohort'],r['venue'],r['line'])==(co,v,l)];b,j=rows
   text+=f"| {v} | {l} | {p(j['observed_rate'])} | {p(b['mean_predicted'])} | {p(j['mean_predicted'])} | {100*j['error_observed_minus_predicted']:+.2f} | {interval(j['error_ci95'])} | {interval(j['joint_primary_family_ci'])} |\n"
 text+=f'\n![{title} reliability]({co}_reliability.png)\n'
text+='''
All four Championship home errors exclude zero under the declared 16-cell adjustment at 28-day blocking. Pointwise home intervals remain above zero at both 14 and 56 days. This supports a systematic historical home offset under the resampling assumptions, not a prospective claim. Baseline home point errors are smaller, between −0.42 and +1.03 pp, though those estimates also have uncertainty.

Post-training EPL home errors are +3.13 to +4.44 pp. Three of four pointwise home intervals exclude zero at 14, 28 and 56 days; over 4.5 does not. None excludes zero under the main 16-cell adjustment. This is directional corroboration with limited precision, not independent statistical confirmation. EPL away over 3.5 is +2.66 pp, and its pointwise zero-exclusion changes with block length: treat it as uncertain. The other EPL away pooled errors lie between −0.75 and +0.64 pp. All primary away family intervals include zero; that does not demonstrate equivalence or perfect calibration.

## Where the errors occur

Home underprediction spans several lines and commonly populated probability ranges, rather than one isolated threshold. Some representative supported bins illustrate the scale; every prespecified bin is shown in the plots and complete JSON tables, so these examples are not a selected decision rule.

| Cohort and cell | Probability bin | Count | Mean prediction | Event frequency | Observed minus predicted 95% interval pp |
|---|---|---:|---:|---:|---|
'''
examples=[('E1_later','home',3.5,'0.6-0.8'),('E1_later','home',5.5,'0.4-0.6'),('E1_later','home',6.5,'0.4-0.6'),('E1_later','home',6.5,'0.0-0.2'),('E1_later','away',4.5,'0.2-0.4'),('E1_later','away',4.5,'0.6-0.8'),('E0_post_training','home',3.5,'0.6-0.8'),('E0_post_training','home',4.5,'0.6-0.8'),('E0_post_training','home',5.5,'0.4-0.6'),('E0_post_training','home',6.5,'0.4-0.6')]
for co,v,l,b in examples:
 r=next(r for r in x['curves'] if (r['cohort'],r['venue'],r['line'],r['bin'],r['model'])==(co,v,l,b,'joint'))
 text+=f"| {co}, {v}, over {l} | {b} | {r['n']} | {p(r['mean_predicted'])} | {p(r['observed_rate'])} | {interval(r['error_ci95'])} |\n"
text+='''
The exceptions matter. Championship home over 6.5 at predicted probabilities below 20% is overpredicted, while its 40–60% bin is underpredicted. Championship away over 4.5 has opposite errors in lower and higher probability bins despite near-zero pooled error. The higher bin has 110 observations, just above the reporting threshold: its conspicuous gap is exploratory and vulnerable to multiplicity and sampling variation. There is no reason to treat it as a betting opportunity or a stable correction target by itself. A venue-wide offset may still fail to repair range-dependent errors.

Hollow sparse points can look extreme, especially when one or a handful of outcomes dominate. Their empirical bootstrap may even be degenerate because resampling cannot invent unseen outcomes. Do not interpret narrow or zero-width intervals in such cells as precision. Across both models and all cohorts, 106 of 240 bins are empty or sparse. No inference is drawn from those visual excursions.

## Reliability and discrimination

We report AUC as a descriptive rank-separation statistic with half credit for ties. No new model or calibration function is fitted. The joint AUC exceeds fixed180 in all 16 primary venue/line cells, although one improvement is tiny and we do not claim all differences are statistically established. Brier improves in 15 of those 16 cells; the exception is post-training EPL home over 3.5 (+0.00013).

For fixed bins we compute the exact identity:

`Brier = uncertainty − binned resolution + binned reliability + within-bin remainder`.

Reliability is the count-weighted squared difference between bin mean prediction and event rate; lower is better. Resolution is the weighted squared difference between bin event rate and overall event rate; higher is better. The remainder is weighted within-bin forecast variance minus twice within-bin covariance of prediction and outcome. Omitting it would incorrectly apply the binned-forecast decomposition to continuous probabilities. The coarsened Brier score instead equals uncertainty − resolution + reliability.

The table averages the eight venue/line decompositions per cohort with equal weights, matching the score objective. AUC is averaged descriptively, not pooled into a new discrimination test.

| Cohort | Model | Brier | Binned reliability | Binned resolution | Within-bin remainder | Mean AUC |
|---|---|---:|---:|---:|---:|---:|
'''
for co in ['E1_later','E0_post_training']:
 for name in ['fixed180','joint']:
  rows=[r for r in x['decomposition'] if (r['cohort'],r['model'])==(co,name)]
  vals=[np.mean([r[k] for r in rows]) for k in ['brier','reliability_binned','resolution_binned','within_bin_remainder','auc']]
  text+=f'| {co} | {name} | '+' | '.join(f'{v:.6f}' for v in vals)+' |\n'
text+='''
On both primary cohorts, joint binned reliability is worse on average while resolution and rank separation improve. Within-bin behavior also contributes to the Brier gain. Thus a better overall proper score coexists with less accurate absolute probability levels; “better Brier” is not synonymous with “better calibrated.” Coarse-bin terms depend on the chosen bins and have finite-sample noise: the squared empirical calibration term is not an unbiased population miscalibration estimate. No significance claim or causal attribution is made from these component differences.

## Interpretation and next decision

One focused future calibration research question is justified: can a restrained correction of the joint model’s home-team probability levels improve reliability while retaining its discrimination and coherent ordering across lines? These findings do not justify selecting its form, magnitude or fitted parameters, or changing current forecasts. A blanket uplift across both venues is particularly unsupported because away averages are close and some low-probability cells already overpredict. Even a single home offset could worsen the low-probability exceptions.

If a correction is pursued, choose one form and an estimation procedure on designated development data, preserve coherent line probabilities, then freeze it before genuinely new confirmation outcomes. Do not use this same historical diagnostic as its validation. There is no need to launch another feature search or tune bins, venues, leagues or thresholds to find a favorable correction. The existing frozen joint model remains a promising research candidate with an identified calibration limitation.

Missing confirmation evidence remains: forecasts archived before outcomes, timestamped and source-matched odds at the declared horizon, a realistically powered prospective cohort, and approved practical margins. All these histories were reused; EPL full and post-training cohorts overlap, and shared leagues or repeated architecture inspection prevent an independence claim. Block resampling does not remove selection bias, authenticate quote timing, or protect against arbitrary cross-block team dependence and regime changes. No corner-price strategy, execution cost or betting-profit claim is evaluated.

## Reproduction and validation

Run `OPENBLAS_NUM_THREADS=1 MPLCONFIGDIR=/tmp/deepfc-mpl python diagnostic.py`, then `python write_report.py` in an environment with the versions in `manifest.json`. The bundled NPZ files contain the independently reconstructed outcomes, frozen means, dispersion, dates, venues and season labels. They originate from the audit’s 18 hash-verified source files; `../audit/source_manifest.json` records those hashes. The full audit reconstruction script is retained at ../audit/reproduce.py.

The script asserts complete home/away pairing, uses unchanged means and dispersion to reconstruct coherent NB probabilities, and checks the decomposition identity to numerical precision. The two primary overall Brier scores reproduce the prior audit. Hash checks before and after confirm the frozen NPZ inputs are unchanged. Plots were visually inspected. No tracked repository source or result artifact was edited. These historical diagnostic artifacts are published separately without changing the original model or conclusions.
'''
(R/'REPORT.md').write_text(text)
