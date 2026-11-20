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
