# Joint attack/defence experiment: numerical failure, no valid performance verdict

One statistical candidate implemented; three numerical attempts failed in development. No candidate aggregate metrics, later-period scores, uncertainty or statistical-gate verdicts were produced. Decision: research-only, numerically unvalidated; do not adopt. This is NOT an empirical rejection based on forecast quality.

## Attempt audit

1. Raw centered L-BFGS-B, ftol=1e-14: stopped 2018-08-31 (612 history fixtures, 75 iterations). success=True but projected gradient 0.0001047147 exceeded unchanged acceptance limit 0.0001. Rejected.
2. Same objective/parameters, stricter ftol=0: stopped 2021-04-25 (2179 fixtures, 127 iterations), gradient 7.55445e-6 but success=False / ABNORMAL line search. Rejected.
3. Equivalent orthonormal sum-to-zero contrasts, trust-exact with analytic Hessian: stopped 2018-10-24 (715 fixtures, 4 iterations), projected gradient 9.87479e-7 but success=False: A bad approximation caused failure to predict improvement. Rejected.

The numerical amendments were made and documented during development, before any aggregate performance metrics or later-period candidate evaluation. The objective, unit Gaussian regularization, 180-day weighting, pooled dispersion and all statistical gates remained unchanged. Final failure was not overridden despite its small gradient. No baseline substitution, dropped fixture or relaxed acceptance rule was used.

## Baseline checkpoints (from previous verified run, not candidate results)

| Period | Team observations | Brier | Count NLL | MAE |
| --- | ---: | ---: | ---: | ---: |
| selection | 5218 | 0.217140 | 2.338689 | 2.073609 |
| validation | 1048 | 0.210451 | 2.406443 | 2.200642 |
| later_test | 2150 | 0.208559 | 2.354073 | 2.120767 |
| combined_later | 3198 | 0.209179 | 2.371235 | 2.146942 |

Candidate metrics and paired intervals: unavailable. Season/venue/extreme-band candidate comparisons: unavailable. No valid paired evaluation exists because the candidate did not complete the identical fixture cohort. Baseline season/venue/band metrics and uncertainty remain in ../weakness_diagnostic/results.json. Band membership in the candidate runner is fixed by baseline mu (<4, [4,6), >=6).

## Gates

The numerical success gate FAILED. The following statistical gates are NOT EVALUATED (neither passed nor failed): combined later Brier improvement >=0.001; paired Brier upper bound <0; each later season improves; halve bias in both extreme bands; NLL point delta <=0 and upper bound <=+0.005; venue Brier worsening <=0.001. Combined later means 2023/24–2025/26, fixed before attempts; test-only gates are also coded separately. No bar was lowered and no favorable slice was substituted.

## Verification

79 tests passed in 0.80 seconds. Includes NB objective differences against existing likelihood, analytic gradient and Hessian finite differences, positive Hessian, identifiability, unseen effects, prior-date restriction, future/same-date outcome invariance, fixture/dispersion alignment and explicit hard failure. Synthetic tests validate calculations but cannot certify historical optimizer reliability. Python3.12.14, numpy2.5.3, scipy1.18.1. pip check passed.

Exact final attempt command (exited 1):

```bash
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.joint_strength > experiments/results/joint_strength/results.json 2> experiments/results/joint_strength/run.log
PYTHONPATH=src:. /workspace/.venvs/deepfc/bin/python -m pytest -q
```

The otherwise empty results.json was replaced after failure with a machine-readable failure-status record and prior baseline metrics, explicitly marking candidate metrics null. See failure.json, run.log, attempt1/, attempt2/, frozen_hashes.txt and the specification for exact evidence.

## Smallest next step

Resolve numerical termination on the saved pre-2023 development fixtures only, with a separately approved/refrozen convergence contract or a robust gradient-certified solver. Do not relax forecast-quality gates or tune against later outcomes. Then rerun this same statistical candidate end-to-end. No scientific conclusion about opponent-adjusted strength is justified until that completes. All historical validation remains exploratory; no pristine holdout or profitable betting edge is claimed.

Original checkout and production src/ unchanged. Zeno and its existing challenger unchanged. No push, merge or deployment. Raw historical CSVs stay ignored.
