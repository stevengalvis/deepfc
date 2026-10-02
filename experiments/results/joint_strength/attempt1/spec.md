# Frozen joint attack / defence experiment

Frozen before viewing any candidate historical metrics, 2026-10-02. One candidate;
no grid, no later-period tuning. This implements weakness_diagnostic/PROPOSAL.md.
All historical validation is exploratory because the seasons were inspected before.

For team i scoring corners at venue v against j at opposite venue u:
log(mu)=b_v + a_(i,v) + d_(j,u). Four effect families (home/away attack,
home/away concession) each sum to zero across all teams in prior history.
Two unpenalized venue intercepts. Teams absent from prior history get zero effects.
Team roster is formed from prior dates only; never from future fixtures.

Minimize SUM over prior team-match observations of
w * NB_negative_log_likelihood(y, exp(eta), alpha) + 0.5*SUM(effect**2).
w=2**(-age_days/180), unnormalized. Unit log-scale Gaussian prior variance for
every centered effect. No penalty on intercepts. Alpha is baseline's pooled
all-prior-history corner moment dispersion at the prediction date, held fixed
during fitting; NB variance=mu+alpha*mu**2. Poisson limit if alpha<=1e-12.
The objective implementation omits constants independent of eta only.
Both venues' observations are included jointly. Four raw parameter vectors are
centered on every objective evaluation; gradients are projected accordingly.
Redundant constant directions are initialized to zero and have zero gradients.

Refit once before EACH eligible forecast date, using matches strictly earlier
than the date. All same-date forecasts use that one fit, before any updates.
Use all earlier completed E1 fixtures including warm-up, independent of whether
they were eligible to be scored. Baseline's common fixture eligibility is preserved.
L-BFGS-B, analytic gradient, maxiter=1000, maxls=40, ftol=1e-14, gtol=1e-6.
Cold start: zero team effects, venue intercept log of weighted observed venue mean
(minimum 1e-6 solely to initialize in all-zero synthetic histories).
Converged only if optimizer success, finite objective/parameters and projected
maximum absolute gradient<=1e-4. Fail hard otherwise, record failure and date;
NO baseline substitution, dropped fixtures, second solver, or relaxed tolerance.
No clipping of fitted means. Overflow/nonfinite values are run failures.

Exact archived E1 CSV hashes are checked against verified_data_manifest.json.
Fixed180 baseline is primary; retained DeepFC separately reported on same fixtures.
2017/18 warmup; evaluation from 2018-07-01; development before 2023-07-01;
validation [2023-07-01,2024-07-01); test >=2024-07-01.
Resolve 'combined later periods' BEFORE running as validation+test (>=2023-07-01).
Apply gates to that combined cohort; also report test-only gates, never substitute
whichever is more favorable. Season slices use source CSV (July 2020 is 2019/20).
Fixed180 mu defines unchanged <4, [4,6), >=6 bands for both models.

Unchanged gates on combined later cohort:
- Brier candidate-baseline <= -0.001 and paired 95% upper bound <0;
- Brier improves in EACH 2023/24,2024/25,2025/26 season;
- absolute mean bias in BOTH extreme bands <=half baseline absolute bias;
- count-NLL delta <=0 and paired 95% upper bound <=+0.005;
- no venue Brier delta >+0.001.
All gates required; failure means reject this candidate as the next challenger.
Also show full-history extreme bias against the original diagnostic target.
Intervals: paired 28-day blocks, 2000 draws, seed7, inherited research helper;
pointwise not multiplicity-adjusted. Bias intervals use same block method.
Report Brier, count NLL, MAE, RMSE, all seasons/venues/lines and extreme bands.
No claim of pristine holdout, causal proof, profitable edge, or promotion.

Dependencies isolated to research: numpy==2.5.3, scipy==1.18.1, Python3.12.14.
Original src/ and project dependencies unchanged. No Zeno changes.
