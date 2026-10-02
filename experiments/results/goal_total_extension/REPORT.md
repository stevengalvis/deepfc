# Goal-total odds extension: incremental evidence inconclusive

**Do not promote this extension.** It slightly improves aggregate line-probability Brier over the saved joint model, but the paired intervals cross zero in Championship and in EPL after May 2023. Count NLL provides no consistent incremental gain; EPL MAE worsens. Low-baseline-mean calibration deteriorates in both leagues. This is one completed, frozen experiment, not evidence that goals cause corners or that no goal-market signal could exist. No variants were tried.

## Source/schema audit and coverage

Used only `Avg>2.5` and `Avg<2.5` plus the existing `AvgH/D/A`, all finite decimal prices >1. All 3,864 Championship and 2,660 EPL source fixtures from 2019/20 onward have valid required quotes. No invalid-quote exclusions, bookmaker substitution, closing fields, or imputation. Earlier 2017/18–2018/19 files have `BbAv` fields and serve only as corner-history warm-up; their odds are not spliced into the model.

The provider distinguishes non-C pre-closing snapshots from C closing odds and reports Oddsportal replacing Betbrain from 2019/20. It also reports excluding Pinnacle from market averages from July 23, 2025 because of stale API quotes: consistent column names do not guarantee a constant bookmaker pool. Exact quote timestamps are unavailable; fixed-time pre-kickoff availability is unverified. [Football-Data documentation](https://football-data.co.uk/data.php), checked October 2, 2026.

E1 files match previously archived primary hashes; EPL files retain pinned mirror hashes without independent primary-file verification. No historical data was downloaded. Full per-file paths/hashes, schema, validity counts and feature ranges are in `audit.json`.

| League | Source season | Source fixtures | Valid required pairs/triplets | Normalized over probability range |
|---|---|---:|---:|---|
| E1 | 2019/20 | 552 | 552 | 0.3551–0.6432 |
| E1 | 2020/21 | 552 | 552 | 0.3413–0.5893 |
| E1 | 2021/22 | 552 | 552 | 0.3461–0.6596 |
| E1 | 2022/23 | 552 | 552 | 0.3634–0.5725 |
| E1 | 2023/24 | 552 | 552 | 0.3753–0.6893 |
| E1 | 2024/25 | 552 | 552 | 0.3093–0.6651 |
| E1 | 2025/26 | 552 | 552 | 0.3587–0.7080 |
| E0 | 2019/20 | 380 | 380 | 0.3534–0.7862 |
| E0 | 2020/21 | 380 | 380 | 0.3558–0.7280 |
| E0 | 2021/22 | 380 | 380 | 0.3759–0.7495 |
| E0 | 2022/23 | 380 | 380 | 0.3840–0.7665 |
| E0 | 2023/24 | 380 | 380 | 0.4173–0.7909 |
| E0 | 2024/25 | 380 | 380 | 0.4025–0.7875 |
| E0 | 2025/26 | 380 | 380 | 0.3864–0.7238 |

Eligible evaluation coverage is unchanged: Championship 3,198 team observations / 1,599 fixtures; EPL 5,142 / 2,571. These retain the existing history-eligibility exclusions (Championship 57 of 1,656 later source fixtures; EPL 89 of 2,660). EPL through May 2023 is 2,922 / 1,461, last date May 28, 2023; after May 2023 is 2,220 / 1,110, August 11, 2023–May 24, 2026. The former is a retrospective application of later-fitted coefficients, not historically available forecasts. All history has prior research exposure.

## Frozen design and early fitting

`q=(1/over)/(1/over+1/under)`, `g=q−0.5`. This is a scoring-level probability proxy, not measured expected goals; no expected-goals inversion. Five-parameter NB mean: `mu=fixed180*exp(a_home I_home+a_away I_away+h log(fixed180/5)+beta s+delta g)`. The same g acts on both teams; existing 1X2 s is signed by venue. All five coefficients are jointly fitted, so the incremental comparison assesses the whole nested extension, not a causal isolated coefficient. Dispersion remains the earlier-history fixed180 dispersion. Equal-observation NB NLL plus half the squared coefficient norm; unit ridge, no penalty/feature/centering search.

The feature/transform and fitting rule were chosen before candidate scores. Two chronological folds assess development performance: each refits both joint and extension only on earlier Championship observations, then scores a full later season. These folds do not select variants or impose a result-dependent gate. Final extension fit uses 4,224 team observations before July 1, 2023, last date May 8, 2023. No EPL or later-period fit. Coefficients and their hash were saved before later evaluation.

| Early held-out fold | Earlier training team n | Held-out team n | Brier delta vs fold joint [95% CI] | NLL delta | MAE delta |
|---|---:|---:|---|---:|---:|
| 2021/22 | 2076 | 1064 | +0.000291810 [-0.000401587, +0.001144338] | +0.000818819 | +0.001608001 |
| 2022/23 | 3140 | 1084 | -0.000253768 [-0.000641991, +0.000123677] | -0.000960939 | -0.004481514 |

Early folds give mixed signs; full paired metrics/intervals are in `fit.json`. There is no strong early out-of-fold gain being hidden by the final fit.

| Final coefficient | Value |
|---|---:|
| a_home | 0.008354417576 |
| a_away | -0.004653377448 |
| gamma_minus_one | -0.719774200644 |
| beta_1x2 | 0.427883223589 |
| delta_goal | 0.447301285208 |

Final gamma=1+h=0.280225799356. A 0.1 rise in normalized over probability multiplies fitted corner mean by 1.045746, holding other inputs fixed; this is a fitted association. Final independent gradient max 1.1e-09; minimum Hessian eigenvalue 33.890821; solver certified in 3 iterations. Fold certificates also passed.

## Overall accuracy on identical cohorts

Primary contrast is extension minus saved joint, not merely extension minus fixed180. Lower Brier/NLL/MAE is better. Brier equally weights lines 3.5, 4.5, 5.5 and 6.5 and both sides. Paired 28-day calendar blocks, 10,000 resamples, seed 7, pointwise 95% intervals preserve fixture pairing. They omit fitting/selection uncertainty and are exploratory, not a multiplicity-adjusted confirmation.

| Cohort | Model | Brier | Count NLL | Mean MAE |
|---|---|---:|---:|---:|
| league=E1 | fixed180 | 0.209179305 | 2.371234959 | 2.146942371 |
| league=E1 | joint | 0.206365044 | 2.356454717 | 2.101047128 |
| league=E1 | goal | 0.205995111 | 2.356225992 | 2.102615675 |
| league=E0 | fixed180 | 0.208713116 | 2.381498716 | 2.195720731 |
| league=E0 | joint | 0.204667217 | 2.364238754 | 2.142337484 |
| league=E0 | goal | 0.204508580 | 2.366203729 | 2.161708057 |
| league=E0/era=through_May2023 | fixed180 | 0.207683383 | 2.369389772 | 2.166677617 |
| league=E0/era=through_May2023 | joint | 0.203552390 | 2.353248852 | 2.111789452 |
| league=E0/era=through_May2023 | goal | 0.203710841 | 2.356237762 | 2.132704605 |
| league=E0/era=after_May2023 | fixed180 | 0.210068468 | 2.397436705 | 2.233947749 |
| league=E0/era=after_May2023 | joint | 0.206134570 | 2.378703842 | 2.182545298 |
| league=E0/era=after_May2023 | goal | 0.205558578 | 2.379321096 | 2.199882871 |

| Cohort | Reference | Metric | Extension − reference | 95% CI |
|---|---|---|---:|---|
| league=E1 | joint | brier | -0.000369933 | [-0.000785947, +0.000000658] |
| league=E1 | joint | nll | -0.000228725 | [-0.001526842, +0.000910553] |
| league=E1 | joint | mae | +0.001568547 | [-0.003087251, +0.006082641] |
| league=E1 | fixed180 | brier | -0.003184194 | [-0.005363833, -0.001061499] |
| league=E1 | fixed180 | nll | -0.015008967 | [-0.021990745, -0.008131817] |
| league=E1 | fixed180 | mae | -0.044326696 | [-0.065268662, -0.022427540] |
| league=E0 | joint | brier | -0.000158636 | [-0.000816380, +0.000469813] |
| league=E0 | joint | nll | +0.001964975 | [-0.000242607, +0.004132397] |
| league=E0 | joint | mae | +0.019370573 | [+0.012140013, +0.026547169] |
| league=E0 | fixed180 | brier | -0.004204536 | [-0.005709742, -0.002737922] |
| league=E0 | fixed180 | nll | -0.015294987 | [-0.020710280, -0.009936386] |
| league=E0 | fixed180 | mae | -0.034012674 | [-0.048379515, -0.020201614] |
| league=E0/era=through_May2023 | joint | brier | +0.000158451 | [-0.000588441, +0.000886958] |
| league=E0/era=through_May2023 | joint | nll | +0.002988910 | [+0.000126158, +0.005727308] |
| league=E0/era=through_May2023 | joint | mae | +0.020915152 | [+0.012439842, +0.029643551] |
| league=E0/era=through_May2023 | fixed180 | brier | -0.003972542 | [-0.005719831, -0.002088929] |
| league=E0/era=through_May2023 | fixed180 | nll | -0.013152010 | [-0.019655359, -0.006263170] |
| league=E0/era=through_May2023 | fixed180 | mae | -0.033973012 | [-0.049181028, -0.017423941] |
| league=E0/era=after_May2023 | joint | brier | -0.000575992 | [-0.001708091, +0.000532889] |
| league=E0/era=after_May2023 | joint | nll | +0.000617255 | [-0.003068075, +0.004122931] |
| league=E0/era=after_May2023 | joint | mae | +0.017337572 | [+0.004340347, +0.029933824] |
| league=E0/era=after_May2023 | fixed180 | brier | -0.004509889 | [-0.007133390, -0.001977704] |
| league=E0/era=after_May2023 | fixed180 | nll | -0.018115609 | [-0.027445517, -0.009157033] |
| league=E0/era=after_May2023 | fixed180 | mae | -0.034064878 | [-0.060729746, -0.009430602] |

Championship incremental Brier upper bound is +0.000000658: it narrowly crosses zero, and must not be rounded into a superiority claim. Both 14- and 56-day sensitivities also cross zero. The point improvement 0.000370 is below the previously proposed, unapproved 0.001 materiality reference. EPL post-May point improvement 0.000576 also falls below that reference and has a wider interval crossing zero. Stronger fixed180 comparisons do not prove value beyond joint. EPL count NLL worsens on point estimates and MAE worsens with an interval wholly above zero; that MAE describes predicted means, not optimal conditional medians.

| League | Block days | Incremental Brier 95% CI |
|---|---:|---|
| E1 | 14 | [-0.000804254, +0.000044138] |
| E1 | 56 | [-0.000847037, +0.000065514] |
| E0 | 14 | [-0.000751720, +0.000427139] |
| E0 | 56 | [-0.000891453, +0.000568960] |

## Seasons, venues and baseline-defined bands

Bias = actual minus predicted. Band membership always uses fixed180, never the candidate mean. Full NLL/MAE/line and tail metrics with uncertainty for all slices, season×band, era×venue and era×band are in `results.json`.

| Slice | Team n | Fixed180 Brier | Joint Brier | Extension Brier | Incremental Brier CI | Joint bias | Extension bias |
|---|---:|---:|---:|---:|---|---:|---:|
| league=E1/season=2023 | 1048 | 0.210451 | 0.210822 | 0.210193 | [-0.001594367, +0.000332238] | +0.229937 | +0.132275 |
| league=E1/venue=home | 1599 | 0.214892 | 0.212627 | 0.211868 | [-0.001426243, -0.000122057] | +0.294453 | +0.243001 |
| league=E1/band=4to6 | 2112 | 0.216950 | 0.212036 | 0.211656 | [-0.000911576, +0.000184392] | +0.144544 | +0.110279 |
| league=E1/venue=away | 1599 | 0.203467 | 0.200103 | 0.200122 | [-0.000649471, +0.000722563] | -0.011173 | -0.061437 |
| league=E1/band=lt4 | 369 | 0.170646 | 0.169017 | 0.170474 | [+0.000460177, +0.002538381] | -0.282712 | -0.363340 |
| league=E1/band=ge6 | 717 | 0.206121 | 0.208881 | 0.207602 | [-0.002388815, -0.000214838] | +0.351476 | +0.267062 |
| league=E1/season=2024 | 1066 | 0.203762 | 0.200060 | 0.199773 | [-0.000822151, +0.000111804] | +0.023568 | +0.011465 |
| league=E1/season=2025 | 1084 | 0.213277 | 0.208256 | 0.208055 | [-0.000713573, +0.000184913] | +0.172386 | +0.128667 |
| league=E0/season=2019 | 702 | 0.209246 | 0.206709 | 0.206423 | [-0.001702834, +0.001338561] | +0.147757 | -0.024193 |
| league=E0/venue=home | 2571 | 0.208732 | 0.205720 | 0.204697 | [-0.002018069, +0.000000106] | +0.135276 | -0.081409 |
| league=E0/band=lt4 | 739 | 0.159095 | 0.156953 | 0.160821 | [+0.002179243, +0.005514711] | -0.269411 | -0.490074 |
| league=E0/venue=away | 2571 | 0.208694 | 0.203615 | 0.204320 | [-0.000201931, +0.001587381] | +0.052870 | -0.125621 |
| league=E0/band=ge6 | 1208 | 0.203325 | 0.198516 | 0.196630 | [-0.003381508, -0.000350484] | +0.166906 | -0.158171 |
| league=E0/band=4to6 | 3195 | 0.222227 | 0.218029 | 0.217592 | [-0.001134231, +0.000248662] | +0.150609 | +0.006560 |
| league=E0/season=2020 | 740 | 0.208922 | 0.204444 | 0.204198 | [-0.002075955, +0.001438158] | +0.031485 | -0.098161 |
| league=E0/season=2021 | 740 | 0.208632 | 0.203001 | 0.203551 | [-0.000853287, +0.001821159] | +0.134053 | -0.010694 |
| league=E0/season=2022 | 740 | 0.204013 | 0.200218 | 0.200810 | [-0.000410705, +0.001773415] | +0.015129 | -0.142359 |
| league=E0/season=2023 | 740 | 0.206240 | 0.204317 | 0.202492 | [-0.003147300, -0.000523206] | +0.306260 | +0.004118 |
| league=E0/season=2024 | 740 | 0.210659 | 0.205103 | 0.206018 | [-0.001657157, +0.003056084] | +0.016752 | -0.275509 |
| league=E0/season=2025 | 740 | 0.213306 | 0.208984 | 0.208166 | [-0.002305453, +0.000500437] | +0.009833 | -0.173735 |

All three later Championship seasons have favorable incremental Brier point estimates, but EPL seasons are mixed (2021/22, 2022/23 and 2024/25 worsen). Both leagues show home gains with away deterioration on point estimates. Championship low-band bias worsens from −0.283 to −0.363, while high-band bias improves from +0.351 to +0.267. EPL low-band bias worsens from −0.269 to −0.490; high-band bias reverses from +0.167 to −0.158. Aggregate improvement therefore does not resolve conditional calibration. No every-season sign veto or relative-bias-halving gate has been imposed.

## Tail calibration

Events are <=1 and >=10 corners. Errors are observed minus predicted probabilities. All models and intervals are retained in the machine-readable results.

| Slice | Tail | Observed | Fixed180 p | Joint p | Extension p | Extension error 95% CI |
|---|---|---:|---:|---:|---:|---|
| league=E1 | low_tail | 0.072233 | 0.076739 | 0.080446 | 0.078283 | [-0.014531134, +0.002250247] |
| league=E1 | high_tail | 0.081614 | 0.087563 | 0.073601 | 0.076776 | [-0.005108428, +0.015087091] |
| league=E1/band=4to6 | low_tail | 0.072917 | 0.076698 | 0.082159 | 0.080574 | [-0.016302582, +0.001872311] |
| league=E1/band=4to6 | high_tail | 0.070549 | 0.067314 | 0.062060 | 0.063950 | [-0.005759913, +0.019518994] |
| league=E1/band=lt4 | low_tail | 0.146341 | 0.167509 | 0.141569 | 0.134254 | [-0.029236376, +0.054614104] |
| league=E1/band=lt4 | high_tail | 0.013550 | 0.014304 | 0.022304 | 0.024270 | [-0.021978760, +0.003164119] |
| league=E1/band=ge6 | low_tail | 0.032078 | 0.030145 | 0.043944 | 0.042732 | [-0.024581857, +0.003454852] |
| league=E1/band=ge6 | high_tail | 0.149233 | 0.184911 | 0.133997 | 0.141577 | [-0.018848292, +0.040854075] |
| league=E0 | low_tail | 0.082264 | 0.093003 | 0.098550 | 0.090034 | [-0.014257817, -0.001139421] |
| league=E0 | high_tail | 0.087904 | 0.100063 | 0.091928 | 0.104518 | [-0.024465924, -0.008637514] |
| league=E0/band=lt4 | low_tail | 0.219215 | 0.195415 | 0.186784 | 0.164707 | [+0.028588050, +0.080238974] |
| league=E0/band=lt4 | high_tail | 0.020298 | 0.016738 | 0.019288 | 0.024728 | [-0.014147252, +0.006895889] |
| league=E0/era=through_May2023 | low_tail | 0.079055 | 0.092364 | 0.097944 | 0.091290 | [-0.020973281, -0.003327245] |
| league=E0/era=through_May2023 | high_tail | 0.083162 | 0.098651 | 0.091511 | 0.101104 | [-0.026291164, -0.009757010] |
| league=E0/band=ge6 | low_tail | 0.029801 | 0.038096 | 0.045693 | 0.040665 | [-0.019611852, -0.001562781] |
| league=E0/band=ge6 | high_tail | 0.185430 | 0.208759 | 0.184262 | 0.212321 | [-0.048707376, -0.004595425] |
| league=E0/band=4to6 | low_tail | 0.070423 | 0.090076 | 0.098127 | 0.091428 | [-0.029334333, -0.012098796] |
| league=E0/band=4to6 | high_tail | 0.066667 | 0.078240 | 0.073819 | 0.082214 | [-0.023877442, -0.006940152] |
| league=E0/era=after_May2023 | low_tail | 0.086486 | 0.093845 | 0.099348 | 0.088381 | [-0.011279733, +0.007626008] |
| league=E0/era=after_May2023 | high_tail | 0.094144 | 0.101922 | 0.092477 | 0.109011 | [-0.029210802, -0.000071956] |

In EPL low-band fixtures, <=1 observed frequency is 21.92%; joint predicts 18.68%, extension 16.47%, moving further away. In EPL high-band fixtures, >=10 occurs 18.54%; joint predicts 18.43%, extension 21.23%, losing the close tail agreement. Championship high-tail calibration improves in the high band, but low-band errors worsen. These tradeoffs argue against treating the extension as a broad calibration repair.

## Validation, preservation and recommendation

117 tests passed (105 inherited, 12 new). Tests cover strict normalization/quote rejection without fallback, same-sign venue feature and centering, NB likelihood/gradient/Hessian checks including Poisson limit and nesting, future/EPL exclusion, and identical-model contrasts. All frozen source/code/spec/audit and fitted-coefficient hashes verified. Fixed180 and saved joint per-row Brier/NLL/MAE reproduce prior predictions within 1e-12. No earlier model result, production source or dependency was edited.

```bash
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.goal_total_extension audit
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.goal_total_extension train
# Save fit.json/hash before later evaluation.
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.goal_total_extension evaluate
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m pytest -q
```

Reproduction uses the saved environment and pinned local input paths, with NumPy/SciPy pins in `experiments/joint_strength_requirements.txt`. Raw source data is not committed. No startup/dependency blocker arose.

**Conclusion: incremental probability benefit is inconclusive, and calibration/count tradeoffs are unfavorable enough that this experiment does not justify replacing joint calibration.** Preserve it as a single tested historical hypothesis. Do not tune to these later results or claim a deployable fixed-time or profitable betting model. No further model experiment was run; no push, PR or merge.
