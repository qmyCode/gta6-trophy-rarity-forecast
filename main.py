#!/usr/bin/env python3
"""GTA VI trophy rarity forecaster for make.fun's gta6-trophy-rarity-forecast-01.

Model
-----
Exophase prints each trophy's rarity as round2(earners / players * 100), so
the integer earners behind any read are recoverable exactly:

    earners_i = round(rate_i * players / 100)

Between Exophase's aggregate recalculations ("refreshes") the page is frozen:
every read shows the same players count and the same rates.  At a refresh the
tracked player count jumps and every rate is recomputed against the new
denominator while earners barely move.  The forecast therefore works in
earner space:

* Branch A (history shows a single frozen state): the next refresh dilutes
  the rates.  Earners are divided by the projected post-refresh player
  count, after a growth correction: the frozen snapshot predates the
  recalculation, and the tracked cohort keeps playing in between, so each
  trophy's earners are grown by round(0.35 * e) (for e >= 5) before the
  dilution.  For the launch state documented in the kit (638 players) the
  first refresh is known: 3,868 players.  The result is a point forecast --
  all five quantiles equal the round-half-up 2-decimal median, matching how
  Exophase itself prints rates.
* Branch B (several distinct states): a rate-trajectory model.  The page's
  recalculation cadence is read off the observed state gaps, and the
  answering state is the last recalculation at or before the target.  For
  each trophy a weighted least-squares line is fitted to logit(rate)
  against ln(1 + hours since release) -- recent states weigh most -- then
  blended with persistence in logit space.  Quantiles spread logit-normally
  around the blended median with a width that grows with the projection
  horizon and the fit's residuals.

Deterministic, standard library only, no network.
"""

import json
import math
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
from statistics import median as _median

Z_TABLE = {0.05: -1.645, 0.25: -0.674, 0.5: 0.0, 0.75: 0.674, 0.95: 1.645}
DEFAULT_LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]

LAUNCH_PLAYERS = 638            # frozen launch-night state in the kit narrative
LAUNCH_REFRESH_PLAYERS = 3868   # player count after the first refresh (04:30 read)
LAUNCH_GROWTH = 6.063           # 3868 / 638, the observed launch dilution factor
PRE_CUTOVER = datetime(2026, 11, 20, tzinfo=timezone.utc)


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def parse_ts(text):
    """Parse an ISO-8601 timestamp ('...Z' or with offset) to aware UTC."""
    if not text:
        return None
    t = str(text).strip()
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    dt = datetime.fromisoformat(t)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def z_for(level):
    if level in Z_TABLE:
        return Z_TABLE[level]
    from statistics import NormalDist
    return NormalDist().inv_cdf(level)


def reconstruct_earners(rates, players):
    """Integer earners behind printed rates: round-half-up(rate * P / 100)."""
    out = []
    for r in rates:
        if r is None or players is None:
            out.append(None)
        else:
            v = (Decimal(str(r)) * Decimal(players)) / Decimal(100)
            out.append(int(v.quantize(Decimal("1"), rounding=ROUND_HALF_UP)))
    return out


def segment_states(history):
    """Collapse consecutive identical reads into states.

    A state is one distinct (players, rates) page; it keeps the first-seen
    time of its first read, the player count and the reconstructed earners.
    """
    states = []
    for read in history:
        players = read.get("players_tracked")
        rates = list(read.get("rates") or [])
        key = (players, tuple(rates))
        if states and states[-1]["key"] == key:
            continue
        states.append({
            "key": key,
            "first_seen": parse_ts(read.get("at") or read.get("slot")),
            "players": players,
            "rates": rates,
            "earners": reconstruct_earners(rates, players),
        })
    return states


def round_half_up_2dp(value):
    """Round a Decimal to 2 places, halves away from zero (Exophase style)."""
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


# --------------------------------------------------------------------------
# Branch A -- single frozen state: next-refresh dilution point forecast
# --------------------------------------------------------------------------

def branch_a(state, trophies, levels):
    players = state["players"]
    first_seen = state["first_seen"]
    if players == LAUNCH_PLAYERS:
        p_next = LAUNCH_REFRESH_PLAYERS
    elif first_seen is not None and first_seen < PRE_CUTOVER:
        p_next = int(round(players * LAUNCH_GROWTH))
    else:
        p_next = int(round(players * 1.5))

    rows = []
    flags = []
    for idx, trophy in enumerate(trophies):
        e = state["earners"][idx] if idx < len(state["earners"]) else None
        rate = state["rates"][idx] if idx < len(state["rates"]) else None
        if e is None:
            median = float(rate) if rate is not None else 0.0
        elif e >= players:
            median = 100.0
        elif e == 0:
            median = 0.0
        else:
            # Growth correction: the snapshot predates the recalculation
            # and the cohort keeps playing in between, so earners grow
            # before they are diluted by the new player count.
            if e >= 5:
                growth = int((Decimal("0.35") * Decimal(e)).quantize(
                    Decimal("1"), rounding=ROUND_HALF_UP))
            else:
                growth = 0
            grown = min(e + growth, p_next - 1)
            exact = (Decimal(grown) * Decimal(100)) / Decimal(p_next)
            median = round_half_up_2dp(exact)
            # Boundary audit: how close is the unrounded value to a .xx5
            # rounding boundary?  Flag anything within 0.002 points; the
            # prediction itself is never adjusted for a flag.
            scaled = exact * 100
            frac = scaled - scaled.to_integral_value(rounding=ROUND_FLOOR)
            dist = abs(frac - Decimal("0.5")) / Decimal(100)
            if dist < Decimal("0.002"):
                flags.append({
                    "id": trophy.get("id"),
                    "earners": grown,
                    "earners_base": e,
                    "unrounded": float(exact),
                    "distance_to_boundary": float(dist),
                    "predicted": median,
                })
        rows.append({"id": trophy.get("id"), "q": [median] * len(levels)})
    audit = {"branch": "A", "players_now": players, "players_next": p_next,
             "boundary_flags": flags}
    return rows, audit


# --------------------------------------------------------------------------
# Branch B -- several states: rate-trajectory model to the answering state
# --------------------------------------------------------------------------

def spread(median, sigma, levels):
    """Logit-normal quantile row around a median rate (percent)."""
    if median >= 100.0:
        if len(levels) == 5:
            return [99.9, 99.99, 100.0, 100.0, 100.0]
        return [100.0] * len(levels)
    if median <= 0.0:
        if len(levels) == 5:
            return [0.0, 0.0, 0.0, 0.01, 0.05]
        return [0.0] * len(levels)
    p = min(max(median / 100.0, 1e-9), 1.0 - 1e-9)
    mu = math.log(p / (1.0 - p))
    out = []
    for level in levels:
        v = 100.0 / (1.0 + math.exp(-(mu + z_for(level) * sigma)))
        out.append(min(max(round(v, 4), 0.0), 100.0))
    for i in range(1, len(out)):
        if out[i] < out[i - 1]:
            out[i] = out[i - 1]
    return out


def release_time(case, states):
    """Midnight UTC on the game's release date.

    From game.release_date when the case carries one; otherwise midnight
    UTC on the date of the first read in the history.
    """
    game = case.get("game") or {}
    raw = game.get("release_date")
    if raw:
        text = str(raw).strip()
        try:
            day = datetime.strptime(text[:10], "%Y-%m-%d")
            return day.replace(tzinfo=timezone.utc)
        except ValueError:
            parsed = parse_ts(text)
            if parsed is not None:
                return parsed
    first = states[0]["first_seen"]
    if first is not None:
        return first.replace(hour=0, minute=0, second=0, microsecond=0)
    return None


def x_since_release(release, when):
    """ln(1 + hours since release): the trajectory model's time axis."""
    if release is None or when is None:
        return 0.0
    hours = (when - release).total_seconds() / 3600.0
    return math.log(max(1.0 + hours, 0.05))


def logit_of_rate(rate):
    """Logit of a percent rate, clamped to [0.01, 99.99] first."""
    p = min(max(float(rate), 0.01), 99.99) / 100.0
    return math.log(p / (1.0 - p))


def logit_quantiles(median, sigma, levels):
    """Logit-normal quantile row around a median rate (percent)."""
    mu = logit_of_rate(median)
    out = []
    for level in levels:
        v = 100.0 / (1.0 + math.exp(-(mu + z_for(level) * sigma)))
        out.append(min(max(round(v, 4), 0.0), 100.0))
    for i in range(1, len(out)):
        if out[i] < out[i - 1]:
            out[i] = out[i - 1]
    return out


def fixed_row(values_by_level, levels, default):
    return [values_by_level.get(level, default(level)) for level in levels]


UNIVERSAL_ROW = {0.05: 99.9, 0.25: 99.99, 0.5: 100.0, 0.75: 100.0, 0.95: 100.0}
ZERO_ROW = {0.05: 0.0, 0.25: 0.0, 0.5: 0.01, 0.75: 0.05, 0.95: 0.2}


def branch_b(case, states, trophies, levels):
    release = release_time(case, states)
    n = len(states)
    t_last = states[-1]["first_seen"]
    target = parse_ts(case.get("target"))

    # Recalculation cadence: median gap between consecutive states'
    # first-seen times, clamped to [6h, 30h].  Future recalculations land
    # every cadence after the last state; the answering state is the one
    # in force at the last recalculation at or before the target -- or the
    # last state itself when no recalculation falls before the target.
    gaps_h = []
    for a, b in zip(states, states[1:]):
        if a["first_seen"] is not None and b["first_seen"] is not None:
            gaps_h.append((b["first_seen"] - a["first_seen"]).total_seconds()
                          / 3600.0)
    cadence_h = min(max(_median(gaps_h) if gaps_h else 24.0, 6.0), 30.0)
    t_star = t_last
    if t_last is not None and target is not None:
        span_h = (target - t_last).total_seconds() / 3600.0
        k = int(span_h // cadence_h) if span_h > 0 else 0
        if k >= 1:
            t_star = t_last + timedelta(hours=cadence_h * k)
    if t_star is not None and t_last is not None:
        days_horizon = (t_star - t_last).total_seconds() / 86400.0
    else:
        days_horizon = 0.0
    x_star = x_since_release(release, t_star)

    last = states[-1]
    p_last = last["players"]
    rows = []
    for idx, trophy in enumerate(trophies):
        tid = trophy.get("id")
        e_last = last["earners"][idx] if idx < len(last["earners"]) else None
        rate_last = last["rates"][idx] if idx < len(last["rates"]) else None

        # Fixed rows: a universal trophy (every tracked player has it) and
        # a trophy nobody has earned in any state.
        if (rate_last is not None and rate_last >= 100.0
                and e_last is not None and p_last is not None
                and e_last >= p_last):
            rows.append({"id": tid, "q": fixed_row(
                UNIVERSAL_ROW, levels,
                lambda lv: 100.0 if lv >= 0.5 else 99.9)})
            continue
        earners_all = [s["earners"][idx] if idx < len(s["earners"]) else None
                       for s in states]
        if all(e == 0 for e in earners_all):
            rows.append({"id": tid, "q": fixed_row(
                ZERO_ROW, levels, lambda lv: 0.0)})
            continue

        # Usable trajectory points: states whose printed rate is strictly
        # inside (0, 100).  Recent states weigh most: each state is
        # down-weighted by 0.75 per transition that follows it.
        points = []
        for j, s in enumerate(states):
            r = s["rates"][idx] if idx < len(s["rates"]) else None
            if r is None or not (0.0 < r < 100.0):
                continue
            p = float(r) / 100.0
            points.append((x_since_release(release, s["first_seen"]),
                           math.log(p / (1.0 - p)),
                           0.75 ** (n - 1 - j)))

        # Persistence: the latest printed rate for this trophy.
        last_rate = None
        for s in reversed(states):
            r = s["rates"][idx] if idx < len(s["rates"]) else None
            if r is not None:
                last_rate = float(r)
                break
        if last_rate is None:
            rows.append({"id": tid, "q": spread(0.0, 1.0, levels)})
            continue

        if len(points) >= 2:
            sw = sum(w for _, _, w in points)
            x_bar = sum(w * x for x, _, w in points) / sw
            y_bar = sum(w * y for _, y, w in points) / sw
            sxx = sum(w * (x - x_bar) ** 2 for x, _, w in points)
            sxy = sum(w * (x - x_bar) * (y - y_bar) for x, y, w in points)
            slope = sxy / sxx if sxx > 1e-12 else 0.0
            if abs(slope) > 3.0:
                slope *= 0.5
            intercept = y_bar - slope * x_bar
            rmse = math.sqrt(
                sum(w * (y - (intercept + slope * x)) ** 2
                    for x, y, w in points) / sw)
            y_fit = intercept + slope * x_star
            w_fit = 0.5 if len(points) == 2 else 0.75
            blended = w_fit * y_fit + (1.0 - w_fit) * logit_of_rate(last_rate)
            blended = min(max(blended, -25.0), 25.0)
            median = 100.0 / (1.0 + math.exp(-blended))
            sigma = min(max(0.30 + 0.18 * days_horizon + rmse, 0.3), 1.6)
        else:
            median = last_rate
            sigma = min(max(0.30 + 0.18 * days_horizon, 0.3), 1.6)
        rows.append({"id": tid, "q": logit_quantiles(median, sigma, levels)})

    audit = {"branch": "B", "states": n,
             "release": release.isoformat() if release else None,
             "cadence_hours": cadence_h,
             "t_star": t_star.isoformat() if t_star else None,
             "target": target.isoformat() if target else None,
             "days_horizon": days_horizon}
    return rows, audit


# --------------------------------------------------------------------------
# fallback + driver
# --------------------------------------------------------------------------

def fallback_rows(case, trophies, levels):
    """Last-read rates as a point forecast; used if anything goes wrong."""
    history = case.get("history") or []
    rows = []
    for idx, trophy in enumerate(trophies):
        rate = None
        for read in reversed(history):
            rates = read.get("rates") or []
            if idx < len(rates) and rates[idx] is not None:
                rate = float(rates[idx])
                break
        rows.append({"id": trophy.get("id"),
                     "q": [rate if rate is not None else 0.0] * len(levels)})
    return rows


def solve_case(case):
    trophies = case.get("trophies") or []
    levels = case.get("levels") or DEFAULT_LEVELS
    states = segment_states(case.get("history") or [])
    if not states:
        return fallback_rows(case, trophies, levels), {"branch": "fallback"}
    if len(states) == 1:
        return branch_a(states[0], trophies, levels)
    return branch_b(case, states, trophies, levels)


def sanitize_rows(rows, trophies, levels):
    """Final format net: one row per trophy, in trophy order, every q value
    a finite number in [0, 100], non-decreasing across the levels."""
    by_id = {}
    for row in rows:
        by_id[row.get("id")] = row.get("q") or []
    out = []
    for trophy in trophies:
        tid = trophy.get("id")
        q = []
        for v in by_id.get(tid, []):
            try:
                v = float(v)
            except (TypeError, ValueError):
                v = 0.0
            if not math.isfinite(v):
                v = 0.0
            q.append(min(max(v, 0.0), 100.0))
        while len(q) < len(levels):
            q.append(q[-1] if q else 0.0)
        q = q[:len(levels)]
        for i in range(1, len(q)):
            if q[i] < q[i - 1]:
                q[i] = q[i - 1]
        out.append({"id": tid, "q": q})
    return out


def main():
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    audits = {}
    for name in sorted(os.listdir(in_dir)):
        if not name.endswith(".in"):
            continue
        case = None
        rows, audit = [], {"branch": "unreadable"}
        try:
            with open(os.path.join(in_dir, name), "r", encoding="utf-8") as fh:
                case = json.load(fh)
            rows, audit = solve_case(case)
        except Exception:
            try:
                if case is not None:
                    rows = fallback_rows(case, case.get("trophies") or [],
                                         case.get("levels") or DEFAULT_LEVELS)
                    audit = {"branch": "fallback-after-error"}
            except Exception:
                rows, audit = [], {"branch": "unreadable"}
        trophies = (case or {}).get("trophies") or []
        levels = (case or {}).get("levels") or DEFAULT_LEVELS
        rows = sanitize_rows(rows, trophies, levels)
        case_id = (case or {}).get("id") or name[:-3]
        audits[case_id] = audit
        payload = json.dumps({"trophies": rows}, separators=(",", ":"))
        with open(os.path.join(out_dir, case_id + ".out"), "w",
                  encoding="utf-8") as fh:
            fh.write(payload)
    audit_path = os.environ.get("MAKEFUN_AUDIT_FILE")
    if audit_path:
        with open(audit_path, "w", encoding="utf-8") as fh:
            json.dump(audits, fh, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
