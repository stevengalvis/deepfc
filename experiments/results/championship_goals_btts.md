# Championship full-match goals / BTTS research

**Recommendation: CONTINUE RESEARCH. No promotion or production integration.**

Run on 2026-10-07, based on DeepFC main `cff381c04b0b6b341b4845fded743c7aa2df6f4b`.
This isolated experiment changes neither the retained corner models nor Model FC/Zeno.

## Protocol and model definitions

- Reuse the canonical `Match`, Football-Data completed-match adapter, five-match venue-role smoothing, fixed 180-day time weight and predict-whole-date-before-update pattern.
- Goal counts are joined to canonical match identities; corner counts are **not** predictive features.
- Warm-up: 2017-18. Score from 2018-07-01; first scored fixture 2018-08-03, last 2026-05-02.
- 4,968 source rows; 4,967 retained, including 552 warm-up matches; 4,415 scored fixtures. The existing adapter excludes Bolton-Brentford 2019-04-27: the source has 0-1 goal fields but no corner results. The ambiguity is preserved as an explicit exclusion, not edited away.
- Development-era report: 2018-19 through 2023-24, **3,311** fixtures. Latest-two-season report: 2024-25 and 2025-26, **1,104** fixtures, 2024-08-09 through 2026-05-02.
- Only strictly earlier dates enter rates, event baselines or rho. Earlier results inside the recent window can inform later predictions: this is online walk-forward, not a frozen-fit holdout.
- Settings/window were fixed before viewing these goal metrics; there was no parameter search or fitted test-set calibration. Nevertheless the recent window is a **retrospective pseudo-holdout**, not a prospectively sealed untouched test.
- Season summaries use **source filenames**, not July boundaries; COVID-delayed July 2020 fixtures remain in 2019-20.

Let L be the earlier league average for the relevant venue role. Team attack A and opponent concessions D each use `(observed goals + 5*L)/(effective matches + 5)`.

| Model | Definition |
| --- | --- |
| coin_0_5 | Both event probabilities fixed at 0.5. |
| expanding_event_rate | Earlier league event frequency, Beta(1,1) smoothing. |
| venue_poisson | Independent Poisson home/away goals at earlier venue-specific league means. |
| team_arithmetic | Independent Poisson; rate `(A+D)/2`, equal-weight expanding history; mirrors retained team-corner structure. |
| team_multiplicative | Independent Poisson; rate `A*D/L`, equal-weight expanding history; mirrors the corner-decay experiment comparator. |
| team_decay_180 | Same multiplicative rate with fixed 180-day exponential weights. |
| Each of the four Poisson models + _dc | Dixon-Coles low-score correction, retaining exactly the same scoring intensities. |

Ten candidates score the identical cohort. Independent Poisson gives `P(over 2.5)=1-exp(-s)*(1+s+s²/2)`, s=home+away rate, and `P(BTTS)=(1-exp(-home))*(1-exp(-away))`. Under/No are complements and have identical Brier scores.

DC multipliers for 0-0, 0-1, 1-0, 1-1 are `1-home*away*rho`, `1+home*rho`, `1+away*rho`, `1-rho`. Rho maximizes conditional likelihood on earlier **prequential** low-score forecasts, with at least 50 such observations, a fixed +/-0.25 bound and strictly positive cell multipliers. The decay candidate also decays rho observations by 180 days. This is **not** joint maximum-likelihood fitting of team attack/defence and DC dependence.

## Brier scores

Lower is better. A low Brier score is not proof of a sportsbook edge.

| Model | All O/U 2.5 | All BTTS | Recent O/U 2.5 | Recent BTTS |
| --- | ---: | ---: | ---: | ---: |
| coin_0_5 | 0.250000 | 0.250000 | 0.250000 | 0.250000 |
| expanding_event_rate | 0.249384 | 0.250010 | 0.249466 | 0.249652 |
| venue_poisson | 0.249396 | 0.249993 | 0.249578 | 0.249410 |
| team_arithmetic | 0.248674 | 0.249447 | 0.247488 | 0.246827 |
| team_multiplicative | 0.251097 | 0.251260 | 0.247939 | 0.246547 |
| team_decay_180 | 0.250458 | 0.251557 | 0.250510 | 0.248824 |
| venue_poisson_dc | 0.249396 | 0.249981 | 0.249578 | 0.249459 |
| team_arithmetic_dc | 0.248674 | 0.249427 | 0.247488 | 0.246873 |
| team_multiplicative_dc | 0.251097 | 0.251227 | 0.247939 | 0.246613 |
| team_decay_180_dc | 0.250458 | 0.251532 | 0.250510 | 0.248882 |

## Calibration

Observed over/BTTS rates: **47.2933% / 51.0985%** across all scored fixtures; **47.5543% / 53.5326%** in the latest two seasons.
ECE uses ten fixed equal-width probability bins; it is descriptive and sensitive to bin sparsity. Bias = mean predicted minus observed. No calibration fit is applied.

| Window / model / target | Mean predicted | Observed | Bias (pp) | ECE (pp) |
| --- | ---: | ---: | ---: | ---: |
| All / expanding_event_rate / over_2_5 | 47.4574% | 47.2933% | +0.1641 | 0.1641 |
| All / expanding_event_rate / btts_yes | 50.8724% | 51.0985% | -0.2261 | 0.2261 |
| All / team_arithmetic / over_2_5 | 47.0925% | 47.2933% | -0.2008 | 0.6053 |
| All / team_arithmetic / btts_yes | 51.1088% | 51.0985% | +0.0102 | 1.3090 |
| All / team_arithmetic_dc / over_2_5 | 47.0925% | 47.2933% | -0.2008 | 0.6053 |
| All / team_arithmetic_dc / btts_yes | 51.1151% | 51.0985% | +0.0165 | 1.1478 |
| All / team_decay_180 / over_2_5 | 46.0253% | 47.2933% | -1.2681 | 4.2666 |
| All / team_decay_180 / btts_yes | 49.1526% | 51.0985% | -1.9459 | 4.5452 |
| Recent / expanding_event_rate / over_2_5 | 47.0746% | 47.5543% | -0.4798 | 0.4798 |
| Recent / expanding_event_rate / btts_yes | 50.3857% | 53.5326% | -3.1469 | 3.1469 |
| Recent / team_arithmetic / over_2_5 | 46.8562% | 47.5543% | -0.6982 | 2.0100 |
| Recent / team_arithmetic / btts_yes | 50.9019% | 53.5326% | -2.6307 | 2.6307 |
| Recent / team_arithmetic_dc / over_2_5 | 46.8562% | 47.5543% | -0.6982 | 2.0100 |
| Recent / team_arithmetic_dc / btts_yes | 50.8282% | 53.5326% | -2.7044 | 2.7044 |
| Recent / team_decay_180 / over_2_5 | 45.6859% | 47.5543% | -1.8684 | 4.0563 |
| Recent / team_decay_180 / btts_yes | 48.7023% | 53.5326% | -4.8304 | 4.8304 |

Recent arithmetic-model nonempty calibration bins:

| Target | Probability bin | N | Mean predicted | Observed |
| --- | --- | ---: | ---: | ---: |
| over_2_5 | 0.3-0.4 | 10 | 39.41% | 70.00% |
| over_2_5 | 0.4-0.5 | 900 | 45.64% | 44.89% |
| over_2_5 | 0.5-0.6 | 190 | 52.69% | 58.95% |
| over_2_5 | 0.6-0.7 | 4 | 61.94% | 50.00% |
| btts_yes | 0.4-0.5 | 438 | 48.03% | 48.40% |
| btts_yes | 0.5-0.6 | 661 | 52.72% | 56.73% |
| btts_yes | 0.6-0.7 | 5 | 61.77% | 80.00% |

Bins with four/five/ten fixtures are too sparse for strong calibration claims.

## Paired uncertainty and Dixon-Coles

Paired 28-calendar-day block bootstrap: 2,000 samples, seed 7; 87 blocks overall, 22 recent blocks. Negative challenger-minus-baseline delta favors the challenger. Intervals are descriptive, not adjusted for multiple comparisons or all long-range team/season dependence.

| Comparison | Window | Target | Delta Brier | Approximate 95% interval |
| --- | --- | --- | ---: | --- |
| team_arithmetic_minus_expanding_event_rate | All | over_2_5 | -0.00070929 | [-0.00198185, +0.00051394] |
| team_arithmetic_minus_expanding_event_rate | All | btts_yes | -0.00056293 | [-0.00156965, +0.00036527] |
| team_decay_180_minus_team_arithmetic | All | over_2_5 | +0.00178398 | [-0.00033659, +0.00383559] |
| team_decay_180_minus_team_arithmetic | All | btts_yes | +0.00211021 | [+0.00025473, +0.00387802] |
| team_arithmetic_dc_minus_team_arithmetic | All | over_2_5 | +0.00000000 | [+0.00000000, +0.00000000] |
| team_arithmetic_dc_minus_team_arithmetic | All | btts_yes | -0.00001996 | [-0.00005721, +0.00001228] |
| team_decay_180_dc_minus_team_decay_180 | All | over_2_5 | +0.00000000 | [+0.00000000, +0.00000000] |
| team_decay_180_dc_minus_team_decay_180 | All | btts_yes | -0.00002527 | [-0.00012742, +0.00007308] |
| team_arithmetic_minus_expanding_event_rate | Recent | over_2_5 | -0.00197763 | [-0.00410872, +0.00018849] |
| team_arithmetic_minus_expanding_event_rate | Recent | btts_yes | -0.00282482 | [-0.00485323, -0.00100992] |
| team_decay_180_minus_team_arithmetic | Recent | over_2_5 | +0.00302210 | [-0.00032302, +0.00591748] |
| team_decay_180_minus_team_arithmetic | Recent | btts_yes | +0.00199674 | [-0.00164443, +0.00571928] |
| team_arithmetic_dc_minus_team_arithmetic | Recent | over_2_5 | +0.00000000 | [+0.00000000, +0.00000000] |
| team_arithmetic_dc_minus_team_arithmetic | Recent | btts_yes | +0.00004523 | [+0.00000684, +0.00009111] |
| team_decay_180_dc_minus_team_decay_180 | Recent | over_2_5 | +0.00000000 | [+0.00000000, +0.00000000] |
| team_decay_180_dc_minus_team_decay_180 | Recent | btts_yes | +0.00005800 | [-0.00018650, +0.00030724] |

**DC does not materially improve either target in this experiment.** O/U 2.5 is exactly invariant: all four corrected cells have total goals <=2, and their mass shifts cancel. BTTS changes are tiny: arithmetic+DC improves full-window Brier by only 0.00001996 (interval crosses zero) and slightly worsens recent Brier by 0.00004523. A future **joint** DC/intensity refit could alter O/U 2.5 through changed intensities; that different model was not evaluated here.

## True source-season stability

| Season | N | Event-rate OU | Arithmetic OU | Decay OU | Event-rate BTTS | Arithmetic BTTS | Decay BTTS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2018-2019 | 551 | 0.250543 | 0.249247 | 0.252076 | 0.249473 | 0.248608 | 0.251786 |
| 2019-2020 | 552 | 0.250155 | 0.249449 | 0.251307 | 0.249275 | 0.249843 | 0.254211 |
| 2020-2021 | 552 | 0.246826 | 0.246980 | 0.247687 | 0.251690 | 0.252989 | 0.254423 |
| 2021-2022 | 552 | 0.249021 | 0.251610 | 0.253131 | 0.250207 | 0.252818 | 0.254278 |
| 2022-2023 | 552 | 0.247203 | 0.246814 | 0.250301 | 0.250086 | 0.249681 | 0.253723 |
| 2023-2024 | 552 | 0.252391 | 0.250319 | 0.248147 | 0.250042 | 0.247979 | 0.246389 |
| 2024-2025 | 552 | 0.247631 | 0.245499 | 0.246078 | 0.250053 | 0.247237 | 0.248009 |
| 2025-2026 | 552 | 0.251301 | 0.249478 | 0.254943 | 0.249251 | 0.246418 | 0.249639 |

## Dataset provenance and acceptance

Exactly nine files reside in ignored `data/`; `.gitignore` already contains `data/`. CSVs must not be staged or committed.
The five earlier files came directly from `https://football-data.co.uk/mmz4281/{season}/E1.csv`: HTTP 200, text/csv, non-HTML bodies. The documented www host initially returned redirects to that same official host; no redirect/error body was accepted.
The four newer files are copies of `/var/lib/modelfc/history/E1_{season}.csv`; source SHA-256 before/after copying and destination SHA-256 all match. Source ownership, mode, mtime, inode and ACL/xattrs were unchanged.
Every file has Div=E1, 24 distinct teams, 552 unique fixtures, valid season dates and non-negative integer FTHG/FTAG; fixture identity plus HC/AC columns are present. All goal fields are populated. One source row has both corner results absent and is explicitly excluded by the shared completion adapter.

| File | Rows | First / last date | SHA-256 |
| --- | ---: | --- | --- |
| E1_1718.csv | 552 | 2017-08-04 / 2018-05-06 | `04d07d578d818bdcd6b95d43e79f10a6a26be01b45be6190b09ebdeaeba0a7ce` |
| E1_1819.csv | 552 | 2018-08-03 / 2019-05-05 | `112eedf787e26e00aac1442ef86e7fee5d4a43f86552ff2dac31ceb95a849487` |
| E1_1920.csv | 552 | 2019-08-02 / 2020-07-22 | `f31450c623c0b74b89692584a85924cc652d33ec89757acf4b2dda5e26261d57` |
| E1_2021.csv | 552 | 2020-09-11 / 2021-05-08 | `cf93295e310c60e5b97ae7466d772f8ec6a908ad401e38fceb7e8617369d5073` |
| E1_2122.csv | 552 | 2021-08-06 / 2022-05-07 | `a181451be4801b9f838daf5f6aaf21e9f09d36042be9e6c15388e71001e772ea` |
| E1_2223.csv | 552 | 2022-07-29 / 2023-05-08 | `cd38ab0586ea8cb4d573c363ff70749117f116da5b2741e5b0ea37da05860b1b` |
| E1_2324.csv | 552 | 2023-08-04 / 2024-05-04 | `5737f6cc95c95092b28317f41d3123e2fb09345434efc1c84bbdf15830849ab3` |
| E1_2425.csv | 552 | 2024-08-09 / 2025-05-03 | `f34c340446c916374be66bdc2fb25b87ee7f2662712ca009653d03ac705535f9` |
| E1_2526.csv | 552 | 2025-08-08 / 2026-05-02 | `98954c319950f19158624b17a154ef1c56eb7b8d169ef317f28f06d11d0b9a74` |

The companion `championship_goals_btts_data.json` records HTTP/provenance and byte-identity checks, but contains no raw CSV rows or credentials.

## Limitations and recommendation

- Full-window arithmetic improvements over event rates are small and both bootstrap intervals cross zero. Recent BTTS is more encouraging (delta -0.00282482; interval [-0.00485323,-0.00100992]), but temporal instability, recent underprediction and multiple comparisons prevent a promotion claim.
- Multiplicative models do not improve the full-window baseline; the fixed 180-day corner setting does not transfer convincingly to goals. Reject automatic reuse of that setting and a DC-only upgrade.
- Simple venue-role means are not jointly estimated attack/defence ratings; no opponent-adjusted regression, lineup/injury inputs, season resets, hyperparameter selection, Negative Binomial goal model or independently fitted binary classifier is evaluated.
- COVID and league/club turnover can change the distribution. Retrospective chronological scoring is not an untouched prospective validation.
- Low ECE for a nearly constant league baseline does not show fixture discrimination; sparse-bin ECE and aggregate bias can hide conditional miscalibration.
- No historical sportsbook benchmark, trusted opener/close, vig adjustment, CLV, ROI, profitability or production readiness assessment is made. CSV bookmaker columns are not used.
- Network access for dataset assembly was limited to those five official static CSV resources. **OddsPapi requests: 0.** Model FC source files, production code/state/evidence, controls, services and timers were not modified.

**CONTINUE RESEARCH** with the arithmetic baseline as the reference candidate, not as a selected production model. Any further shrinkage/decay/calibration or joint-rate/DC choices must be learned only on earlier data, followed by independently held-out/prospective evaluation and trustworthy market-price comparisons before promotion.

## Run with the same local inputs

This checkout is not self-contained for exact reproduction: the nine source
CSVs are intentionally gitignored and are not distributed by this repository.
Four inputs came from read-only Model FC history paths that are not public.
The hashes above allow an authorized holder of the same files to verify byte
identity, but they do not make the raw data recoverable. With those exact files
placed under `data/`, run:

```bash
python -m experiments.goals_btts \
  data/E1_1718.csv data/E1_1819.csv data/E1_1920.csv \
  data/E1_2021.csv data/E1_2122.csv data/E1_2223.csv \
  data/E1_2324.csv data/E1_2425.csv data/E1_2526.csv
python -m pytest
```

The CLI prints complete aggregate, fixed-bin calibration, seasonal and bootstrap metrics as JSON. No model outputs are saved to production.
