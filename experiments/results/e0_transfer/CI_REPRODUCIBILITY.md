# Clean research-suite installation

2026-10-02 follow-up to the original EPL report's CI limitation. The historical report is preserved; this companion records the authorized dependency fix.

CI now installs the existing NumPy2.5.3/SciPy1.18.1 pins in experiments/joint_strength_requirements.txt alongside the pytest extra. Its pip cache includes that file and pyproject.toml. Production dependencies remain empty; no model/spec/result changes.

Verified in a fresh virtual environment and a separate Git-archive checkout with no provider datasets:

```bash
/workspace/.venvs/deepfc/bin/python -m venv /tmp/deepfc-clean-ci-venv
/tmp/deepfc-clean-ci-venv/bin/python -m pip install -e '/tmp/deepfc-clean-ci[test]' -r /tmp/deepfc-clean-ci/experiments/joint_strength_requirements.txt
cd /tmp/deepfc-clean-ci
/tmp/deepfc-clean-ci-venv/bin/python -m pytest -q
/tmp/deepfc-clean-ci-venv/bin/python -m pip check
```

Result:102 passed in1.10s; no broken requirements. Python3.12.14, NumPy2.5.3, SciPy1.18.1, pytest8.4.2. A nonblocking pip cache-permission warning disabled caching locally. This resolves local clean-install reproduction; remote CI status is verified separately for the published head.

The seven-season historical transfer and separate2023/24-onward interpretation remain unchanged. Reproducing model metrics still requires separately documented source data/hashes; tests do not.
