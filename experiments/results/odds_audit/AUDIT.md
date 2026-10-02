# Odds-input data check — 2026-10-02

**Conditional go for exploratory historical pre-closing 1X2 research; no-go for a claimed fixed-time live/Zeno experiment until input parity is verified.** No candidate fitted, outcome relationship tested, or Zeno change made.

## Coverage

Nine exact-hash-verified E1 season files: 4968 rows, 552 per season. One Bolton–Brentford fixture lacks corners; odds completeness does not restore its outcome. Counts below require finite decimal prices >1 and, for AH, a finite handicap line. Completeness is not a guarantee of correctness or timestamp validity.

| Season | Average pre 1X2 | Average pre goals | Average pre AH+line | B365 pre 1X2 | Pinnacle pre 1X2 | Average closing (each family) | Pinnacle closing 1X2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E1_1718 | 552 | 552 | 552 | 552 | 552 | absent | 552 |
| E1_1819 | 552 | 552 | 552 | 551 | 551 | absent | 552 |
| E1_1920 | 552 | 552 | 552 | 552 | 551 | 552 | 552 |
| E1_2021 | 552 | 552 | 552 | 552 | 551 | 552 | 550 |
| E1_2122 | 552 | 552 | 552 | 552 | 552 | 552 | 552 |
| E1_2223 | 552 | 552 | 552 | 552 | 552 | 552 | 552 |
| E1_2324 | 552 | 552 | 552 | 552 | 552 | 552 | 552 |
| E1_2425 | 552 | 552 | 552 | 552 | 552 | 552 | 552 |
| E1_2526 | 552 | 552 | 552 | 552 | 260 | 552 | 271 |

2017/18–2018/19 average fields: BbAvH/D/A, BbAv>2.5/<2.5, BbAvAHH/AHA with BbAHh. From 2019/20: AvgH/D/A, Avg>2.5/<2.5, AvgAHH/AHA with AHh. Closing counterparts AvgCH/CD/CA, AvgC>2.5/<2.5, AvgCAHH/CAHA with AHCh start in 2019/20. PSCH/CD/CA exist throughout these nine seasons. B365H/D/A exist throughout; B365 total-goal and AH pairs start in 2019/20 in these files.

Full season-specific bookmaker schemas and per-column missing/invalid counts: inventory.json and field_missingness.csv. These include Max, Bet365, Pinnacle, bwin, William Hill, Betfair/Exchange and the changing book roster. Book codes are not interchangeable: BF is Betfair, BFD is Betfred, BFE is Exchange; older VC and newer BV denote BetVictor. See [official field definitions](https://football-data.co.uk/notes.txt).

## Consistency and limitations

- Pre 1X2 averages exceed none of their corresponding maxima. Normalized Bet365 versus average 1X2 probabilities differ by a median maximum component of 0.75–0.92 percentage points by season; 95th-percentile differences are about 1.66–1.91 points. They are similar, not interchangeable.
- Average pre 1X2 implied-probability sums have seasonal medians 1.052–1.064. Proportional normalization removes this aggregate overround mechanically, not necessarily bookmaker bias. Never normalize a mixed-book triplet or treat best-price Max triplets as an executable single-book quote.
- B365H=0 for Brentford–Blackburn 2019-02-02 (corners present): exclude that quote, never treat zero as decimal odds. Pinnacle loses 292 pre and 281 closing triplets in 2025/26. Do not silently backfill from closing prices.
- AH anomaly: Sheffield United–Sheffield Weds 2024-11-10 AvgAHH=1.99 exceeds MaxAHH=1.93. Quarantine that market if used. Middlesbrough–Plymouth 2025-04-18 has zero BFECAHH/BFECAHA. Thus full numerical average-AH coverage is not fully consistency-clean.
- Goals and AH single-book coverage and normalized-pair comparisons are recorded separately in consistency.json. AH comparisons require the same line; a two-way price without its handicap is not a feature.
- Bb averages become Avg averages in 2019/20. The contributing books and averaging weights cannot be reconstructed from these rows. Individual bookmaker roster changes substantially in 2024/25 and 2025/26. Do not assume stationarity or calculate an unweighted mean of visible books as if it recreated the published average.

## Official timing evidence

[Download documentation](https://football-data.co.uk/downloadm.php) states two snapshots from 2019/20: one after opening and one closing. Earlier pre-closing data and older Pinnacle closing 1X2 are distinct. A pre-closing label does not mean a true opening price.

[Current fixtures page](https://football-data.co.uk/matches.php) gives Friday collection generally by 17:00 and Tuesday by 13:00, using the site’s wording British Standard Time. The [notes](https://football-data.co.uk/notes.txt) describe Friday/Tuesday afternoons; the fixtures page is more specific. Neither supplies historical per-row collection timestamps, exact lead time, consistent historical timezone rules, or exception handling for rearranged matches.

No quote timestamp fields exist in the audited CSVs. Time is kickoff, absent before 2019/20 here; it is not quote capture time. These files cannot establish that a quote was observable at kickoff−60min, kickoff−24h, or an exact publication instant. Closing columns are excluded from any proposed earlier-time feature. Same-date match-result exclusion does not itself make same-match odds timing safe. Official notes attribute odds to Betbrain, Oddsportal and individual books, but do not establish the per-row source mix.

## Existing research and live-input gap

Accessible main/research branches and local saved experiments cover time weighting, shrinkage, probability calibration, dispersion, signal-strength exponents, shot pressure and joint attack/defence. No odds-feature experiment was found in their code/docs/history. This finding is limited to accessible refs; it is not proof about unavailable private/original workspaces.

No Zeno source checkout/configuration or timestamped odds payload is available in this executor. GitHub installed-repository search for zeno and owner-scoped search found no identifiable project; broad results were unrelated and were not treated as Steve’s Zeno. Existing research merely states Zeno remains unchanged. Therefore provider, account tier, E1 coverage, 1X2/handicap/totals entitlements, bookmaker identity, update timestamp, polling latency, quota and existing scheduled prediction time are all UNVERIFIED. No claim that the same input is already available free through Zeno is justified.

Football-Data publicly offers a free upcoming fixtures file on its [fixtures page](https://football-data.co.uk/matches.php). This is a possible no-subscription source, not a verified existing Zeno integration or a fixed-horizon historical archive. The executor’s earlier CONNECT403 blocks direct primary-domain download; the static GitHub mirror supplied exact historical bytes but is not a demonstrated timely live feed. No access-control bypass or new subscription was attempted.

## One conditional next design

Only if the user accepts historical pre-closing-snapshot research as distinct from live validation: restrict the first study to 2019/20 onward AvgH/D/A, retaining earlier seasons solely as corner warm-up to avoid splicing BbAv/Avg features. Derive normalized pH,pD,pA and one signed strength feature s=pH−pA for home, −s for away. Test a single coefficient in mu=mu_fixed180*exp(beta*s), fitting beta only before 2023/24 with fixed baseline dispersion and a fixed unit Gaussian prior. Do not add goal-total/AH features or search variants initially. This is a genuinely different information source (current-match market assessment), but its incremental corner-prediction value is untested.

Freeze identical quote-complete fixtures, no closing fallback, chronological splits, source hashes, missing-data policy and existing performance gates before any fit. Report historical validity limitations. This is a proposal only, not authorization to run or a claim of live readiness.

For a future live test, a defensible proposed prediction time is kickoff−60 minutes UTC; retrieve the most recent complete same-book/same-market quote observed at or before that cutoff, with provider updated_at and own retrieved_at, and a predeclared freshness limit (e.g. 15 minutes). Do not impute missing markets or reuse a later quote. This is NOT historically validated by Football-Data’s pre-closing columns; a prospectively archived overlap is needed to measure source/timing differences.

## Go/no-go and minimum next step

Historical data check: PASS for a clearly labeled pre-closing 1X2 research hypothesis. Fixed-time historical/live parity: NOT ESTABLISHED. Running a deployable odds-feature experiment through current Zeno: NO-GO pending source evidence. No betting-edge claim.

Minimum next step: obtain the exact Zeno repository/source configuration and one redacted, timestamped E1 pre-match 1X2 payload using an existing entitlement (no credentials needed in the handoff). Confirm market/book coverage, freshness at the chosen cutoff, and whether a published average or named book can be matched. Then collect a small timestamped overlap across weekend and midweek fixtures before freezing a live-input design. If that existing source is unavailable, decide explicitly whether to pursue the limited historical-only study; do not silently substitute a paid feed.

Audit command: `/workspace/.venvs/deepfc/bin/python -m experiments.odds_data_audit`. Source hashes rechecked; 9×552=4968 rows verified. No modeling run, purchases, credentials, source modifications, push, deployment or Zeno changes. Audit files are saved locally and uncommitted.
