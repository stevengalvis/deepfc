# Independent DeepFC research review

This directory preserves the independent review of audited commit `7e8ad0acdcea13f5778e107882c36e5d6922fbd3`, the completed probability-reliability diagnostic, and the approved home-slope experiment that stopped on earlier data. It is published on its own branch. Original model code, results and failed-gate decisions remain intact.

- [Independent audit](audit/REPORT.md) reproduces historical gains without claiming independent confirmation.
- [Reliability diagnostic](reliability/REPORT.md) finds home probability underprediction alongside better discrimination. It includes frozen bins, code, results and plots.
- [Home-slope plan](home_slope/APPROVED_PLAN.md) specifies one correction and earlier-data stopping rules.
- [Stopped execution](home_slope/REPORT.md) records delta −0.1315218318 and no later candidate scoring.
- [Source references](REFERENCES.md) identify the earlier rejected calibration variants.

The stopped test passed 111 clean-install tests. A negative interior slope triggered its prespecified stop; neither a negative replacement candidate nor later E1/EPL scores were run. This is not a deployment or betting-profit result.

## Reproduce without provider data or model fitting

From the repository root, create a fresh virtual environment and install

```sh
python -m pip install -e '.[test]' -r experiments/joint_strength_requirements.txt -r experiments/independent_review/reliability/requirements.txt
PYTHONPATH=src:.:experiments/independent_review/home_slope OPENBLAS_NUM_THREADS=1 python -m pytest tests experiments/independent_review/home_slope/test_home_slope.py
OPENBLAS_NUM_THREADS=1 python experiments/independent_review/verify_artifacts.py
```

The verification command uses a temporary directory. It checks hashes and the stopped decision, reproduces saved audit slices from derived arrays, and regenerates reliability results/plots without model fitting. It does not overwrite tracked artifacts or enter the stopped candidate's later evaluation.

The NPZ files contain derived audited predictions and outcomes, not provider CSVs. They are losslessly compressed; compression_provenance.json maps original hashes to packaged hashes, and every array was verified unchanged. PNG plots are provided; duplicate PDFs, ZIP dumps, raw data, caches and redundant CSV summaries are omitted. reliability/results.json retains the complete bin, overall and decomposition tables.

## Optional complete raw-source arithmetic reproduction

These commands download only the 18 exact manifest-pinned mirror files into a chosen directory and recompute the already audited frozen forecasts. They fit no candidate. Network access and raw source availability are required.

```sh
python experiments/independent_review/audit/fetch_sources.py --output-dir /tmp/deepfc-audit-data
OPENBLAS_NUM_THREADS=1 python experiments/independent_review/audit/reproduce.py --data-root /tmp/deepfc-audit-data --output-dir /tmp/deepfc-audit-reproduction
python experiments/independent_review/audit/check_slices.py --arrays-dir /tmp/deepfc-audit-reproduction --output /tmp/deepfc-audit-reproduction/slice_checks.json
```

The current publication did not repeat the historical model fit. The stopped experiment's separate reproduction instructions explain how to recreate its earlier stage in a new output directory if explicitly desired. The generic verifier and CI do not do that.

## Provenance

Original execution manifests are retained as historical evidence. Packaging provenance distinguishes path-only CLI edits, lossless compression and document relocation from the code/data hashes at original execution. Publication authorization supersedes historical wording that work was local or not yet authorized to run. Those dated plans do not change the completed stopping decision. No private conversation or provider secrets are included.
