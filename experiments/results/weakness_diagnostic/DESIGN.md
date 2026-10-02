# Exploratory diagnostic design, fixed before generating these cuts

Compare retained DeepFC and fixed180 on the identical 4208-fixture research cohort.
No candidate fitted. Preserve all source hashes from verified shot data manifest.
Predefined cuts only: season; venue; fixed180 expected mean <4 / 4–6 / >=6;
first 10 team appearances of a season versus later; and teams absent from the
previous Championship season versus returning Championship teams. Absence is an
entrant proxy, not a claim of promotion: it mixes relegated and promoted teams.
Cross entrant status with first10/later because transition adaptation is the
mechanism of interest. Exclude 2017/18 warm-up from metrics. Status uses prior
season membership, never future season outcomes. Matchday history updates after
the full date; first10 uses team appearances in either venue before the fixture.
Assess mean bias (actual minus predicted), Brier/NLL/MAE, probabilities of <=1
and >=10 corners versus frequencies. Cuts use fixed180 means for BOTH models.
Report 28-day block-bootstrap pointwise intervals for bias, Brier difference,
and tail calibration error, 2000 draws seed7. No multiplicity correction, no
causal claims, and no pristine holdout: every historical season was inspected.
Report all predefined groups, avoiding team-by-team or threshold searches.
Do not compare raw subgroup Brier as if intrinsic event uncertainty were equal.

Implementation correction before interpretation: season labels and first-ten/entrant
status use the source season CSV, not a July boundary. The delayed July 2020
fixtures belong to 2019/20. Initial diagnostic output was superseded for this
calendar-label bug; cuts and model forecasts were not changed.
