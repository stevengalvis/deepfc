# Premier League frozen Championship-model transfer

**Both frozen adjustments transfer aggregate predictive gains to E0, with mixed calibration.** Joint calibration has the stronger aggregate Brier/NLL/MAE result; original odds improves low-band mean bias but worsens high-band overprediction. Joint calibration retains low-band overprediction and reverses high-band bias. This is a descriptive historical transfer, not a promotion or revised Championship verdict.

## Execution and chronology

One frozen run, no coefficient estimation, parameter selection, clipping or new variants. Exact saved Championship coefficients and source artifact hashes are in results.json and frozen_hashes.txt. Original odds beta0.11376584000060998; joint a_home−0.00870047867223288,a_away−0.01899680404719811,gamma0.3116296486016443,beta0.4215638920715592. Both retain baseline NB dispersion.

Primary scored source seasons2019/20–2025/26 as explicitly requested;2017/18–2018/19 corner warmup. Each fixture uses only strictly earlier E0 corner history under unchanged fixed180 arithmetic, smoothing, dispersion and eligibility. Explicit E0 competition support was added to the research comparator guard; no league relabelling or source-model algorithm edit. Default E1 remains unchanged and numerical equivalence is tested.

Scored 2,571 fixtures / 5,142 team observations out of2,660 fixtures in the seven source seasons:89 fixtures fail inherited history eligibility. Quote exclusions=0; identical ordered match/venue/outcome/dispersion pairs for all3 models. Four lines3.5–6.5, equal line/team weights. Source-year labels preserve July2020 matches as2019/20. Paired28-day blocks=80,10,000 draws,seed7;14/56-day sensitivity. Pointwise conditional intervals, not multiple-selection corrected.

**Temporal qualification:** correction coefficients were fitted on Championship outcomes through2023-05-08. Their application to earlier E0 seasons is retrospective and could not have been issued historically. E0 baseline inputs remain past-only, but that does not remove the later coefficient-training information. The separate2023/24–2025/26 analysis follows coefficient training chronologically. Neither subset is an untouched holdout because ModelFC previously inspected EPL outcomes and related models. No claim of future Championship confirmation.

## Aggregate metrics

| Period | Model | Team n | Brier | Count NLL | MAE |
|---|---|---:|---:|---:|---:|
| all | fixed180 | 5142 | 0.208713 | 2.381499 | 2.195721 |
| all | original | 5142 | 0.206795 | 2.375578 | 2.185400 |
| all | joint | 5142 | 0.204667 | 2.364239 | 2.142337 |
| era=pre2023 | fixed180 | 2922 | 0.207683 | 2.369390 | 2.166678 |
| era=pre2023 | original | 2922 | 0.205644 | 2.363537 | 2.157747 |
| era=pre2023 | joint | 2922 | 0.203552 | 2.353249 | 2.111789 |
| era=2023onward | fixed180 | 2220 | 0.210068 | 2.397437 | 2.233948 |
| era=2023onward | original | 2220 | 0.208311 | 2.391425 | 2.221797 |
| era=2023onward | joint | 2220 | 0.206135 | 2.378704 | 2.182545 |

### Paired candidate-minus-comparator differences

| Comparison | Period | Metric | Delta | 95% CI |
|---|---|---|---:|---|
| joint_vs_fixed180 | all | brier_delta | -0.004046 | [-0.005515, -0.002609] |
| joint_vs_fixed180 | all | nll_delta | -0.017260 | [-0.022562, -0.012083] |
| joint_vs_fixed180 | all | mae_delta | -0.053383 | [-0.067013, -0.040000] |
| joint_vs_fixed180 | era=pre2023 | brier_delta | -0.004131 | [-0.006016, -0.002244] |
| joint_vs_fixed180 | era=pre2023 | nll_delta | -0.016141 | [-0.022730, -0.009218] |
| joint_vs_fixed180 | era=pre2023 | mae_delta | -0.054888 | [-0.071356, -0.037726] |
| joint_vs_fixed180 | era=2023onward | brier_delta | -0.003934 | [-0.006328, -0.001651] |
| joint_vs_fixed180 | era=2023onward | nll_delta | -0.018733 | [-0.027255, -0.010466] |
| joint_vs_fixed180 | era=2023onward | mae_delta | -0.051402 | [-0.075196, -0.028217] |
| original_vs_fixed180 | all | brier_delta | -0.001918 | [-0.002462, -0.001407] |
| original_vs_fixed180 | all | nll_delta | -0.005921 | [-0.008021, -0.003915] |
| original_vs_fixed180 | all | mae_delta | -0.010321 | [-0.017335, -0.003488] |
| original_vs_fixed180 | era=pre2023 | brier_delta | -0.002040 | [-0.002707, -0.001346] |
| original_vs_fixed180 | era=pre2023 | nll_delta | -0.005853 | [-0.008447, -0.003203] |
| original_vs_fixed180 | era=pre2023 | mae_delta | -0.008931 | [-0.016852, -0.000371] |
| original_vs_fixed180 | era=2023onward | brier_delta | -0.001758 | [-0.002618, -0.000965] |
| original_vs_fixed180 | era=2023onward | nll_delta | -0.006011 | [-0.009477, -0.002820] |
| original_vs_fixed180 | era=2023onward | mae_delta | -0.012151 | [-0.024116, -0.000897] |
| joint_vs_original | all | brier_delta | -0.002128 | [-0.003350, -0.000938] |
| joint_vs_original | all | nll_delta | -0.011339 | [-0.015850, -0.006809] |
| joint_vs_original | all | mae_delta | -0.043062 | [-0.056289, -0.030027] |
| joint_vs_original | era=pre2023 | brier_delta | -0.002091 | [-0.003567, -0.000572] |
| joint_vs_original | era=pre2023 | nll_delta | -0.010288 | [-0.015977, -0.004394] |
| joint_vs_original | era=pre2023 | mae_delta | -0.045958 | [-0.061676, -0.029979] |
| joint_vs_original | era=2023onward | brier_delta | -0.002176 | [-0.004219, -0.000168] |
| joint_vs_original | era=2023onward | nll_delta | -0.012722 | [-0.020090, -0.005289] |
| joint_vs_original | era=2023onward | mae_delta | -0.039251 | [-0.062202, -0.016830] |

Full-period Brier gains versus fixed180 exceed proposed0.001 at the point estimate and at the28-day interval upper bound for both candidates. This describes evidence relative to a proposed research margin, not an approved acceptance gate. In2023 onward, original odds upper bound−0.000965 excludes zero but not−0.001; joint upper bound−0.001651 clears both. Joint versus original full-period upper bound−0.000938 excludes zero but does not establish an additional0.001 gain. Do not choose a different window to strengthen a claim.

### Dependence sensitivity, overall Brier CI

| Comparison | 14-day | 28-day | 56-day |
|---|---|---|---|
| joint_vs_fixed180 | [-0.005462, -0.002648] | [-0.005515, -0.002609] | [-0.005335, -0.002745] |
| original_vs_fixed180 | [-0.002490, -0.001348] | [-0.002462, -0.001407] | [-0.002398, -0.001422] |
| joint_vs_original | [-0.003327, -0.000921] | [-0.003350, -0.000938] | [-0.003282, -0.001007] |

All overall directions remain favorable under these block lengths. This does not eliminate persistent team dependence or cross-season regime uncertainty.

## Season/venue/band behavior

Both adjustments have lower Brier than fixed180 in each of the seven source seasons. Joint is not uniformly better than original odds:2023/24 joint-minus-original Brier is slightly positive. These are descriptive slice results, not every-season pass/fail rules.

| Slice | Team n / distinct fixtures | Model | Brier | NLL | MAE | Bias actual−predicted | Bias95% CI |
|---|---:|---|---:|---:|---:|---:|---|
| season=2019 | 702 / 351 | fixed180 | 0.209246 | 2.388580 | 2.212750 | -0.075784 | [-0.301177, +0.165256] |
| season=2019 | 702 / 351 | original | 0.208085 | 2.384666 | 2.212368 | -0.125852 | [-0.349509, +0.113275] |
| season=2019 | 702 / 351 | joint | 0.206709 | 2.377470 | 2.158042 | +0.147757 | [-0.074415, +0.389976] |
| venue=home | 2571 / 2571 | fixed180 | 0.208732 | 2.431293 | 2.287719 | -0.066770 | [-0.183048, +0.049347] |
| venue=home | 2571 / 2571 | original | 0.206392 | 2.425510 | 2.282250 | -0.181988 | [-0.297301, -0.065841] |
| venue=home | 2571 / 2571 | joint | 0.205720 | 2.416092 | 2.232691 | +0.135276 | [+0.018734, +0.250983] |
| band=lt4 | 739 / 737 | fixed180 | 0.159095 | 2.140182 | 1.780214 | -0.181158 | [-0.330771, -0.018934] |
| band=lt4 | 739 / 737 | original | 0.157228 | 2.129996 | 1.743060 | +0.004044 | [-0.144289, +0.166039] |
| band=lt4 | 739 / 737 | joint | 0.156953 | 2.126778 | 1.772423 | -0.269411 | [-0.418605, -0.105505] |
| venue=away | 2571 / 2571 | fixed180 | 0.208694 | 2.331704 | 2.103723 | -0.012926 | [-0.118092, +0.090822] |
| venue=away | 2571 / 2571 | original | 0.207199 | 2.325645 | 2.088550 | +0.013696 | [-0.091976, +0.118238] |
| venue=away | 2571 / 2571 | joint | 0.203615 | 2.312385 | 2.051984 | +0.052870 | [-0.052349, +0.159401] |
| band=ge6 | 1208 / 1199 | fixed180 | 0.203325 | 2.558039 | 2.565204 | -0.147367 | [-0.331725, +0.037166] |
| band=ge6 | 1208 / 1199 | original | 0.201059 | 2.556144 | 2.589736 | -0.474491 | [-0.656620, -0.291847] |
| band=ge6 | 1208 / 1199 | joint | 0.198516 | 2.532420 | 2.469053 | +0.166906 | [-0.011962, +0.343324] |
| band=4to6 | 3195 / 1988 | fixed180 | 0.222227 | 2.370567 | 2.152129 | +0.033489 | [-0.057955, +0.124609] |
| band=4to6 | 3195 / 1988 | original | 0.220429 | 2.364110 | 2.134837 | +0.043041 | [-0.047005, +0.133851] |
| band=4to6 | 3195 / 1988 | joint | 0.218029 | 2.355575 | 2.104370 | +0.150609 | [+0.061458, +0.241857] |
| season=2020 | 740 / 370 | fixed180 | 0.208922 | 2.364351 | 2.134849 | -0.071477 | [-0.325626, +0.221159] |
| season=2020 | 740 / 370 | original | 0.206931 | 2.360326 | 2.124358 | -0.112945 | [-0.369191, +0.182460] |
| season=2020 | 740 / 370 | joint | 0.204444 | 2.348106 | 2.079059 | +0.031485 | [-0.223125, +0.313122] |
| season=2021 | 740 / 370 | fixed180 | 0.208632 | 2.365102 | 2.155776 | +0.001803 | [-0.158263, +0.184811] |
| season=2021 | 740 / 370 | original | 0.206106 | 2.356897 | 2.141408 | -0.044166 | [-0.204403, +0.140160] |
| season=2021 | 740 / 370 | joint | 0.203001 | 2.344417 | 2.091645 | +0.134053 | [-0.019163, +0.309022] |
| season=2022 | 740 / 370 | fixed180 | 0.204013 | 2.360512 | 2.165701 | -0.030246 | [-0.176720, +0.105549] |
| season=2022 | 740 / 370 | original | 0.201579 | 2.353344 | 2.155658 | -0.072914 | [-0.221005, +0.063621] |
| season=2022 | 740 / 370 | joint | 0.200218 | 2.344246 | 2.120786 | +0.015129 | [-0.126033, +0.145966] |
| season=2023 | 740 / 370 | fixed180 | 0.206240 | 2.425852 | 2.284512 | +0.126203 | [-0.032443, +0.281122] |
| season=2023 | 740 / 370 | original | 0.204258 | 2.418438 | 2.266322 | +0.076100 | [-0.082435, +0.231010] |
| season=2023 | 740 / 370 | joint | 0.204317 | 2.414150 | 2.241979 | +0.306260 | [+0.155105, +0.457323] |
| season=2024 | 740 / 370 | fixed180 | 0.210659 | 2.412755 | 2.323348 | -0.205442 | [-0.407994, +0.031352] |
| season=2024 | 740 / 370 | original | 0.208709 | 2.404890 | 2.309258 | -0.251475 | [-0.454865, -0.010810] |
| season=2024 | 740 / 370 | joint | 0.205103 | 2.386474 | 2.242520 | +0.016752 | [-0.191666, +0.264272] |
| season=2025 | 740 / 370 | fixed180 | 0.213306 | 2.353703 | 2.093983 | -0.025840 | [-0.148100, +0.093657] |
| season=2025 | 740 / 370 | original | 0.211966 | 2.350948 | 2.089809 | -0.059915 | [-0.182038, +0.060345] |
| season=2025 | 740 / 370 | joint | 0.208984 | 2.335487 | 2.063137 | +0.009833 | [-0.120111, +0.136774] |

Bands use fixed180 means; no candidate-dependent migration. Low n739: bias fixed180−0.181→original+0.004→joint−0.269. The original low-band mean-bias failure from Championship does **not** transfer as a pooled E0 pattern. High n1,208:−0.147→−0.474→+0.167. Original high-band overprediction persists; joint compresses enough to reverse signed bias, though its high-band bias interval[−0.012,+0.343] includes zero.

Joint high-band Brier improves−0.004810 [−0.008140,−0.001546], unlike its earlier Championship high-band result; high-band NLL and MAE also improve. Low-band joint Brier improvement has interval crossing zero and its MAE is worse than original odds. Thus aggregate gains do not establish superiority in every operating region.

## Tail and line calibration

| Slice | Event | Team n | Observed | Fixed180 p | Original p | Joint p | Original error95% CI | Joint error95% CI |
|---|---|---:|---:|---:|---:|---:|---|---|
| all | low_tail | 5142 | 0.08226 | 0.09300 | 0.09616 | 0.09855 | [-0.020307, -0.007325] | [-0.022584, -0.009803] |
| all | high_tail | 5142 | 0.08790 | 0.10006 | 0.10671 | 0.09193 | [-0.026686, -0.010802] | [-0.011796, +0.003953] |
| era=2023onward | low_tail | 2220 | 0.08649 | 0.09385 | 0.09691 | 0.09935 | [-0.019885, -0.000881] | [-0.021933, -0.003580] |
| era=2023onward | high_tail | 2220 | 0.09414 | 0.10192 | 0.10841 | 0.09248 | [-0.028514, +0.000430] | [-0.012743, +0.016803] |
| band=lt4 | low_tail | 739 | 0.21922 | 0.19541 | 0.21682 | 0.18678 | [-0.023316, +0.028164] | [+0.006993, +0.057671] |
| band=lt4 | high_tail | 739 | 0.02030 | 0.01674 | 0.01309 | 0.01929 | [-0.002484, +0.018469] | [-0.008645, +0.012268] |
| band=4to6 | low_tail | 3195 | 0.07042 | 0.09008 | 0.09196 | 0.09813 | [-0.029769, -0.012601] | [-0.035897, -0.018879] |
| band=4to6 | high_tail | 3195 | 0.06667 | 0.07824 | 0.07895 | 0.07382 | [-0.020702, -0.003543] | [-0.015527, +0.001460] |
| band=ge6 | low_tail | 1208 | 0.02980 | 0.03810 | 0.03347 | 0.04569 | [-0.012615, +0.005786] | [-0.024725, -0.006560] |
| band=ge6 | high_tail | 1208 | 0.18543 | 0.20876 | 0.23741 | 0.18426 | [-0.074596, -0.028636] | [-0.020818, +0.023655] |

Low tail means<=1 corner; high tail>=10. High-band10+ frequency18.54% versus original predicted23.74% and joint18.43%: joint largely repairs this pooled tail overprediction. Low-band<=1 frequency21.92% versus original21.68% and joint18.68%: joint underestimates that low-tail frequency. Tail mean calibration and tail Brier need not agree because discrimination also contributes to proper scores. Complete tail Brier differences/intervals and baseline error intervals are in results.json.

| Overall line | Observed over | Fixed180 p | Original p | Joint p |
|---|---:|---:|---:|---:|
| 3.5 | 0.675807 | 0.664221 | 0.661708 | 0.649551 |
| 4.5 | 0.534422 | 0.527047 | 0.527022 | 0.510168 |
| 5.5 | 0.405679 | 0.401205 | 0.403943 | 0.384214 |
| 6.5 | 0.292493 | 0.294912 | 0.299905 | 0.279392 |

Joint underpredicts pooled over-event frequency on all four lines despite better Brier. This is a concrete reason to inspect reliability before interpreting improved proper scores as calibrated probabilities.

## Provenance, limits and next research

All nine E0 bytes match the audit hashes at liammcdade/Footballdata commit84eb7985dc4b842a62f2169eb6a5c2986834932f. That mirror’s E1 hash matches do not independently certify E0 bytes. Raw provider files remain outside Git; results contain provenance and derived predictions. No new provider requests. AvgH/D/A only,2019 onward; earlier BbAv fields are not spliced. Missing exact quote timestamps limit fixed-horizon interpretations. The Newcastle–WestHam2021-08-15 shot inconsistency is irrelevant to these models and retained for valid corners/odds.

EPL prior ModelFC exposure, today’s repeated architecture work, different odds/strength distributions, schedule/team composition and corner processes prevent pristine-holdout or causal claims. No new promotion criterion was inferred from favorable scores. All original Championship failed-gate records remain unchanged.

**Next research recommendation:** use these saved predictions for a separately specified reliability-versus-discrimination diagnostic, focusing on post-training2023 onward line probabilities by venue and the low forecast band. The joint model’s pooled over-event underprediction and low-tail miss are specific targets for understanding; do not refit an intercept or choose another gamma on these outcomes. Both frozen adjustments warrant further research, but this transfer does not repair their original Championship acceptance failures or prove future Championship performance.

## Reproducibility and CI limitation

Local saved environment: Python3.12.14, NumPy2.5.3, SciPy1.18.1.102 tests passed. Added tests verify explicit league isolation, E0/E1 numerical equality on identical synthetic histories, same-date outcome isolation and frozen transform behavior. Code/spec/base-helper/coefficient artifact hashes were recorded before scoring and rechecked after.

**Clean-install caveat:** the parent reported [published-branch CI run37032908985](https://github.com/stevengalvis/deepfc/actions/runs/37032908985) at1dab722 failed collection with five missing-NumPy errors. Inspected configuration confirms CI installs only `.[test]`, which supplies pytest; project runtime dependencies are empty. Research dependencies NumPy/SciPy are pinned in experiments/joint_strength_requirements.txt but CI does not install that file. Local success therefore does not imply clean-install reproducibility.

Minimal proposed fix, subject to separate approval: have the research-branch CI install `-r experiments/joint_strength_requirements.txt` alongside `-e ".[test]"`, and document that research setup. This preserves a dependency-light production package. An optional research extra is an alternative, not an additional change made here. No packaging/workflow edit or push was made in this task.

```bash
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.e0_transfer > experiments/results/e0_transfer/run.txt
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m pytest -q
```

Full per-season×band results and all paired intervals are in results.json; predictions.csv preserves per-observation means, outcomes, dispersion and signed strength for reproduction. Decision: historical_transfer_description_only_no_promotion.
