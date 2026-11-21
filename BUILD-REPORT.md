# Build report — gta6-trophy-rarity-forecast-01 entry

## Model summary

The program (`main.py`, Python stdlib only, deterministic) forecasts in
**earner space**. Exophase prints each trophy's rarity as
`round2(earners / players * 100)`, so the integer earners behind any read are
recovered exactly as `e_i = round-half-up(rate_i * players / 100)` (verified
on the practice history: the 55 reconstructed earners sum to the printed
`trophies_earned` of 943). Reads are segmented into frozen page states
(identical `(players, rates)` = one state, keeping first-seen time).

- **Branch A — single-state history (the practice shape).** The next
  Exophase refresh dilutes the rates: earners are held fixed and divided by
  the projected post-refresh player count. For the launch state documented
  in the kit RULES.txt (638 players, unchanged through the 04:00 read), the
  first refresh is the 04:30 read at **3,868 players**, so
  `P_next = 3868`. Fallbacks for other single-state cases: `round(P * 6.063)`
  if the state predates 2026-11-20T00:00:00Z, else `round(P * 1.5)`.
  A trophy with `e_i >= players` stays at 100.00; `e_i == 0` stays 0.00; a
  missing rate falls back to the last printed rate. The median is
  `round-half-up(e_i / P_next * 100, 2)` (Decimal `ROUND_HALF_UP`, not
  banker's rounding) and all five quantiles equal the median — a point
  forecast of the post-refresh printed rates.
- **Branch B — multi-state history (the final case shape).** Future
  refreshes are projected every median observed state gap (clamped to
  [6h, 30h]) from the last state change, up to the target. Players grow by
  the daily factor from the last two states, decaying x0.92 per refresh.
  Earners drift by their observed daily delta, each step scaled by
  `0.9^step` and by saturation headroom `max(0, 1 - e_i / P_proj)`, capped
  to `[0, P_proj]`. Quantiles spread logit-normally around the projected
  median with `sigma_i = clamp(0.30 + 0.22 * refreshes + 0.15 * min(1,
  |d_i| / max(1, e_i,last)), 0.3, 1.6)`; medians of 100 / 0 get the fixed
  rows `[99.9, 99.99, 100, 100, 100]` / `[0, 0, 0, 0.01, 0.05]`.
- **Robustness.** Any exception on a case falls back to the last-read rates
  as a point forecast for that case; a final sanitize pass guarantees one
  row per trophy, finite values in [0, 100], non-decreasing quantiles. The
  program never crashes and always writes a valid output file.

## Practice predictions — p00 (Branch A, 638 → 3,868 players)

All five quantiles equal the predicted rate (point forecast). p01's history
is the identical frozen state, and its predictions are byte-identical.

| id | name | e_i | predicted |
|---:|---|---:|---:|
| 1 | Vice Got a Price! | 4 | 0.10 |
| 2 | Just Like Paradise | 638 | 100.00 |
| 3 | Paradise Lost | 8 | 0.21 |
| 4 | T**s Ass Drug Money | 7 | 0.18 |
| 5 | Vice City, Baby! | 7 | 0.18 |
| 6 | Top Of The World, Ma | 7 | 0.18 |
| 7 | You Gotta Know When to Get Off | 7 | 0.18 |
| 8 | Trust | 7 | 0.18 |
| 9 | Break the Bank | 7 | 0.18 |
| 10 | Family Matters | 7 | 0.18 |
| 11 | DWNFALL | 7 | 0.18 |
| 12 | Hi-Jacked | 7 | 0.18 |
| 13 | Snow Storm | 7 | 0.18 |
| 14 | A Long Road | 4 | 0.10 |
| 15 | Cunning Stunts | 4 | 0.10 |
| 16 | Master of None | 5 | 0.13 |
| 17 | The Shootist | 4 | 0.10 |
| 18 | Top Fun | 4 | 0.10 |
| 19 | Earn Cash, Not Kudos | 5 | 0.13 |
| 20 | Baited My Tackle | 13 | 0.34 |
| 21 | Stick Fiddler | 6 | 0.16 |
| 22 | Road to Rehabilitation | 5 | 0.13 |
| 23 | This Was No Boat Accident | 5 | 0.13 |
| 24 | The Lone Rider | 5 | 0.13 |
| 25 | Strangers & Freaks | 4 | 0.10 |
| 26 | Supply & Demand | 4 | 0.10 |
| 27 | Spin On This! | 5 | 0.13 |
| 28 | Positive Mental Attitude | 4 | 0.10 |
| 29 | Fair Game | 5 | 0.13 |
| 30 | Don't Touch My Deck | 4 | 0.10 |
| 31 | You WAiNKer! | 4 | 0.10 |
| 32 | One Last Thing | 4 | 0.10 |
| 33 | Hot Together | 6 | 0.16 |
| 34 | Retail Therapy | 5 | 0.13 |
| 35 | Whip It Good | 8 | 0.21 |
| 36 | Gunslinger | 5 | 0.13 |
| 37 | Catch Me If You Can | 6 | 0.16 |
| 38 | Challenging Tank | 10 | 0.26 |
| 39 | Sneakthief | 6 | 0.16 |
| 40 | Maximum Withdrawal | 5 | 0.13 |
| 41 | A Classic Blitz Play | 6 | 0.16 |
| 42 | The Goodtime State | 5 | 0.13 |
| 43 | Pest Control | 5 | 0.13 |
| 44 | In The Beginning… | 6 | 0.16 |
| 45 | Capital Offense | 5 | 0.13 |
| 46 | Let’s Go Bowling | 5 | 0.13 |
| 47 | Personal Best | 5 | 0.13 |
| 48 | Actions Speak Louder | 5 | 0.13 |
| 49 | Bad Luck, I Guess | 5 | 0.13 |
| 50 | The Truth Is Out There | 5 | 0.13 |
| 51 | Ten Pin | 5 | 0.13 |
| 52 | Dime on the Dollar | 5 | 0.13 |
| 53 | Treat Yo Self | 6 | 0.16 |
| 54 | Little Boxes | 5 | 0.13 |
| 55 | On the Spot | 5 | 0.13 |

## Boundary audit

For each trophy the unrounded value `e_i / 3868 * 100` was compared with the
nearest `.xx5` 2-decimal rounding boundary; anything within 0.002 points is
flagged. **21 of 55 trophies are flagged.** Predictions were NOT changed for
any of them — the flags only record where a one-earner difference in the
answering read, or a different rounding convention at Exophase, would flip
the last printed digit.

Flagged groups (identical earners share the same unrounded value):

| earners | unrounded | distance to boundary | predicted | trophy ids |
|---:|---:|---:|---:|---|
| 6 | 0.155119 | 0.000119 | 0.16 | 21, 33, 37, 39, 41, 44, 53 |
| 13 | 0.336091 | 0.001091 | 0.34 | 20 |
| 4 | 0.103413 | 0.001587 | 0.10 | 1, 14, 15, 17, 18, 25, 26, 28, 30, 31, 32 |
| 8 | 0.206825 | 0.001825 | 0.21 | 3, 35 |

The tightest group is the 7 trophies at 6 earners: 0.155119 sits only
0.000119 above the 0.155 boundary, so they round up to 0.16 — correct under
round-half-up, and the first place a mismatch would appear if the answering
read's earner count differed by one (5 earners would print 0.13, 7 would
print 0.18).

## Tests

- **Practice run** (`MAKEFUN_INPUT_DIR` = kit `input/`, fresh output dir):
  `p00.out` and `p01.out` written, 2,210 bytes each (limit 65,536). Format
  validated programmatically: exactly 55 rows, ids 1..55 in order, 5
  quantiles per row, every value in [0, 100], non-decreasing.
- **p00 vs p01:** outputs byte-identical, as expected — both histories are
  the same frozen launch state.
- **Determinism:** a second full run produced byte-identical outputs
  (`cmp` clean on both files).
- **Timing:** ~0.05 s per case including interpreter start (3 runs of a
  single-case directory: 0.047 / 0.047 / 0.051 s); the two-case practice
  run took 0.072 s wall total. Limit is 8 s per case.
- **Branch B synthetic test:** a fabricated case with 3 distinct states
  (players 1,000 → 1,600 → 2,300 at 24 h gaps, earners grown per state,
  target 2.5 days after the last change) ran with no crash and produced a
  valid 55-row output. Audit: branch B, interval 1.0 day, 2 projected
  refreshes, projected answering players 4,372.5; quantile rows spread
  logit-normally around the projected medians (e.g. trophy 1:
  [0.0882, 0.1898, 0.3228, 0.5486, 1.1739]).

## V2 — growth correction + rate-trajectory model

v1 scored practice loss 0.179339. Diagnosis: the dilution skeleton
(earners reconstructed exactly, post-refresh players 3,868) was exactly
right for ~24 of 55 trophies, but ~31 trophies gained ≈106 earners in
total by the refresh — the pre-release cohort kept playing between the
frozen snapshot and the recalculation. v2 answers that in both branches:

- **Branch A — earners growth before dilution.** After reconstructing
  `e_i` and choosing `P_next` (unchanged: 3,868 for the 638 launch state),
  each trophy's earners grow first: `g_i = round-half-up(0.35 * e_i)` when
  `e_i >= 5`, else 0; `E_i = min(e_i + g_i, P_next - 1)`. The universal
  trophy (`e_i >= players`) still maps to `E_i = P_next` (100.00),
  `e_i == 0` stays 0, a missing rate still falls back to the last printed
  rate. The median is `round-half-up(E_i / P_next * 100, 2)` and all five
  quantiles still equal it. Total growth added on the practice state:
  +93 earners across 43 trophies (v1's missing mass was ≈106).
- **Branch B — replaced by a rate-trajectory model.** States are built as
  before. Release time is midnight UTC on `game.release_date` (else the
  first read's date). The recalculation cadence is the median state gap
  clamped to [6h, 30h]; the answering-state time `t*` is the last
  recalculation at or before the target (the last state itself when no
  recalculation falls before the target). Per trophy, a weighted least
  squares line is fitted to `logit(rate)` against
  `x = ln(1 + hours since release)` over the states with
  `0 < rate < 100`, weights `0.75^(transitions after the state)`; a slope
  beyond ±3 is halved once. The fit is evaluated at `x(t*)` and blended
  with persistence in logit space (fit weight 0.5 with exactly 2 usable
  states, 0.75 with ≥3; fewer than 2 → pure persistence). Sigma is
  `clamp(0.30 + 0.18 * days(last state → t*) + weighted fit RMSE, 0.3,
  1.6)` and the quantiles are logit-normal around the blended median.
  Fixed rows: last-state rate 100 with `E == P` →
  `[99.9, 99.99, 100, 100, 100]`; earners 0 in every state →
  `[0, 0, 0.01, 0.05, 0.2]`. The per-case fallback and the sanitize pass
  are unchanged.

### V2 practice predictions — p00 (Branch A, 638 → 3,868 players)

Point forecasts as in v1; `E` is the grown earner count. **43 of 55
predictions changed** (total +93 earners); the 12 unchanged rows are the
universal trophy (id 2) and the eleven 4-earner trophies (`e < 5` → no
growth). p01's output is byte-identical to p00's, as in v1.

| id | name | e | E | v1 | v2 | Δ |
|---:|---|---:|---:|---:|---:|---:|
| 1 | Vice Got a Price! | 4 | 4 | 0.10 | 0.10 | — |
| 2 | Just Like Paradise | 638 | 3868 | 100.00 | 100.00 | — |
| 3 | Paradise Lost | 8 | 11 | 0.21 | 0.28 | +0.07 |
| 4 | T**s Ass Drug Money | 7 | 9 | 0.18 | 0.23 | +0.05 |
| 5 | Vice City, Baby! | 7 | 9 | 0.18 | 0.23 | +0.05 |
| 6 | Top Of The World, Ma | 7 | 9 | 0.18 | 0.23 | +0.05 |
| 7 | You Gotta Know When to Get Off | 7 | 9 | 0.18 | 0.23 | +0.05 |
| 8 | Trust | 7 | 9 | 0.18 | 0.23 | +0.05 |
| 9 | Break the Bank | 7 | 9 | 0.18 | 0.23 | +0.05 |
| 10 | Family Matters | 7 | 9 | 0.18 | 0.23 | +0.05 |
| 11 | DWNFALL | 7 | 9 | 0.18 | 0.23 | +0.05 |
| 12 | Hi-Jacked | 7 | 9 | 0.18 | 0.23 | +0.05 |
| 13 | Snow Storm | 7 | 9 | 0.18 | 0.23 | +0.05 |
| 14 | A Long Road | 4 | 4 | 0.10 | 0.10 | — |
| 15 | Cunning Stunts | 4 | 4 | 0.10 | 0.10 | — |
| 16 | Master of None | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 17 | The Shootist | 4 | 4 | 0.10 | 0.10 | — |
| 18 | Top Fun | 4 | 4 | 0.10 | 0.10 | — |
| 19 | Earn Cash, Not Kudos | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 20 | Baited My Tackle | 13 | 18 | 0.34 | 0.47 | +0.13 |
| 21 | Stick Fiddler | 6 | 8 | 0.16 | 0.21 | +0.05 |
| 22 | Road to Rehabilitation | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 23 | This Was No Boat Accident | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 24 | The Lone Rider | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 25 | Strangers & Freaks | 4 | 4 | 0.10 | 0.10 | — |
| 26 | Supply & Demand | 4 | 4 | 0.10 | 0.10 | — |
| 27 | Spin On This! | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 28 | Positive Mental Attitude | 4 | 4 | 0.10 | 0.10 | — |
| 29 | Fair Game | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 30 | Don't Touch My Deck | 4 | 4 | 0.10 | 0.10 | — |
| 31 | You WAiNKer! | 4 | 4 | 0.10 | 0.10 | — |
| 32 | One Last Thing | 4 | 4 | 0.10 | 0.10 | — |
| 33 | Hot Together | 6 | 8 | 0.16 | 0.21 | +0.05 |
| 34 | Retail Therapy | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 35 | Whip It Good | 8 | 11 | 0.21 | 0.28 | +0.07 |
| 36 | Gunslinger | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 37 | Catch Me If You Can | 6 | 8 | 0.16 | 0.21 | +0.05 |
| 38 | Challenging Tank | 10 | 14 | 0.26 | 0.36 | +0.10 |
| 39 | Sneakthief | 6 | 8 | 0.16 | 0.21 | +0.05 |
| 40 | Maximum Withdrawal | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 41 | A Classic Blitz Play | 6 | 8 | 0.16 | 0.21 | +0.05 |
| 42 | The Goodtime State | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 43 | Pest Control | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 44 | In The Beginning… | 6 | 8 | 0.16 | 0.21 | +0.05 |
| 45 | Capital Offense | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 46 | Let’s Go Bowling | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 47 | Personal Best | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 48 | Actions Speak Louder | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 49 | Bad Luck, I Guess | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 50 | The Truth Is Out There | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 51 | Ten Pin | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 52 | Dime on the Dollar | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 53 | Treat Yo Self | 6 | 8 | 0.16 | 0.21 | +0.05 |
| 54 | Little Boxes | 5 | 7 | 0.13 | 0.18 | +0.05 |
| 55 | On the Spot | 5 | 7 | 0.13 | 0.18 | +0.05 |

Changed groups, by base earners: e=5 (22 trophies) 0.13 → 0.18;
e=6 (7) 0.16 → 0.21; e=7 (10) 0.18 → 0.23; e=8 (2) 0.21 → 0.28;
e=10 (1) 0.26 → 0.36; e=13 (1) 0.34 → 0.47.

### V2 tests

- **Practice run** (kit `input/`, fresh output dirs): `p00.out` and
  `p01.out` written, 2,210 bytes each; format validated (55 rows, ids
  1..55, 5 quantiles, all in [0, 100], non-decreasing); **p00 and p01
  byte-identical**; a second run produced **byte-identical** outputs
  (`cmp` clean). Runtime 0.070 s wall for both cases together.
- **Branch B synthetic test:** a fabricated case with **4 states at 24 h
  gaps** (players 3,868 → 9,000 → 16,000 → 24,000; two reads per state;
  release 2026-11-19; last state 2026-11-23 04:30 UTC; target
  2026-11-27 16:30 UTC, ~4.5 days after the last state). No crash, valid
  55-row output, deterministic across runs. Audit: branch B, cadence
  24.0 h, **`t*` = 2026-11-27 04:30 UTC** — a recalculation time ≤ target,
  not the target itself — projection horizon 4.0 days. Direction checks:
  - *Fast-rising story trophy* (id 3, rates 0.21 → 10.67 → 21.00 →
    31.67): median **47.79**, above the last rate, following the
    trajectory up; row [6.1779, 23.7429, 47.7908, 72.9083, 92.7141].
  - *Flat grind trophy* (id 15, rates 0.10 / 0.10 / 0.11 / 0.10): median
    **0.1035** — stays at the flat rate; row
    [0.0181, 0.0506, 0.1035, 0.2114, 0.5906].
  - *Gentle riser* (id 20, rates 0.34 → 0.87 → 1.14 → 1.30): median
    **2.31**.
  - *Fixed rows:* universal trophy (id 2, earners = players in every
    state) → `[99.9, 99.99, 100, 100, 100]`; zero-earner trophy (id 1)
    → `[0, 0, 0.01, 0.05, 0.2]`.
  - Runtime 0.062 s for the case.
- **Answering-state edge case:** the same synthetic history with the
  target moved to 2026-11-23 20:00 UTC (before the next recalculation)
  picks `t*` = the last state time (2026-11-23 04:30 UTC) with a 0.0-day
  horizon, exactly as specified.

## V3 — baked live states in Branch B

The winners' method, adopted 21 Nov: snapshot the live Exophase page at
each daily recalculation and anchor the trajectory fit on those real
states. Two rates-only snapshots are baked into `main.py` as
`BAKED_STATES` (55 rates each, case-file trophy order; anchors verified:
id 2 = 100.00, id 3 = Chapter 1, id 20 = fishing, id 38 = Challenging
Tank; values copied programmatically from
`baked-states-note.md`, not retyped):

- **S2 — 2026-11-20T04:30:00Z** (page crawled 20 Nov 12:33 UTC): id 3
  7.99, id 20 10.57, id 8 2.52.
- **S3 — 2026-11-21T04:30:00Z** (page crawled 21 Nov 05:55 UTC =
  12:55 WIB, fresh snapshot this run): id 3 18.02, id 20 16.73, id 8
  7.98. S3 differs from S2 on **32 of 55** trophies (note: the working
  note says 41 — a recount of the two baked vectors gives 32; the rates
  themselves are identical in both sources).

The page's players-tracked header was absent from both crawls, so baked
states carry rates only (`players`/`earners` = None) and feed Branch B's
rate-trajectory fit, never Branch A.

**Merge rules** (`merge_baked_states`, called at the top of `branch_b`
only): a baked state joins the state list in time order unless its rate
vector is within `BAKED_DEDUPE_TOL = 0.02`pp on **every** trophy of an
existing state (the case history already contains that recalculation).
The audit records `baked_states_added` / `baked_states_total`. Two
None-safety guards, both inert on the no-bake path: the universal-trophy
check confirms universality from the states that carry earners when the
last state is a baked one, and the zero-earner check ignores `None`
earners. Branch A, `solve_case`'s single-state routing, the fallback and
the sanitize pass are untouched.

### V3 tests

- **(a) Practice output byte-identical to v2.** v2's output was
  regenerated from git commit `e57740d` into a temp dir; v3's practice
  run matches it exactly: `p00.out` and `p01.out` both md5
  `ebbfc3bd44b7bbc7556702e355c21495` under v2 and v3 (`cmp` clean).
- **(b) Baked states join the fit.** Synthetic case with a 2-state
  history only (launch 638 players + 20 Nov state at 3,868 players,
  target 2026-11-26T00:00Z): v3 audit `branch B, states 3,
  baked_states_added 1, cadence 26.33 h, t* 2026-11-25T13:48:22Z`
  (S2 deduped against the matching case state, S3 joined); the no-bake
  (v2) run on the same case fits 2 states. Medians move on **27 of 55**
  trophies, e.g. id 3: 11.7789 → 24.2177, id 20: 14.8348 → 22.5676.
  The universal row survives with baked S3 as the last merged state
  (id 2 → `[99.9, 99.99, 100, 100, 100]`).
- **(c) Dedupe keeps output equal to no-bake.** Synthetic case with a
  complete history (launch + 20 Nov + 21 Nov at 9,000 players + a
  22 Nov state at 15,000): v3 audit `states 4, baked_states_added 0`
  and the v3 output is **byte-identical** to the v2 (no-bake) output on
  the same case.
- **Zero-row guard** (extra): a synthetic case with trophy 1 at 0.00 in
  every real state still yields the fixed row
  `[0, 0, 0.01, 0.05, 0.2]` with baked states present.
- **(d) Determinism + runtime.** Practice run repeated: byte-identical
  outputs; Branch B synthetic case run twice: byte-identical. Runtime
  54–69 ms wall for the 2-case practice run, ~0.07 s per 1-case
  Branch B run including interpreter start (limit 8 s per case).
