# Single global distribution blend: no useful new tradeoff

**The prespecified selection chose w=1.0:100% joint calibration,0% fixed180. Reject blending as an additional calibration remedy under this experiment.** It is exactly the saved joint distribution, with identical scores and conditional errors. This is neither a new winning model nor a reason to reopen any Championship acceptance decision. No alternative weight was tried after this result.

## Selection without same-outcome component fitting

One component was chosen before scores: saved joint baseline/odds calibration, motivated by its previously observed contraction/overcorrection. The original-odds component was not searched as a second family. Mixture PMF is (1−w)NB_baseline+w NB_joint with one global w∈[0,1]. Over probabilities and means mix coherently; log loss is negative log of mixed probability mass, not the NB likelihood at the mixed mean.

Weight selection used two temporal out-of-fold Championship seasons, four lines equally weighted. For2021/22, the joint component was fitted on2,076 eligible earlier observations through2021-05-08. For2022/23 it used3,140 observations through2022-05-07. Scored fold sizes1,064 and1,084 team observations, respectively;8,592 binary event scores total. The2021 fold outcomes legitimately become earlier training data for the2022 fold. No fold uses its own outcomes for component fitting.

Each fold uses the identical four-parameter joint specification, fixed unit penalties and certified solver. Independent gradient norms≈1.02e−10 and4.41e−10. Selection certificate contains the helper’s original2023 outer cutoff plus the stricter effective fold cutoff; supplied prediction lists enforce the latter. Exact fold coefficients and certificates are in selection.json.

Analytic bounded Brier minimizer: clip(sum((p_joint−p_base)*(y−p_base))/sum((p_joint−p_base)²),0,1); zero-denominator tie goes to baseline. No grid or weight penalty. The squared-difference denominator20.163732 is nonzero; endpoint1 is selected, not the degenerate tie. Weight/spec/code hashes were saved before later evaluation.

The selected weight applies to the saved final joint model trained on all eligible Championship data before2023-07-01. Fold models and this final model have different fitted coefficients: this is a stacking-style transfer assumption, explicitly frozen, not an assertion that the final component supplied out-of-sample development predictions. Optimizing w on the pooled fold outcomes also makes its own development objective a selection result rather than independent confirmation.

## Evaluation and pairing

Saved E1/E0 fixed180 and component Brier/NLL/MAE reproduced within1e−12 before accepting output. E1:2023/24–2025/26,3,198 team observations/1,599 fixtures. E0:2019/20–2025/26,5,142/2,571; chronology-qualified2023 onward2,220/1,110. E0 pre2023 uses later-trained Championship coefficients and a later-selected weight, so it is retrospective, not a historically available forecast. All periods have prior research exposure.

Identical fixture/venue/outcome pairs; strictly earlier local-league baseline histories retained. No provider downloads, E0 fits, refitting of saved final component, missing-quote substitution or new cohort selection. E0 derived forecasts and E1 input hashes are inherited from pinned artifacts. Mirror provenance and missing quote timestamps remain limitations.

Paired28-day calendar blocks,10,000 resamples seed7, pointwise95 intervals; entire fixture sides/lines kept together.14/56-day overall sensitivity also saved. Conditional intervals omit selection and parameter uncertainty. The larger bootstrap draw count explains small interval differences from the original2,000-draw Championship report; that report was not edited.

## Overall results

| Cohort | Model | Brier | Count NLL | MAE |
|---|---|---:|---:|---:|
| league=E1 | baseline | 0.209179 | 2.371235 | 2.146942 |
| league=E1 | component | 0.206365 | 2.356455 | 2.101047 |
| league=E1 | blend | 0.206365 | 2.356455 | 2.101047 |
| league=E0 | baseline | 0.208713 | 2.381499 | 2.195721 |
| league=E0 | component | 0.204667 | 2.364239 | 2.142337 |
| league=E0 | blend | 0.204667 | 2.364239 | 2.142337 |
| league=E0/era=pre2023 | baseline | 0.207683 | 2.369390 | 2.166678 |
| league=E0/era=pre2023 | component | 0.203552 | 2.353249 | 2.111789 |
| league=E0/era=pre2023 | blend | 0.203552 | 2.353249 | 2.111789 |
| league=E0/era=2023onward | baseline | 0.210068 | 2.397437 | 2.233948 |
| league=E0/era=2023onward | component | 0.206135 | 2.378704 | 2.182545 |
| league=E0/era=2023onward | blend | 0.206135 | 2.378704 | 2.182545 |

| Cohort | Metric | Blend−baseline | 95% CI | Blend−component |
|---|---|---:|---|---:|
| league=E1 | brier | -0.002814 | [-0.004971, -0.000712] | 0 (CI[0,0]) |
| league=E1 | nll | -0.014780 | [-0.021664, -0.007897] | 0 (CI[0,0]) |
| league=E1 | mae | -0.045895 | [-0.065783, -0.025299] | 0 (CI[0,0]) |
| league=E0 | brier | -0.004046 | [-0.005515, -0.002609] | 0 (CI[0,0]) |
| league=E0 | nll | -0.017260 | [-0.022562, -0.012083] | 0 (CI[0,0]) |
| league=E0 | mae | -0.053383 | [-0.067013, -0.040000] | 0 (CI[0,0]) |
| league=E0/era=pre2023 | brier | -0.004131 | [-0.006016, -0.002244] | 0 (CI[0,0]) |
| league=E0/era=pre2023 | nll | -0.016141 | [-0.022730, -0.009218] | 0 (CI[0,0]) |
| league=E0/era=pre2023 | mae | -0.054888 | [-0.071356, -0.037726] | 0 (CI[0,0]) |
| league=E0/era=2023onward | brier | -0.003934 | [-0.006328, -0.001651] | 0 (CI[0,0]) |
| league=E0/era=2023onward | nll | -0.018733 | [-0.027255, -0.010466] | 0 (CI[0,0]) |
| league=E0/era=2023onward | mae | -0.051402 | [-0.075196, -0.028217] | 0 (CI[0,0]) |

All baseline comparisons have favorable aggregate point metrics, but there is zero incremental gain over the component. The proposed0.001 research Brier threshold is descriptive only: E1 point gain exceeds it but upper CI−0.000712 does not establish a gain beyond it. Full E0 and2023 onward upper bounds do clear−0.001. None is a new approved acceptance rule.

## Season, venue and baseline-defined bands

Component and blend are identical; one shared column is shown for both. Bias is actual minus predicted. Bands retain fixed180<4,[4,6),>=6 membership.

| Slice | Team n | Baseline Brier | Component=blend Brier | Baseline bias | Component=blend bias | Blend bias95% CI | Brier delta95% CI |
|---|---:|---:|---:|---:|---:|---|---|
| league=E1/season=2023 | 1048 | 0.210451 | 0.210822 | +0.027966 | +0.229937 | [+0.145370, +0.313698] | [-0.002649, +0.003384] |
| league=E1/venue=home | 1599 | 0.214892 | 0.212627 | -0.028901 | +0.294453 | [+0.158304, +0.432168] | [-0.004919, +0.000414] |
| league=E1/band=4to6 | 2112 | 0.216950 | 0.212036 | +0.034814 | +0.144544 | [+0.011096, +0.274570] | [-0.007296, -0.002591] |
| league=E1/venue=away | 1599 | 0.203467 | 0.200103 | -0.050322 | -0.011173 | [-0.123466, +0.103394] | [-0.006125, -0.000608] |
| league=E1/band=lt4 | 369 | 0.170646 | 0.169017 | +0.018769 | -0.282712 | [-0.501154, -0.044469] | [-0.009246, +0.005156] |
| league=E1/band=ge6 | 717 | 0.206121 | 0.208881 | -0.288884 | +0.351476 | [+0.204200, +0.511793] | [-0.001407, +0.006963] |
| league=E1/season=2024 | 1066 | 0.203762 | 0.200060 | -0.192771 | +0.023568 | [-0.156094, +0.250756] | [-0.006151, -0.000744] |
| league=E1/season=2025 | 1084 | 0.213277 | 0.208256 | +0.045672 | +0.172386 | [+0.031063, +0.299070] | [-0.009716, -0.000894] |
| league=E0/season=2019 | 702 | 0.209246 | 0.206709 | -0.075784 | +0.147757 | [-0.074415, +0.389976] | [-0.006826, +0.002650] |
| league=E0/venue=home | 2571 | 0.208732 | 0.205720 | -0.066770 | +0.135276 | [+0.018734, +0.250983] | [-0.005053, -0.001037] |
| league=E0/band=lt4 | 739 | 0.159095 | 0.156953 | -0.181158 | -0.269411 | [-0.418605, -0.105505] | [-0.004669, +0.000244] |
| league=E0/venue=away | 2571 | 0.208694 | 0.203615 | -0.012926 | +0.052870 | [-0.052349, +0.159401] | [-0.007280, -0.002922] |
| league=E0/band=ge6 | 1208 | 0.203325 | 0.198516 | -0.147367 | +0.166906 | [-0.011962, +0.343324] | [-0.008140, -0.001546] |
| league=E0/band=4to6 | 3195 | 0.222227 | 0.218029 | +0.033489 | +0.150609 | [+0.061458, +0.241857] | [-0.006005, -0.002400] |
| league=E0/season=2020 | 740 | 0.208922 | 0.204444 | -0.071477 | +0.031485 | [-0.223125, +0.313122] | [-0.008434, -0.000153] |
| league=E0/season=2021 | 740 | 0.208632 | 0.203001 | +0.001803 | +0.134053 | [-0.019163, +0.309022] | [-0.009280, -0.002798] |
| league=E0/season=2022 | 740 | 0.204013 | 0.200218 | -0.030246 | +0.015129 | [-0.126033, +0.145966] | [-0.005898, -0.001416] |
| league=E0/season=2023 | 740 | 0.206240 | 0.204317 | +0.126203 | +0.306260 | [+0.155105, +0.457323] | [-0.006299, +0.002329] |
| league=E0/season=2024 | 740 | 0.210659 | 0.205103 | -0.205442 | +0.016752 | [-0.191666, +0.264272] | [-0.010064, -0.001806] |
| league=E0/season=2025 | 740 | 0.213306 | 0.208984 | -0.025840 | +0.009833 | [-0.120111, +0.136774] | [-0.007753, -0.001026] |

E1 low-band bias remains−0.283 and high-band+0.351; E0 low-band−0.269 and high-band+0.167. The mixture has not moderated either tail because it assigns zero weight to baseline. It also leaves joint’s2023/24 Championship Brier worsening unchanged. No every-season sign veto or relative-bias-halving test was introduced. Full NLL/MAE/uncertainty for these and season×band slices are in results.json.

## Tail calibration

| Slice | Event | Team n | Observed | Baseline p | Component=blend p | Blend error95% CI |
|---|---|---:|---:|---:|---:|---|
| league=E1 | low_tail | 3198 | 0.07223 | 0.07674 | 0.08045 | [-0.016616, -0.000024] |
| league=E1 | high_tail | 3198 | 0.08161 | 0.08756 | 0.07360 | [-0.002197, +0.018563] |
| league=E1/band=lt4 | low_tail | 369 | 0.14634 | 0.16751 | 0.14157 | [-0.036206, +0.046660] |
| league=E1/band=lt4 | high_tail | 369 | 0.01355 | 0.01430 | 0.02230 | [-0.019931, +0.005193] |
| league=E1/band=4to6 | low_tail | 2112 | 0.07292 | 0.07670 | 0.08216 | [-0.017860, +0.000385] |
| league=E1/band=4to6 | high_tail | 2112 | 0.07055 | 0.06731 | 0.06206 | [-0.004174, +0.021738] |
| league=E1/band=ge6 | low_tail | 717 | 0.03208 | 0.03015 | 0.04394 | [-0.025655, +0.002052] |
| league=E1/band=ge6 | high_tail | 717 | 0.14923 | 0.18491 | 0.13400 | [-0.011008, +0.047961] |
| league=E0 | low_tail | 5142 | 0.08226 | 0.09300 | 0.09855 | [-0.022584, -0.009803] |
| league=E0 | high_tail | 5142 | 0.08790 | 0.10006 | 0.09193 | [-0.011796, +0.003953] |
| league=E0/band=lt4 | low_tail | 739 | 0.21922 | 0.19541 | 0.18678 | [+0.006993, +0.057671] |
| league=E0/band=lt4 | high_tail | 739 | 0.02030 | 0.01674 | 0.01929 | [-0.008645, +0.012268] |
| league=E0/band=4to6 | low_tail | 3195 | 0.07042 | 0.09008 | 0.09813 | [-0.035897, -0.018879] |
| league=E0/band=4to6 | high_tail | 3195 | 0.06667 | 0.07824 | 0.07382 | [-0.015527, +0.001460] |
| league=E0/band=ge6 | low_tail | 1208 | 0.02980 | 0.03810 | 0.04569 | [-0.024725, -0.006560] |
| league=E0/band=ge6 | high_tail | 1208 | 0.18543 | 0.20876 | 0.18426 | [-0.020818, +0.023655] |

Events<=1 and>=10 corners. Probability errors are observed minus predicted. Component and blend tail probabilities, errors and Brier are exactly identical; blending does not resolve previously documented low-tail underprediction or mean-calibration tradeoffs. A proper aggregate score can favor the full component despite conditional calibration weaknesses.

## Recommendation and limits

Do not create another operational model or force an interior weight to manufacture a tradeoff. The tested single-global-weight/Brier-selection hypothesis provides no improvement over joint calibration. Preserve the finding that aggregate probability accuracy favored the full component in these early folds, without treating it as calibrated or independently confirmed.

The next productive research step remains a prespecified reliability/discrimination diagnosis using saved post2023 probabilities, especially joint low-band and venue-specific line calibration. If later work changes the selection objective to value calibration constraints, that would be a distinct, newly justified experiment; these later outcomes must not choose a weight. No such work was executed.

Only two early selection seasons; changing component fits, team/league shifts, repeated inspected data and conditional bootstrap limitations remain. Selection was leakage-controlled at the outcome-fitting level, but this does not erase architecture selection from previous research. E0 and E1 statistical results do not establish future performance or profitable betting.

## Reproduction and validation

105 tests passed. New tests verify probability-mass normalization, exact endpoint NLL, coherent over probabilities and expectation, analytic weight limits/tie, and exclusion of heldout/future outcomes from fold fitting. No production or earlier frozen experiment file changed. Source/code/spec and selection hashes verified.

```bash
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.distribution_blend select
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.distribution_blend evaluate
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m pytest -q
```

Running selection then evaluation reproduces the two-phase workflow; preserve selection.json before evaluation. Results include coherent mixture metrics and derived per-observation predictions. Local preservation only; no push, PR, merge or deployment.
