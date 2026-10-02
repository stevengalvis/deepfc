# Research publication validation

2026-10-02. Prepublication local head a82506e047344e4978336b4694dd929bee0ad938; remote research/deepfc-2026-10-02 verified at7e8ad0acdcea13f5778e107882c36e5d6922fbd3 and is an ancestor. Publication adds a comparison/recommendation, this receipt, and the previously saved D2 feasibility audit; no model result changes.

Reviewed the complete post-7e8ad0 file inventory and remaining D2 audit. Derived forecast CSVs retain observed outcomes and model outputs, not raw provider season files. No credential/private-key patterns found. No .env/config/auth material, private operational ModelFC files, or provider data directory is staged. Historical local/private-only statements record earlier execution scope; explicit publication authorization now covers these research artifacts. The independent review branch is outside this publication.

Fresh virtual environment and separate Git-archive checkout (no data directory):

```bash
/workspace/.venvs/deepfc/bin/python -m venv /tmp/deepfc-publication-clean-venv
git archive a82506e047344e4978336b4694dd929bee0ad938 | tar -x -C /tmp/deepfc-publication-clean
/tmp/deepfc-publication-clean-venv/bin/python -m pip install -e '/tmp/deepfc-publication-clean[test]' -r /tmp/deepfc-publication-clean/experiments/joint_strength_requirements.txt
cd /tmp/deepfc-publication-clean
/tmp/deepfc-publication-clean-venv/bin/python -m pytest -q
/tmp/deepfc-publication-clean-venv/bin/python -m pip check
```

127 tests passed; pip check found no broken requirements. Exact timing and installed versions in companion receipts. The added D2 audit is a source-inventory script, not a fitted model or test dependency; it is syntax-checked separately. Remote exact-head CI is followed after the non-force push and its final URL/SHA reported to the requester. This receipt does not preclaim CI success.

Tests require no historical provider files; reproducing archived model results still needs the pinned inputs and their original paths. No merge/deployment or independent-review branch changes.
