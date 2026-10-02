# Home slope test stopped on earlier data

The approved home slope test stopped before later evaluation. The fitted coefficient was **−0.1315218318**, whereas the prespecified expansion hypothesis required a positive interior coefficient. The fit favors further compression of home means around five corners, the opposite of the proposed correction. Keep the frozen joint model unchanged and retire this specific expansion test under its approved rules.

This is a completed stopped experiment, not a numerical failure or missing-data blocker. All three nuisance fits were certified, earlier-data support passed, and the scalar solution was interior with a near-zero gradient. There is no later Brier, calibration or EPL result for this candidate because producing one would violate the stopping rule.

## What was run

One home-only correction around the fixed five-corner anchor, with delta constrained to [−0.5, +0.5] and a zero-centered Gaussian prior with standard deviation 0.25. Away forecasts remain unchanged. A single NB distribution with the existing per-row dispersion generates all four coherent exceedance probabilities and the count likelihood.

The published joint objective and certified Newton solver produced the three prescribed temporal OOF forecast sets. Each first-stage fit used only earlier E1 observations; fixed180 histories excluded the entire prediction date. July 2020 fixtures were assigned by actual date. The final published joint coefficients were never refitted or replaced.

| Training cutoff | Latest training outcome | Training fixtures | OOF fixtures |
|---|---|---:|---:|
| 1 July 2020 | 30 June 2020 | 446 | 592 |
| 1 July 2021 | 8 May 2021 | 1,038 | 532 |
| 1 July 2022 | 7 May 2022 | 1,570 | 542 |

The correction used 1,666 home OOF observations, with outcomes from 1 July 2020 through 8 May 2023. There were 536 home means below five and 1,130 above five, each spanning 33 occupied 28-day blocks. All pooled support floors passed. Of the nine available source seasons, only the six E1 files through 2022/23 were required for this stage. Their hashes matched the published manifest. Of 3,312 raw rows, 3,311 contained corner outcomes. There were no invalid quote exclusions among the eligible feature seasons.

## Numerical evidence and stopping decision

| Quantity | Result |
|---|---:|
| Fitted delta | −0.13152183178153348 |
| Implied home slope multiplier | 0.8684781682184665 |
| Penalized score at delta zero | +18.392906137463918 |
| Score at the solution | −4.44 × 10⁻¹⁵ |
| Independently accumulated score | −7.51 × 10⁻¹⁵ |
| Positive curvature at the solution | 139.4713440711327 |
| Boundary solution | No |
| Recorded status | `stop_nonpositive_delta` |
| Later scoring executed | No |

The positive score at zero means increasing delta initially worsens the earlier penalized likelihood. Its strictly positive curvature gives a unique scalar optimum. The fitted negative delta would move home means toward five, rather than expand them away from five. We did not change its sign, choose another pivot, add an intercept, fit a different family or carry the negative correction into later scoring.

This is earlier-data estimation evidence only. It does not show that compression would improve later probability forecasts. It also does not invalidate the previously observed home probability underprediction. Rather, that diagnostic did not translate into support for this particular earlier-trained slope-expansion hypothesis. The likelihood fitting objective and four-line Brier objective differ, and OOF base models have shorter training histories than the frozen final base model. These were known design limitations, not grounds for changing the plan after seeing the coefficient.

## Verification and preserved artifacts

The full test suite includes the 102 existing tests and nine new tests covering exact no-change recovery, unchanged away forecasts, the two directions around the pivot, coherent decreasing probabilities, bounds, derivatives, zero and signed interior fits, boundary KKT conditions, support rules, cutoff isolation and same-date baseline isolation. A fresh installation passed all 111 tests in 0.96 seconds, and pip check found no broken requirements. The evidence is in tests_clean_install.txt and pip_check.txt.

All 124 published tracked files in the review checkout were compared with commit 7e8ad0acdcea13f5778e107882c36e5d6922fbd3 and remain unchanged. The experiment implementation and copied approved plan match the hashes saved before fitting. The original joint coefficient artifact remains byte-identical. Complete fixture pairing and OOF chronology were independently checked after execution.

The separated local artifact contains the code, tests, unchanged approved plan, pre-fit manifest, OOF predictions, fit certificates, support counts, run log and validation evidence. No original model-result rewrite, pull request, merge or deployment occurred. The experiment originally remained local; its artifacts are now published separately without rerunning the fit. The preliminary test invocation's working-directory error and its correction are documented in EXECUTION_NOTES.md.

## Recommendation

Keep the unchanged joint model as the existing research candidate. Do not run the stopped correction on later Championship or EPL outcomes to see whether it can be rescued. Another correction would require a new hypothesis and separate approval, not an automatic continuation of this test.

The broader home calibration issue remains unresolved. This result supplies no new confirmation evidence and no betting-edge evidence. Previously inspected histories still cannot substitute for genuinely new forecasts archived before outcomes with timestamped, source-matched inputs. The proposed later numerical continuation margins were not reached and remain research assumptions, not deployment criteria.
