# Completed shot-pressure reconstruction

The frozen reconstruction completed without changing its code or specification. All nine restored CSV files match prior DeepFC archive SHA256 hashes exactly. The shot implementation is reconstructed, not equivalent to unavailable commit 98762bd.

Decision: retain fixed180 baseline under the predeclared earlier-selection rule. Strength 0.25 is the best shot candidate, but no shot candidate beats baseline in selection.

| Period | Observations | Model | Brier | Count NLL | MAE |
| --- | ---: | --- | ---: | ---: | ---: |
| selection | 5218 | baseline | 0.217140 | 2.338689 | 2.073609 |
| selection | 5218 | candidate | 0.217405 | 2.340376 | 2.076270 |
| validation | 1048 | baseline | 0.210451 | 2.406443 | 2.200642 |
| validation | 1048 | candidate | 0.210406 | 2.405511 | 2.204727 |
| later_test | 2150 | baseline | 0.208559 | 2.354073 | 2.120767 |
| later_test | 2150 | candidate | 0.207773 | 2.352773 | 2.119524 |

## Earlier selection grid

| Strength | Brier |
| --- | ---: |
| 0.25 | 0.217405 |
| 0.5 | 0.218590 |
| 1.0 | 0.223346 |

## Paired uncertainty

Candidate minus baseline, 28-day blocks; 2000 draws, seed 7. Intervals condition on these inspected data and do not account for all model-selection uncertainty.

| Period | Metric | Lower 95% | Upper 95% |
| --- | --- | ---: | ---: |
| selection | mean_brier_score | -0.000243 | 0.000740 |
| selection | negative_binomial_negative_log_loss | -0.000140 | 0.003536 |
| selection | mae | -0.001984 | 0.007326 |
| validation | mean_brier_score | -0.001621 | 0.001227 |
| validation | negative_binomial_negative_log_loss | -0.006270 | 0.003655 |
| validation | mae | -0.011158 | 0.016458 |
| later_test | mean_brier_score | -0.001411 | -0.000147 |
| later_test | negative_binomial_negative_log_loss | -0.003694 | 0.001025 |
| later_test | mae | -0.009051 | 0.006139 |

## Season, venue and line checks

| Season start year | Brier difference |
| --- | ---: |
| 2018 | -0.000634 |
| 2019 | -0.000599 |
| 2020 | +0.001552 |
| 2021 | +0.000313 |
| 2022 | +0.000348 |
| 2023 | -0.000045 |
| 2024 | -0.000576 |
| 2025 | -0.000993 |

| Period | Venue | Brier difference |
| --- | --- | ---: |
| selection | home | +0.000241 |
| selection | away | +0.000289 |
| validation | home | +0.000138 |
| validation | away | -0.000228 |
| later_test | home | -0.001201 |
| later_test | away | -0.000371 |

| Period | Line | Brier difference |
| --- | ---: | ---: |
| selection | 3.5 | +0.000282 |
| selection | 4.5 | +0.000067 |
| selection | 5.5 | +0.000221 |
| selection | 6.5 | +0.000490 |
| validation | 3.5 | -0.000254 |
| validation | 4.5 | +0.000607 |
| validation | 5.5 | -0.000383 |
| validation | 6.5 | -0.000152 |
| later_test | 3.5 | -0.000980 |
| later_test | 4.5 | -0.001376 |
| later_test | 5.5 | -0.000661 |
| later_test | 6.5 | -0.000127 |

## Replication versus reported chat checkpoints

Baseline validation Brier/NLL and later Brier/NLL/MAE match the reported numbers to six decimals. Best shot strength 0.25 and failure to beat baseline in earlier selection also agree. Candidate numbers do NOT replicate:

| Metric | Prior chat | Reconstruction |
| --- | ---: | ---: |
| Validation shot Brier | 0.210277 | 0.210406 |
| Validation shot NLL | 2.405287 | 2.405511 |
| Later shot Brier | 0.208046 | 0.207773 |
| Later shot NLL | 2.352916 | 2.352773 |
| Later shot MAE | 2.118482 | 2.119524 |
| Later Brier interval lower | -0.000825 | -0.001411 |
| Later Brier interval upper | -0.000192 | -0.000147 |

Exact data and baseline agreement isolate remaining discrepancies to reconstruction assumptions/implementation rather than source-byte differences. The original formula, smoothing, clipping, grid and missingness details are needed to establish equivalence. No parameter was changed to chase reported numbers.

## Reproducibility and scope

Working directory `/workspace/deepfc-shot-reconstruction`; branch `research/shot-pressure-reconstruction`; base `8af3712a132e97b35acdc56ddbdd0732f77eb815`. Changes remain uncommitted. Python 3.12.14, pytest 8.4.2; 70 tests passed in 0.44s. Original checkout remains clean at cff381c; src/, production and Zeno unchanged.

Exact historical command:

```bash
PYTHONPATH=src:. /workspace/.venvs/deepfc/bin/python -m experiments.shot_reconstruction data/E1_*.csv > experiments/results/shot_reconstruction/results.json
```

See ACQUISITION.md and verified_data_manifest.json for pinned mirror URLs, transformations, raw/restored hashes, date coverage and quarantine evidence. results.json contains full metrics and code/specification hashes. tests.txt records verification. Initial blocked-attempt manifests are retained as historical evidence, not the current run status.

## Prospective next step

Freeze an explicitly approved model choice before new outcomes; the selection rule here retains baseline and permits only exploratory shot shadow tracking. Obtain validated current Championship history and upcoming fixtures, define the future window and acceptance rule, persist immutable pre-match predictions with timestamps and code/data hashes, then reconcile verified corner outcomes. That prospective ledger workflow remains unimplemented. October 9 is not schedule-verified. Later historical seasons were already inspected; these results do not show a profitable betting edge.
