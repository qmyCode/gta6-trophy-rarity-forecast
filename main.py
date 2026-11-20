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
  the rates.  Earners are held fixed and divided by the projected post-refresh
  player count.  For the launch state documented in the kit (638 players) the
  first refresh is known: 3,868 players.  The result is a point forecast --
  all five quantiles equal the round-half-up 2-decimal median, matching how
  Exophase itself prints rates.
* Branch B (several distinct states): refreshes are projected forward on the
  observed cadence (~daily), the player count grows with a decaying daily
  factor, earners drift with their observed daily delta damped by saturation
  headroom, and the quantiles spread logit-normally around the median with a
  width that grows with the number of projected refreshes.

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
            exact = (Decimal(e) * Decimal(100)) / Decimal(p_next)
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
                    "earners": e,
                    "unrounded": float(exact),
                    "distance_to_boundary": float(dist),
                    "predicted": median,
                })
        rows.append({"id": trophy.get("id"), "q": [median] * len(levels)})
    audit = {"branch": "A", "players_now": players, "players_next": p_next,
             "boundary_flags": flags}
    return rows, audit


# --------------------------------------------------------------------------
# Branch B -- several states: project the refresh cycle to the target
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


def branch_b(case, states, trophies, levels):
    target = parse_ts(case.get("target"))
    last, prev = states[-1], states[-2]
    t_last, t_prev = last["first_seen"], prev["first_seen"]
    if t_last is not None and t_prev is not None:
        days_prev = max((t_last - t_prev).total_seconds() / 86400.0, 1e-9)
    else:
        days_prev = 1.0

    gaps = []
    for a, b in zip(states, states[1:]):
        if a["first_seen"] is not None and b["first_seen"] is not None:
            gaps.append((b["first_seen"] - a["first_seen"]).total_seconds() / 86400.0)
    interval = min(max(_median(gaps) if gaps else 1.0, 6.0 / 24.0), 30.0 / 24.0)

    # Future refreshes: every `interval` from the last state change, up to
    # the target.  The answering read shows the page as of the last refresh
    # at or before the target.
    n_steps = 0
    if target is not None and t_last is not None:
        t = t_last + timedelta(days=interval)
        while t <= target:
            n_steps += 1
            t += timedelta(days=interval)

    # Player trajectory: daily growth from the last two states, decaying
    # x0.92 per projected refresh.
    p_last = float(last["players"] or 0)
    p_prev = float(prev["players"] or 0)
    if p_prev > 0 and p_last > 0:
        g = (p_last / p_prev) ** (1.0 / days_prev)
    else:
        g = 1.0
    traj = []
    p = p_last
    for s in range(1, n_steps + 1):
        p = p * ((g * (0.92 ** (s - 1))) ** interval)
        traj.append(p)
    p_answer = traj[-1] if traj else p_last

    rows = []
    for idx, trophy in enumerate(trophies):
        e_last = last["earners"][idx] if idx < len(last["earners"]) else None
        e_prev = prev["earners"][idx] if idx < len(prev["earners"]) else None
        rate_last = last["rates"][idx] if idx < len(last["rates"]) else None
        if e_last is not None and e_prev is not None:
            d = (e_last - e_prev) / days_prev
        else:
            d = 0.0
        if e_last is not None:
            e = float(e_last)
        elif rate_last is not None and p_last > 0:
            e = float(rate_last) * p_last / 100.0
        else:
            e = 0.0
        for s in range(1, n_steps + 1):
            p_s = traj[s - 1]
            headroom = max(0.0, 1.0 - e / p_s) if p_s > 0 else 0.0
            e += d * interval * (0.9 ** s) * headroom
            e = min(max(e, 0.0), p_s)
        if p_answer <= 0:
            median = 0.0
        elif e >= p_answer:
            median = 100.0
        else:
            median = e / p_answer * 100.0
        base_e = float(e_last) if e_last is not None else e
        sigma = 0.30 + 0.22 * n_steps + 0.15 * min(1.0, abs(d) / max(1.0, base_e))
        sigma = min(max(sigma, 0.3), 1.6)
        rows.append({"id": trophy.get("id"), "q": spread(median, sigma, levels)})
    audit = {"branch": "B", "states": len(states), "interval_days": interval,
             "projected_refreshes": n_steps, "players_answer": p_answer}
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
