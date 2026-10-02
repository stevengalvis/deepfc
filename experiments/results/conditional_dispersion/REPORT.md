# Conditional dispersion: gains come from estimation, not useful conditioning

**No useful incremental odds-conditioning gain was established.** The likelihood-fitted constant NB dispersion (B) improves aggregate line Brier relative to the saved moment dispersion (A); the conditional arm (C) adds only a few millionths. Both new arms worsen low-band EPL tail calibration. Keep these as exploratory research findings; do not promote C or silently replace A with B. Means and mean-based errors are exactly unchanged.

## What was tested

A uses the saved leading joint-calibration mean and saved pooled earlier-history moment dispersion. B uses the exact same mean with one likelihood-fitted constant dispersion. C uses that same mean with `alpha=exp(a+b*z)`, `z=abs(p_home−p_away)−0.5`, where probabilities normalize inverse pre-closing AvgH/D/A. Both fixture sides share z. C adds the fixed penalty `0.5*(b/0.25)^2`; a is unpenalized. Bounds are alpha in[1e−4,1] over the entire z domain. No feature, penalty, sign, league or later-period tuning.

NB parameterization is `Var(Y)=mu+alpha*mu²`, shape `1/alpha`. Full conditional count likelihood includes every shape-dependent term. The equivalent integer-count product expression avoids near-Poisson gamma-subtraction cancellation. Inference and optimization never refit or adjust a mean.

The idea was motivated by the total-corner shape regression in [Yip et al., full manuscript](https://arxiv.org/html/2112.13001), not evidence for team-corner performance or profitability. This is a team-corner extrapolation. The previous marginal-moment dispersion rejection, goal-total result and residual-persistence decision remain unchanged. Geometric-Poisson and NGBoost were not tested. See the preserved planning document and execution registration for the pre-score choices.

## Chronology, coverage and numerical evidence

Training means are temporal out-of-fold forecasts:2021/22 uses the saved joint component fitted before July2021;2022/23 uses the component fitted before July2022. B/C development fits use1,064 team observations from2021/22, then assess1,084 observations in2022/23. Final B/C coefficients use the pooled2,148 OOF observations, last outcome May8,2023. Final joint means used for later evaluation were already saved, fitted before July2023. No in-sample final-mean residuals were used to estimate dispersion. Transfer from fold components to the final component remains an explicit calibration-transfer assumption.

Both early coefficient fits, code/spec/input hashes and the final fitted hash were saved before later evaluation. No new data downloads, no invalid1X2 quote exclusions, and no cohort changes. Later E1:3,198 team observations/1,599 fixtures; EPL:5,142/2,571, split into2,922/1,461 through May2023 and2,220/1,110 afterward. The earlier EPL period uses later-estimated parameters and is retrospective. All historical periods have prior research exposure; quote timestamps remain unavailable and EPL source hashes are mirror-pinned rather than independently primary-verified.

| Fit period | B intercept | B alpha | C intercept | C slope | Training team n |
|---|---:|---:|---:|---:|---:|
| 2021/22 development | -2.610162942799 | 0.073522562815 | -2.633219285347 | -0.087788995268 | 1064 |
| 2021/22+2022/23 final | -2.661460822406 | 0.069846114414 | -2.674175472508 | -0.044213669642 | 2148 |

Final C full-domain dispersion ratio (max imbalance versus zero imbalance) is exp(b)=0.956750; the fitted change is small and downward, not a reproduction of a total-corner effect. All three fixed numerical starts agreed in objective to reported double precision. B score max=4.1e-13; C start score maxima range 1.23e-14–2.73e-08, below the frozen1e−6 criterion. All finite-difference checks and positive-Hessian checks passed; no bounds were hit. Two C starts used all30 polishing iterations toward the stricter internal1e−8 target but passed the registered certification threshold. No objective, bound or solver fallback change was made.

| Early2022/23 comparison | Brier delta |95% CI| NLL delta |95% CI|
|---|---:|---|---:|---|
| C_minus_B | -0.000001980 | [-0.000011305, +0.000008541] | +0.000067079 | [-0.000046088, +0.000190485] |
| B_minus_A | -0.000112887 | [-0.000243335, +0.000032898] | -0.001200309 | [-0.003393377, +0.000968749] |
| C_minus_A | -0.000114866 | [-0.000246374, +0.000033414] | -0.001133229 | [-0.003258021, +0.000958713] |

Early assessment offered no substantial conditioning gain. Per plan it did not choose a different arm or trigger tuning.

## Overall results: all three arms

Brier averages the four lines3.5/4.5/5.5/6.5 and both sides equally. Count NLL uses the full NB probability. Lower loss is better. Intervals are paired28-day calendar-block bootstrap intervals,10,000 draws seed7, with identical draws across comparisons and both sides preserved. They are conditional on fitted models and omit parameter/research-selection uncertainty.

| Cohort | Arm | Brier | Count NLL | Mean MAE (unchanged) |
|---|---|---:|---:|---:|
| Championship later | A | 0.206365044 | 2.356454717 | 2.101047128 |
| Championship later | B | 0.205946019 | 2.355558721 | 2.101047128 |
| Championship later | C | 0.205943215 | 2.355566042 | 2.101047128 |
| EPL full (mixed chronology) | A | 0.204667217 | 2.364238754 | 2.142337484 |
| EPL full (mixed chronology) | B | 0.203937933 | 2.357608048 | 2.142337484 |
| EPL full (mixed chronology) | C | 0.203931253 | 2.357623288 | 2.142337484 |
| EPL through May2023 (retrospective) | A | 0.203552390 | 2.353248852 | 2.111789452 |
| EPL through May2023 (retrospective) | B | 0.202775891 | 2.344915170 | 2.111789452 |
| EPL through May2023 (retrospective) | C | 0.202768598 | 2.344937930 | 2.111789452 |
| EPL after May2023 | A | 0.206134570 | 2.378703842 | 2.182545298 |
| EPL after May2023 | B | 0.205467433 | 2.374314620 | 2.182545298 |
| EPL after May2023 | C | 0.205461558 | 2.374319962 | 2.182545298 |

| Cohort | Comparison | Brier delta [95% CI] | Count NLL delta [95% CI] |
|---|---|---|---|
| Championship later | C_minus_B | -0.000002805 [-0.000007350, +0.000001747] | +0.000007321 [-0.000033525, +0.000051154] |
| Championship later | B_minus_A | -0.000419025 [-0.000570955, -0.000281185] | -0.000895996 [-0.003132190, +0.001378497] |
| Championship later | C_minus_A | -0.000421829 [-0.000576794, -0.000281451] | -0.000888675 [-0.003141377, +0.001389012] |
| EPL full (mixed chronology) | C_minus_B | -0.000006681 [-0.000012086, -0.000001390] | +0.000015240 [-0.000031448, +0.000063501] |
| EPL full (mixed chronology) | B_minus_A | -0.000729283 [-0.001111695, -0.000354770] | -0.006630706 [-0.010383567, -0.002943273] |
| EPL full (mixed chronology) | C_minus_A | -0.000735964 [-0.001121698, -0.000357039] | -0.006615466 [-0.010386706, -0.002918308] |
| EPL through May2023 (retrospective) | C_minus_B | -0.000007293 [-0.000013850, -0.000000639] | +0.000022761 [-0.000025732, +0.000070332] |
| EPL through May2023 (retrospective) | B_minus_A | -0.000776499 [-0.001235363, -0.000351929] | -0.008333683 [-0.012587655, -0.004193121] |
| EPL through May2023 (retrospective) | C_minus_A | -0.000783792 [-0.001245962, -0.000355694] | -0.008310922 [-0.012586681, -0.004157304] |
| EPL after May2023 | C_minus_B | -0.000005875 [-0.000014830, +0.000002700] | +0.000005342 [-0.000079637, +0.000097722] |
| EPL after May2023 | B_minus_A | -0.000667138 [-0.001336484, -0.000007882] | -0.004389221 [-0.011180107, +0.002139796] |
| EPL after May2023 | C_minus_A | -0.000673012 [-0.001350439, -0.000008746] | -0.004383880 [-0.011199060, +0.002180984] |

C−B is−0.000002805 in E1 and−0.000005875 after May2023 in EPL, with both intervals crossing zero. Full EPL C−B is−0.000006681 with a negative interval, but that mixes chronology and remains tiny; it is not hidden or presented as material evidence. C−B NLL point estimates worsen slightly, with intervals crossing zero throughout. Nearly all aggregate gains over A come from the likelihood estimator change.

B−A E1 Brier is−0.000419 with a favorable interval; B−A post-May EPL is−0.000667 and only narrowly favorable under28days. Count NLL improves on point estimates, but E1 and post-May EPL intervals cross zero. Full EPL NLL improves with a negative interval, heavily informed by retrospective early EPL. Mean bias/MAE cannot improve and were not used as acceptance gates.

| Cohort | Block days | C−B Brier95% CI | B−A Brier95% CI | C−A Brier95% CI |
|---|---:|---|---|---|
| Championship later | 56 | [-0.000007272, +0.000001405] | [-0.000552254, -0.000299479] | [-0.000555670, -0.000301344] |
| Championship later | 84 | [-0.000006850, +0.000001664] | [-0.000572755, -0.000279718] | [-0.000577149, -0.000280550] |
| EPL full (mixed chronology) | 56 | [-0.000012049, -0.000001208] | [-0.001156431, -0.000310421] | [-0.001167635, -0.000313076] |
| EPL full (mixed chronology) | 84 | [-0.000011565, -0.000001609] | [-0.001049554, -0.000389653] | [-0.001058076, -0.000393197] |
| EPL after May2023 | 56 | [-0.000015517, +0.000004092] | [-0.001395291, +0.000075908] | [-0.001407006, +0.000077105] |
| EPL after May2023 | 84 | [-0.000014700, +0.000002590] | [-0.001290283, -0.000046521] | [-0.001300381, -0.000049347] |

At56days, the post-May EPL B−A and C−A intervals cross zero. This dependence-sensitivity disagreement makes even the directional transfer claim inconclusive under the frozen interpretation. C−B remains uncertain in E1 and post-May EPL for both sensitivities.

## Dispersion ranges and unchanged means

| Cohort | A alpha range | B alpha | C alpha range |28d blocks|
|---|---|---:|---|---:|
| Championship later | 0.086396–0.098174 | 0.069846 | 0.068101–0.070505 | 33 |
| EPL full (mixed chronology) | 0.126995–0.141247 | 0.069846 | 0.067835–0.070505 | 80 |
| EPL through May2023 (retrospective) | 0.126995–0.135563 | 0.069846 | 0.067835–0.070505 | 45 |
| EPL after May2023 | 0.132259–0.141247 | 0.069846 | 0.067876–0.070505 | 35 |

B/C substantially reduce the EPL dispersion inherited from pooled marginal moments. Marginal variation includes changing/team-specific mean levels, so conditional-likelihood estimation can reduce it; this explanation is consistent with the design but not a causal diagnosis. Remaining mean misspecification can still affect the fitted shape. Candidate numerical-bound rates are zero in every slice. Mean, bias, MAE and squared error are exactly identical for every one of8,340 rows; A reproduces prior saved joint scores within1e−12.

## Season, venue and fixed bands

| Slice | Team n | A Brier | B Brier | C Brier | B−A delta | C−B delta [95% CI] |
|---|---:|---:|---:|---:|---:|---|
| league=E1/season=2023 | 1048 | 0.2108222 | 0.2104763 | 0.2104796 | -0.0003459 | +0.000003336 [-0.000003099, +0.000009680] |
| league=E1/venue=home | 1599 | 0.2126273 | 0.2120134 | 0.2120089 | -0.0006139 | -0.000004516 [-0.000012994, +0.000004026] |
| league=E1/band=4to6 | 2112 | 0.2120361 | 0.2117082 | 0.2117048 | -0.0003279 | -0.000003380 [-0.000006247, -0.000000391] |
| league=E1/strength_band=lt0.2 | 1720 | 0.2173044 | 0.2170291 | 0.2170323 | -0.0002753 | +0.000003213 [+0.000000447, +0.000005988] |
| league=E1/venue=away | 1599 | 0.2001028 | 0.1998787 | 0.1998776 | -0.0002241 | -0.000001094 [-0.000004708, +0.000002925] |
| league=E1/strength_band=0.2to0.5 | 1238 | 0.1993209 | 0.1986864 | 0.1986749 | -0.0006345 | -0.000011464 [-0.000015868, -0.000007437] |
| league=E1/band=lt4 | 369 | 0.1690171 | 0.1688919 | 0.1688867 | -0.0001252 | -0.000005227 [-0.000009687, -0.000000757] |
| league=E1/band=ge6 | 717 | 0.2088812 | 0.2080426 | 0.2080427 | -0.0008386 | +0.000000136 [-0.000019402, +0.000018014] |
| league=E1/strength_band=ge0.5 | 240 | 0.1643025 | 0.1639647 | 0.1639634 | -0.0003378 | -0.000001265 [-0.000048394, +0.000044451] |
| league=E1/season=2024 | 1066 | 0.2000598 | 0.1995552 | 0.1995507 | -0.0005046 | -0.000004564 [-0.000014180, +0.000004974] |
| league=E1/season=2025 | 1084 | 0.2082565 | 0.2078509 | 0.2078439 | -0.0004056 | -0.000007010 [-0.000013073, -0.000001546] |
| league=E0/season=2019 | 702 | 0.2067088 | 0.2058438 | 0.2058474 | -0.0008650 | +0.000003611 [-0.000006421, +0.000014434] |
| league=E0/venue=home | 2571 | 0.2057197 | 0.2043953 | 0.2043827 | -0.0013244 | -0.000012675 [-0.000022029, -0.000003129] |
| league=E0/band=lt4 | 739 | 0.1569535 | 0.1567952 | 0.1567900 | -0.0001583 | -0.000005235 [-0.000009885, -0.000000688] |
| league=E0/strength_band=ge0.5 | 1162 | 0.1652904 | 0.1636336 | 0.1636062 | -0.0016568 | -0.000027398 [-0.000048736, -0.000006102] |
| league=E0/venue=away | 2571 | 0.2036147 | 0.2034805 | 0.2034798 | -0.0001342 | -0.000000687 [-0.000006349, +0.000005400] |
| league=E0/band=ge6 | 1208 | 0.1985155 | 0.1966834 | 0.1966604 | -0.0018321 | -0.000022968 [-0.000044674, -0.000001690] |
| league=E0/band=4to6 | 3195 | 0.2180293 | 0.2175849 | 0.2175840 | -0.0004444 | -0.000000857 [-0.000004104, +0.000002497] |
| league=E0/strength_band=lt0.2 | 1890 | 0.2245531 | 0.2241486 | 0.2241491 | -0.0004045 | +0.000000563 [-0.000002713, +0.000003828] |
| league=E0/strength_band=0.2to0.5 | 2090 | 0.2085770 | 0.2080697 | 0.2080680 | -0.0005073 | -0.000001713 [-0.000006826, +0.000003100] |
| league=E0/season=2020 | 740 | 0.2044440 | 0.2038437 | 0.2038349 | -0.0006004 | -0.000008766 [-0.000021315, +0.000006616] |
| league=E0/season=2021 | 740 | 0.2030007 | 0.2019819 | 0.2019736 | -0.0010189 | -0.000008298 [-0.000023653, +0.000005773] |
| league=E0/season=2022 | 740 | 0.2002180 | 0.1995917 | 0.1995766 | -0.0006263 | -0.000015159 [-0.000025274, -0.000005143] |
| league=E0/season=2023 | 740 | 0.2043168 | 0.2030293 | 0.2030171 | -0.0012875 | -0.000012264 [-0.000030783, +0.000004581] |
| league=E0/season=2024 | 740 | 0.2051027 | 0.2048301 | 0.2048285 | -0.0002726 | -0.000001586 [-0.000017701, +0.000015254] |
| league=E0/season=2025 | 740 | 0.2089842 | 0.2085428 | 0.2085391 | -0.0004414 | -0.000003773 [-0.000012647, +0.000004563] |

B has favorable Brier point estimates in every reported later season and venue; this is descriptive, not a newly imposed every-season gate. C−B switches signs in E1 and EPL early seasons and is minute everywhere. Full NLL, line/tail scores, intervals and era×band/strength/venue results are in results.json. Baseline bands use fixed180 mean, never fitted dispersion; strength bands use fixed cutoffs .2 and .5 with no post-score regrouping.

## Calibration and tail tradeoffs

Observed event minus predicted probability is signed error. Absolute-error changes compare aggregate calibration, with paired bootstrap uncertainty computed AFTER taking absolute values of each bootstrap aggregate. Narrow change intervals can occur because both arms err on the same side and the shared observed frequency cancels; individual error intervals remain in results.json.

| Cohort/slice | Event | Observed | A probability | B probability | C probability | C absolute-error change vs A [95% CI] |
|---|---|---:|---:|---:|---:|---|
| Championship later | zero | 0.018449 | 0.019197 | 0.016237 | 0.016233 | +0.001468 [-0.003087, +0.003028] |
| Championship later | low_tail | 0.072233 | 0.080446 | 0.072161 | 0.072159 | -0.008140 [-0.008649, +0.007844] |
| Championship later | high_tail | 0.081614 | 0.073601 | 0.066718 | 0.066720 | +0.006881 [+0.002543, +0.007168] |
| EPL full (mixed chronology) | zero | 0.021781 | 0.026317 | 0.018037 | 0.017996 | -0.000751 [-0.007896, +0.006537] |
| EPL full (mixed chronology) | low_tail | 0.082264 | 0.098550 | 0.077196 | 0.077102 | -0.011125 [-0.021439, +0.001812] |
| EPL full (mixed chronology) | high_tail | 0.087904 | 0.091928 | 0.075844 | 0.075778 | +0.008101 [-0.007414, +0.016262] |
| EPL through May2023 (retrospective) | zero | 0.020534 | 0.026060 | 0.018135 | 0.018093 | -0.003085 [-0.008010, +0.007359] |
| EPL through May2023 (retrospective) | low_tail | 0.079055 | 0.097944 | 0.077468 | 0.077372 | -0.017205 [-0.020740, +0.000778] |
| EPL through May2023 (retrospective) | high_tail | 0.083162 | 0.091511 | 0.076058 | 0.075991 | -0.001178 [-0.015512, +0.014707] |
| EPL after May2023 | zero | 0.023423 | 0.026657 | 0.017908 | 0.017870 | +0.002320 [-0.007086, +0.008814] |
| EPL after May2023 | low_tail | 0.086486 | 0.099348 | 0.076837 | 0.076746 | -0.003121 [-0.021268, +0.015447] |
| EPL after May2023 | high_tail | 0.094144 | 0.092477 | 0.075563 | 0.075498 | +0.016979 [-0.008448, +0.017162] |
| league=E1/band=lt4 | zero | 0.051491 | 0.037337 | 0.033028 | 0.032955 | +0.004383 [-0.004351, +0.004568] |
| league=E1/band=lt4 | low_tail | 0.146341 | 0.141569 | 0.131833 | 0.131688 | +0.009882 [-0.010203, +0.010239] |
| league=E1/band=lt4 | high_tail | 0.013550 | 0.022304 | 0.018602 | 0.018576 | -0.003728 [-0.003913, +0.003884] |
| league=E1/band=ge6 | zero | 0.008368 | 0.009294 | 0.007331 | 0.007324 | +0.000119 [-0.002060, +0.002023] |
| league=E1/band=ge6 | low_tail | 0.032078 | 0.043944 | 0.037291 | 0.037257 | -0.006687 [-0.007005, +0.006441] |
| league=E1/band=ge6 | high_tail | 0.149233 | 0.133997 | 0.125288 | 0.125209 | +0.008788 [-0.008698, +0.009187] |
| league=E0/band=lt4 | zero | 0.071719 | 0.055425 | 0.042735 | 0.042552 | +0.012873 [+0.009746, +0.013039] |
| league=E0/band=lt4 | low_tail | 0.219215 | 0.186784 | 0.161825 | 0.161470 | +0.025314 [+0.024977, +0.025641] |
| league=E0/band=lt4 | high_tail | 0.020298 | 0.019288 | 0.012040 | 0.011978 | +0.007310 [-0.007333, +0.007527] |
| league=E0/band=ge6 | zero | 0.005795 | 0.010511 | 0.005623 | 0.005597 | -0.004518 [-0.005020, +0.004600] |
| league=E0/band=ge6 | low_tail | 0.029801 | 0.045693 | 0.029417 | 0.029302 | -0.015392 [-0.016647, +0.003415] |
| league=E0/band=ge6 | high_tail | 0.185430 | 0.184262 | 0.164556 | 0.164337 | +0.019926 [-0.019765, +0.020244] |
| league=E0/era=after_May2023/band=lt4 | zero | 0.065831 | 0.054846 | 0.041596 | 0.041425 | +0.013421 [-0.008435, +0.013616] |
| league=E0/era=after_May2023/band=lt4 | low_tail | 0.225705 | 0.184704 | 0.158470 | 0.158137 | +0.026568 [+0.026171, +0.026886] |
| league=E0/era=after_May2023/band=lt4 | high_tail | 0.015674 | 0.020357 | 0.012513 | 0.012453 | -0.001462 [-0.008100, +0.008122] |
| league=E0/era=after_May2023/band=ge6 | zero | 0.001815 | 0.011043 | 0.005787 | 0.005761 | -0.005283 [-0.005395, -0.004728] |
| league=E0/era=after_May2023/band=ge6 | low_tail | 0.023593 | 0.047515 | 0.030177 | 0.030067 | -0.017448 [-0.017721, -0.010271] |
| league=E0/era=after_May2023/band=ge6 | high_tail | 0.199637 | 0.180847 | 0.160071 | 0.159862 | +0.020985 [-0.017411, +0.021364] |

Lower dispersion does not universally improve tails. Full EPL low-band <=1 absolute calibration error worsens by2.496 percentage points for B and2.531 for C; post-May EPL worsens by2.623 and2.657 points. Those pointwise paired intervals exceed the proposed2-point harm reference. Post-May EPL high-band >=10 calibration also worsens by about2.1 points on point estimates, but its interval is inconclusive. The underlying mean biases remain untouched.

| Cohort | Line | Observed over | A p | B p | C p |
|---|---|---:|---:|---:|---:|
| Championship later | 3.5 | 0.692620 | 0.670813 | 0.682244 | 0.682240 |
| Championship later | 4.5 | 0.542839 | 0.521564 | 0.528706 | 0.528713 |
| Championship later | 5.5 | 0.403064 | 0.383676 | 0.385174 | 0.385196 |
| Championship later | 6.5 | 0.279237 | 0.268884 | 0.265571 | 0.265601 |
| EPL after May2023 | 3.5 | 0.678829 | 0.648660 | 0.677438 | 0.677549 |
| EPL after May2023 | 4.5 | 0.524324 | 0.509637 | 0.528122 | 0.528212 |
| EPL after May2023 | 5.5 | 0.409459 | 0.384100 | 0.389511 | 0.389574 |
| EPL after May2023 | 6.5 | 0.295495 | 0.279624 | 0.273709 | 0.273739 |

## Interpretation against frozen research references

The .001 Brier materiality, .005 NLL harm, .001 subgroup Brier harm and .02 worsening absolute probability-calibration references remain exploratory conventions, not approved deployment risk tolerances. E1 B−A and C−A gains are smaller than .001 even at their favorable95% bounds. C−B gains in both principal cohorts are far smaller than .001 throughout their intervals. Thus the prescribed stricter material-qualification reading is not met; this does not deny a tiny improvement exists. Post-May EPL directional uncertainty varies with block width, and the low-band calibration harm reference is exceeded. No multiplicity-adjusted safety or equivalence claim is made.

**Disposition:** do not advance odds-conditioned dispersion as a useful new model on this evidence. Preserve the simpler constant-likelihood finding as a possible estimator insight, with its calibration tradeoff and insufficient transfer precision; do not promote it on these reused data. No extra family, feature or penalty was tried. Old decisions remain unchanged; no expected-profit, market-edge or team-corner proof is inferred from the paper.

## Reproduction and verification

127 tests passed (122 inherited plus5 new). Added tests cover full NB likelihood/analytic gradients/Hessian, normalization and mean including near-Poisson behavior, nested C=b0/B equivalence, convergence/bounds and future/EPL exclusion, paired inputs, mean/MAE/bias/squared-error preservation, valid ordered probabilities, and paired absolute-calibration bootstrap identity. Frozen plan/spec/code/input/fitted hashes verified. All8,340 paired observations and grouped reported metric means independently checked.

```bash
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.conditional_dispersion train
# Save fit.json hash before later evaluation.
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.conditional_dispersion evaluate
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m pytest -q
```

Saved Python3.12.14 with existing pinned NumPy/SciPy requirements. No execution/dependency blocker. Code, preserved plan, execution specification, certificates, early assessment, derived rows, all results and this report saved locally. No earlier research or production code changed; no new downloads, push, PR, merge or deployment. Private/noncommercial scope was not treated as a new dataset license or publication permission.
