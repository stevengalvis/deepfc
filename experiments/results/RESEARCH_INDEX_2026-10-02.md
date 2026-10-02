# DeepFC research preserved on 2026-10-02

Isolated research branch; no merge or deployment. Frozen historical outcomes remain authoritative in their original records.

- [Shot reconstruction](shot_reconstruction/HANDOFF.md)
- [Joint attack/defence and numerical certification](joint_strength/REPORT.md)
- [Odds source audit](odds_audit/AUDIT.md)
- [Frozen original odds experiment — rejected](market_strength/REPORT.md)
- [Odds failure diagnostic](market_strength_diagnostic/REPORT.md)
- [Joint baseline/odds calibration — rejected](joint_market_calibration/REPORT.md)
- [Acceptance-criteria audit](acceptance_criteria_audit/AUDIT.md)
- [Prospective probability protocol draft](../protocols/team_corner_probability_confirmation.md)
- [Power/feasibility planning](power_planning/REPORT.md)
- [Cross-league exposure/availability audit — not evaluated](cross_league_feasibility/AUDIT.md)

Later writing artifacts are drafts/recommendations where marked; they do not replace old frozen gates. Chronological notes saying “local/uncommitted” describe their original task state, not this preservation snapshot. Provider datasets under data/ are not tracked or published. Included prediction CSV is a derived research result; field_missingness.csv is an aggregate inventory; tests/fixtures is a synthetic fixture.

Validation:100 tests pass using saved Python3.12.14 environment with pinned research dependencies. Git push transport passed a dry-run, despite gh reporting an invalid GH_TOKEN; actual publication must be verified against the remote branch SHA. Credential-pattern scanning covered all80 new-history blobs plus pending artifacts; no matching secrets found. Prior source model files remain unchanged relative to earlier research commits.
