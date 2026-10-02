# Publication verification

This preservation snapshot starts from audited commit 7e8ad0acdcea13f5778e107882c36e5d6922fbd3. All changes are additions under experiments/independent_review plus a dedicated artifact-verification workflow. No previously published file is modified.

A new Python 3.12 virtual environment installed the repository test extra, pinned NumPy/SciPy research requirements and pinned plotting requirements. All 111 tests passed. Pip check found no broken requirements. The artifact verifier reproduced all saved audit slices and reliability metrics and generated plots in a temporary directory. It did not fit a historical model or execute the stopped candidate's later evaluation.

The original home-slope implementation, approved plan, OOF CSV and earlier fit result are preserved byte-for-byte and checked against their original execution hashes. Packaging edits affect audit CLI path portability, report links/status and the audit's observed_over field name only. The field previously named line_errors actually stored observed event rates; its numbers are unchanged. Original execution manifests remain historical records rather than being rewritten to imply a new experiment.

Derived prediction arrays were compressed losslessly with every array checked for equality. Public readable files replace local ZIP archives. Raw provider data, cache files, machine-specific installation logs, duplicated PDFs and private conversation context are excluded. No credential-pattern match was found in the staged additions.

The dedicated CI workflow runs the existing and synthetic home-slope tests plus the no-fit artifact verifier on this branch. Exact pushed SHA and remote run outcomes are verified after publication; a local pass alone is not presented as a remote CI result.
