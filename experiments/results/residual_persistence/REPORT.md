# Residual persistence: insufficient evidence for faster feedback

**Recommendation: stop this specific residual-feedback direction for now. Do not implement a corrected candidate.** Recent errors do not provide reliable incremental evidence that the leading joint model is adapting too slowly. The early positive attack association weakens under dependence and stable-bias checks; later effects are small, uncertain and temporally inconsistent. This does not prove that changing strength is absent or that other diagnostics could never help.

## Earlier work and distinction

DeepFC fixed180 already improved on equal-weight histories. The early-selected attack/concession shrinkage (.75/.50) later worsened Brier. ModelFC tested recent windows 5/10/20/40 and decay half-lives 30/60/90/180/365 without a global promotion. This diagnostic neither reruns that search nor retests the rejected shrinkage candidate.

[ModelFC PR42](https://github.com/stevengalvis/modelfc/pull/42) was accessible: it is a shot-feature diagnostic (Championship selected shot weight zero), not a residual-feedback correction. The accessible local branches and GitHub PR search did not identify a distinct residual-correction implementation. This is a bounded search, not proof that private/deleted/unrecorded work never occurred. See `PRIOR_REVIEW.md` for commits, source files and search scope.

## Frozen construction and chronology

For each existing-model team forecast, error is actual corners minus predicted mean. Attack history follows the scoring team; concession history follows the current opponent and records errors of teams that scored against it. Positive concession error means more corners allowed than predicted. One last-five-match average R and one preceding-fifteen average L are used, with D=R−L. The current outcome is the only horizon. No alternative windows/lags were searched.

Only strictly earlier completed eligible forecasts enter histories; date-batch updates prohibit same-day outcomes. Both histories need twenty observations in the same competition/source season, with oldest observation no more than180 days old. Histories reset every season, including early fold changes. Venues are pooled but current venue and historical venue composition are controlled. No imputation or carryover across summers. Baseline and joint use the same diagnostic rows.

Discovery uses2021/22 and2022/23 Championship forecasts made with saved fold-specific joint coefficients fitted before each season. The final joint fit is not applied to its own training observations. Later E1 uses2023/24–2025/26; EPL after May2023 is the chronology-qualified transfer period. Earlier EPL results are retrospective use of later-estimated coefficients. No component was refitted for this diagnostic. Raw and derived input hashes are inherited from pinned experiments; exact quote timestamps and independent primary-hash verification of EPL remain unavailable.

All definitions were frozen before discovery effects, and discovery.json/hash was saved before unchanged validation. All periods have prior research exposure. This is exploratory validation, not independent confirmation.

## Coverage and exclusions

| Phase/league | Existing forecast team rows | Diagnostic team rows | Fixtures | Retained |
|---|---:|---:|---:|---:|
| discovery/E1 | 2148 | 1146 | 573 | 53.4% |
| validation/E1 | 3198 | 1680 | 840 | 52.5% |
| validation/E0 | 5142 | 1838 | 919 | 35.7% |

Discovery exclusions:1,002 team rows with fewer than20 prior forecasts. Validation exclusions:4,434 with fewer than20, plus388 whose oldest last20 observation exceeds180days (176 EPL2019/20,16 EPL2021/22,196 EPL2022/23). The pandemic and2022/23 schedule interruptions reduce those samples; rules were not relaxed afterward. Earlier EPL season-level regressions2019/20(n98) and2022/23(n134) are explicitly not estimated under the frozen n>=200 rule. Post-May2023 EPL retains982 team rows/491fixtures out of2,220/1,110. Applicability is limited to established in-season histories, not new/promoted teams or early-season adaptation.

## Association models and uncertainty

Three fixed diagnostic regressions are reported for each model: (1) raw recent R association, adjusting venue and season; (2) primary D association, controlling older residual L, current fixed180 log mean and square, signed1X2 strength and square, normalized goal-over probability, current venue, historical venue fractions and season intercepts; (3) the same plus stable team/opponent fixed effects. Both attack and concession terms enter together. Fixed effects are retrospective nuisance parameters, not pre-match candidate inputs. No corrected forecasts or Brier/NLL backtest were produced.

Slopes measure subsequent error in corners per1-corner increase in a recent-minus-older residual shift, conditional on controls. Partial R² is the two recent-change terms’ IN-SAMPLE explanatory contribution beyond controls, not a prediction-score gain. Including older levels distinguishes recency from persistent bias and handles mechanical regression to the mean from subtracting L. Noisy residual estimates can attenuate slopes; forecast updating itself can absorb or reverse a recent-error relationship.

Intervals use84-day calendar-cluster sandwich estimates with finite-cluster correction and Student t degrees of freedom. Both fixture sides are clustered together. Fixed168-day and dyadic-club sensitivities address longer overlap and shared-team dependence. The principal periods have only6,8,7 calendar blocks, respectively; with168days they have4,5,5. These small numbers limit precision and reliability. Calendar blocks cannot capture arbitrary cross-block dependence. Dyadic sensitivity clusters on either club and subtracts duplicated unordered-pair contributions. No iid-match uncertainty or favorable-method selection is used.

## Primary incremental effects beyond forecast and odds

| Cohort | Model | Team n | Attack D slope [84d95% CI] | Concession D slope [84d95% CI] | Joint partial R² |
|---|---|---:|---|---|---:|
| Discovery E1 | baseline | 1146 | +0.1043 [+0.0067, +0.2020] | -0.0584 [-0.1567, +0.0399] | 0.3292% |
| Discovery E1 | joint | 1146 | +0.1096 [+0.0134, +0.2058] | -0.0726 [-0.1800, +0.0348] | 0.3840% |
| Later E1 | baseline | 1680 | +0.0290 [-0.0225, +0.0805] | +0.0467 [-0.1451, +0.2384] | 0.0591% |
| Later E1 | joint | 1680 | +0.0473 [-0.0142, +0.1089] | +0.0634 [-0.1349, +0.2617] | 0.1162% |
| EPL after May2023 | baseline | 982 | +0.0090 [-0.1851, +0.2031] | +0.0234 [-0.1546, +0.2014] | 0.0113% |
| EPL after May2023 | joint | 982 | -0.0059 [-0.2112, +0.1995] | +0.0501 [-0.1532, +0.2534] | 0.0477% |
| EPL through May2023 (retrospective) | baseline | 856 | -0.0683 [-0.2552, +0.1186] | +0.0941 [-0.1287, +0.3169] | 0.2695% |
| EPL through May2023 (retrospective) | joint | 856 | -0.0162 [-0.1917, +0.1594] | +0.1141 [-0.1171, +0.3454] | 0.2505% |
| EPL all (mixed chronology) | baseline | 1838 | -0.0219 [-0.1427, +0.0990] | +0.0543 [-0.0712, +0.1798] | 0.0677% |
| EPL all (mixed chronology) | joint | 1838 | -0.0082 [-0.1315, +0.1151] | +0.0763 [-0.0543, +0.2069] | 0.1114% |

For leading joint calibration, discovery attack slope is+.110 but later Championship is+.047 and post-May EPL−.006. The later84-day intervals are[−.014,+.109] and[−.211,+.200]. Concession slopes switch from−.073 in discovery to+.063 in later E1 and+.050 in later EPL, all with uncertain later intervals. Combined conditional explanatory contribution is only0.116% of remaining variance in later E1 and0.048% in later EPL. These are weak association magnitudes, not evidence of probability-score gains.

| Leading joint cohort | Dependence method | Attack95% CI | Concession95% CI | Groups |
|---|---|---|---|---|
| Discovery E1 | 84_day | [+0.0134, +0.2058] | [-0.1800, +0.0348] | [6] |
| Discovery E1 | 168_day | [-0.0259, +0.2452] | [-0.1353, -0.0099] | [4] |
| Discovery E1 | dyadic_team | [-0.0681, +0.2873] | [-0.2024, +0.0572] | [30, 384] |
| Later E1 | 84_day | [-0.0142, +0.1089] | [-0.1349, +0.2617] | [8] |
| Later E1 | 168_day | [-0.0305, +0.1252] | [-0.0912, +0.2180] | [5] |
| Later E1 | dyadic_team | [-0.1097, +0.2044] | [-0.0626, +0.1894] | [32, 440] |
| EPL after May2023 | 84_day | [-0.2112, +0.1995] | [-0.1532, +0.2534] | [7] |
| EPL after May2023 | 168_day | [-0.1760, +0.1643] | [-0.2257, +0.3259] | [5] |
| EPL after May2023 | dyadic_team | [-0.1739, +0.1622] | [-0.1263, +0.2265] | [25, 241] |

The early attack interval excludes zero under84-day clustering but crosses zero under168-day and dyadic-team intervals. Thus it was already fragile before later validation. Both later slopes cross zero under all three methods. The negative early concession168-day interval is not evidence for positive adaptation feedback, nor a basis for a newly selected reversal strategy.

## Calibration/stable-bias sensitivity

| Leading joint cohort | Diagnostic | Attack slope | Concession slope | Partial R² |
|---|---|---:|---:|---:|
| Discovery E1 | raw | +0.0946 | -0.0799 | 0.3392% |
| Discovery E1 | controlled | +0.1096 | -0.0726 | 0.3840% |
| Discovery E1 | team_effects | -0.0080 | -0.1498 | 0.3987% |
| Later E1 | raw | +0.0687 | +0.0698 | 0.2008% |
| Later E1 | controlled | +0.0473 | +0.0634 | 0.1162% |
| Later E1 | team_effects | -0.0097 | +0.0166 | 0.0068% |
| EPL after May2023 | raw | +0.0077 | +0.0745 | 0.1125% |
| EPL after May2023 | controlled | -0.0059 | +0.0501 | 0.0477% |
| EPL after May2023 | team_effects | -0.0800 | -0.0512 | 0.1517% |

Later E1 raw recent attack association is+.069 with84-day interval[+.024,+.114], but it becomes+.047 after forecast/odds/older-bias controls and−.010 with stable team/opponent effects. The apparent raw streak therefore does not establish changing strength. After team effects, later E1 slopes are effectively zero and EPL slopes are negative/uncertain. Short dynamic panels can induce downward bias when fixed effects and lagged errors are combined; these negative estimates must not be interpreted as a reliable anti-persistence correction. Their role is to show that stable bias and model calibration remain alternative explanations.

## Temporal and venue consistency

| Cohort/slice | Leading joint team n | Attack D slope [84d CI] | Concession D slope [84d CI] |84d blocks|
|---|---:|---|---|---:|
| discovery/E1/season=2021 | 562 | +0.0813 [-0.2126, +0.3752] | -0.0395 [-0.3151, +0.2361] | 3 |
| discovery/E1/venue=away | 573 | +0.2222 [+0.1195, +0.3248] | -0.0388 [-0.3383, +0.2607] | 6 |
| discovery/E1/venue=home | 573 | -0.0142 [-0.1925, +0.1641] | -0.1238 [-0.3331, +0.0856] | 6 |
| discovery/E1/season=2022 | 584 | +0.1214 [-0.0750, +0.3178] | -0.1032 [-0.2901, +0.0837] | 3 |
| validation/E0/season=2019 | 98 | not estimated: insufficient n | — | — |
| validation/E0/venue=away | 919 | +0.0349 [-0.0893, +0.1590] | +0.1174 [-0.0155, +0.2503] | 16 |
| validation/E0/venue=home | 919 | -0.0233 [-0.2150, +0.1683] | +0.0549 [-0.1531, +0.2629] | 16 |
| validation/E0/season=2020 | 320 | +0.0510 [+0.0076, +0.0943] | +0.1382 [+0.1223, +0.1542] | 2 |
| validation/E0/season=2021 | 304 | -0.1832 [-1.1793, +0.8130] | +0.0657 [-0.1139, +0.2454] | 3 |
| validation/E0/season=2022 | 134 | not estimated: insufficient n | — | — |
| validation/E1/season=2023 | 536 | -0.0016 [-0.1268, +0.1237] | -0.0586 [-2.2985, +2.1813] | 2 |
| validation/E1/venue=away | 840 | +0.0536 [-0.0294, +0.1365] | +0.1516 [-0.1680, +0.4713] | 8 |
| validation/E1/venue=home | 840 | +0.0359 [-0.1076, +0.1793] | -0.0199 [-0.1604, +0.1206] | 8 |
| validation/E0/season=2023 | 326 | +0.1051 [-2.6491, +2.8594] | +0.2038 [-1.3977, +1.8053] | 2 |
| validation/E1/season=2024 | 556 | +0.0509 [-0.0549, +0.1567] | +0.1022 [-0.0867, +0.2911] | 3 |
| validation/E0/season=2024 | 326 | -0.0610 [-0.4765, +0.3544] | +0.1325 [-0.4036, +0.6685] | 3 |
| validation/E1/season=2025 | 588 | +0.1242 [-0.0237, +0.2720] | +0.1399 [-0.5004, +0.7803] | 3 |
| validation/E0/season=2025 | 330 | -0.0765 [-0.0925, -0.0605] | -0.2920 [-0.8185, +0.2346] | 2 |

Later E1 attack effects progress−.002,+.051,+.124, rather than remaining stable across all seasons. EPL2023/24–2025/26 attack effects are+.105,−.061,−.076; concession effects+.204,+.132,−.292. Neither channel gives a stable cross-league signal. Season-level intervals are especially uncertain because they contain very few calendar clusters; all estimates remain visible rather than selecting favorable seasons.

## Validation and disposition

122 tests passed (117 inherited,5 diagnostic tests). Tests verify exact windows, concession direction, future/same-day exclusion, season reset, maximum history span, cancellation of constant error levels, known conditional association recovery, and minimum regression sample handling. Full source/spec/input and discovery hashes verified after validation. No existing production or prior research file was modified.

```bash
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.residual_persistence discovery
# Save discovery.json/hash before the unchanged validation run.
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m experiments.residual_persistence validation
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 /workspace/.venvs/deepfc/bin/python -m pytest -q
```

Full regression estimates, uncertainty variants, sample exclusions and per-observation past-feature audit fields are saved in discovery.json/validation.json and corresponding CSVs. No new datasets, live calls, candidate model, correction coefficients for deployment, probability adjustments, window search, push, PR or merge. Read-only GitHub inspection was limited to prior research. No execution/dependency blocker.

**Stop this direction on present evidence.** A faster residual feedback candidate is not justified by this diagnostic. This conclusion is scoped to the frozen five-versus-fifteen, established-season, next-match analysis and noisy historical data; it is not a universal finding that the model adapts optimally. No future adjustment is proposed because the specified support condition was not met.
