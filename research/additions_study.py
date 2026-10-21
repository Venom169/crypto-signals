"""Test ideas from the liquidity literature as additions to the sweep signal.

    python research/additions_study.py   -> research/results/ADDITIONS.md

Each idea is fixed in advance and scored the same way as the filter table in
RESULTS.md: edge versus random entries (same New York hour, direction, stop and
target) in ATR units, on the three separate samples. An idea only counts if it
helps in all three.

Filters keep the sweep entry and only select signals. Confirmations move the
entry to a later bar. Targets change where the trade is closed.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from run_study import COST, MAX_BARS, RAND_PER_SIGNAL, md_table, sample
from sweep_engine import (DATA, add_features, build_levels, daily_table, find_sweeps, ny_hour, random_baseline,
                          simulate, stop_distance, unix)

RESULTS = Path(__file__).resolve().parent / "results"
STOP, TARGET = ("atr", 0.15), 2.0   # stop behind the wick + 0.15 ATR, target 2 ATR (= $15 on 15m)


def load_silver(tf):
    df = pd.read_csv(DATA / f"xagusd_{tf}.csv")
    df.index = pd.to_datetime(df["t"], unit="s", utc=True)
    return df[["high", "low"]]


def _ext(x, f):
    return f(x.tolist())


def edges(base, sig, S, T):
    """Per-trade result minus the mean of random entries, in ATR units."""
    res = simulate(base, sig["i"].to_numpy().astype(int), sig["dir"].to_numpy(), S, T, MAX_BARS, COST)
    rb = random_baseline(base, sig, S, T, MAX_BARS, COST, per_signal=RAND_PER_SIGNAL)
    rand = rb["pnl"].to_numpy().reshape(len(sig), RAND_PER_SIGNAL).mean(axis=1)
    return (res["pnl"].to_numpy() - rand) / sig["atr"].to_numpy(), res


def add_context(base, sig, h1, tf):
    """Features from the literature, all known at the signal bar's close."""
    sig = sig.copy()
    i = sig["i"].to_numpy()
    d = sig["dir"].to_numpy()
    h, l, v = base["high"].to_numpy(), base["low"].to_numpy(), base["volume"].to_numpy()
    t_open = pd.DatetimeIndex(sig["time"])

    # Premium / discount of the previous day's range (ICT PD arrays): sell above the middle, buy below.
    days = daily_table(h1)
    mid = ((days["high"] + days["low"]) / 2).to_numpy()
    ends = days["end"].to_numpy()
    k = np.searchsorted(ends, unix(t_open), side="right") - 1
    sig["prev_mid"] = np.where(k >= 0, mid[np.maximum(k, 0)], np.nan)
    sig["premium_ok"] = ((d == -1) & (sig["entry"] > sig["prev_mid"])) | ((d == 1) & (sig["entry"] < sig["prev_mid"]))

    # New York midnight open ("true day open"): sell above it, buy below it.
    ny = base.index.tz_convert("America/New_York")
    is_mid = (ny.hour == 0) & (ny.minute == 0)
    mid_open = pd.Series(np.where(is_mid, base["open"].to_numpy(), np.nan), index=base.index).ffill().to_numpy()
    sig["midnight_ok"] = ((d == -1) & (sig["entry"] > mid_open[i])) | ((d == 1) & (sig["entry"] < mid_open[i]))

    # Volume (tick volume) on the sweep bar against the 20 bars before it.
    avg = pd.Series(v).rolling(20).mean().shift(1).to_numpy()
    sig["vol_ratio"] = v[i] / avg[i]

    # Time windows: ICT killzones and silver bullet hours (New York time), LBMA auctions (London time).
    hr = ny_hour(t_open)
    sig["killzone"] = ((hr >= 2) & (hr < 5)) | ((hr >= 7) & (hr < 10))
    sig["silver_bullet"] = np.isin(hr, [3, 10, 14])
    lon = t_open.tz_convert("Europe/London")
    mins = lon.hour * 60 + lon.minute
    sig["lbma"] = ((mins >= 600) & (mins < 660)) | ((mins >= 870) & (mins < 930))

    # SMT with silver: gold makes a new 20-bar extreme over the sweep bars, silver does not.
    sv = load_silver(tf).reindex(base.index)
    sh, sl = sv["high"].to_numpy(), sv["low"].to_numpy()
    smt, look = [], 20
    for ii, dd in zip(i, d):
        a = ii - 2  # the sweep may have started up to two bars back (candle sweeps)
        if a - look < 0:
            smt.append(False)
            continue
        if dd == -1:   # tops swept
            g_new = h[a:ii + 1].max() > h[a - look:a].max()
            s_new = _ext(sh[a:ii + 1], max) > _ext(sh[a - look:a], max) if np.isfinite(sh[a - look:ii + 1]).all() else True
        else:
            g_new = l[a:ii + 1].min() < l[a - look:a].min()
            s_new = _ext(sl[a:ii + 1], min) < _ext(sl[a - look:a], min) if np.isfinite(sl[a - look:ii + 1]).all() else True
        smt.append(bool(g_new and not s_new))
    sig["smt"] = smt
    return sig


def confirmed(base, sig, kind, wait):
    """Move the entry to a later bar that confirms the reversal (ICT displacement / structure shift).

    fvg: a three-bar fair value gap opens in the trade direction.
    mss: a close beyond the extreme of the six bars before the sweep (the swing that led into it).
    The idea is dropped if price reaches the stop first.
    """
    o, h, l, c = (base[x].to_numpy() for x in ("open", "high", "low", "close"))
    rows = []
    for _, r in sig.iterrows():
        i, d, ext = int(r["i"]), int(r["dir"]), r["ext"]
        stop = ext - d * 0.15 * r["atr"]
        swing = l[max(i - 6, 0):i + 1].min() if d == -1 else h[max(i - 6, 0):i + 1].max()
        for j in range(i + 1, min(i + 1 + wait, len(base))):
            if (d == -1 and h[j] >= stop) or (d == 1 and l[j] <= stop):
                break
            ok = (h[j] < l[j - 2] if d == -1 else l[j] > h[j - 2]) if kind == "fvg" else \
                 (c[j] < swing if d == -1 else c[j] > swing)
            if ok:
                r2 = r.copy()
                r2["i"], r2["entry"] = j, c[j]
                r2["risk_wick"] = abs(ext - c[j])
                r2["ny_hour"] = int(ny_hour(pd.DatetimeIndex([base.index[j]]))[0])
                rows.append(r2)
                break
    return pd.DataFrame(rows)


def opposite_targets(base, levels, sig):
    """Distance to the nearest unswept level on the other side (the 'draw on liquidity')."""
    ts = unix(base.index)
    h, l = base["high"].to_numpy(), base["low"].to_numpy()
    lv = [(L.price, L.side, int(np.searchsorted(ts, L.start)), L.end) for L in levels]
    out = []
    for _, r in sig.iterrows():
        i, d, e = int(r["i"]), int(r["dir"]), r["entry"]
        best = np.nan
        for p, side, a, end in lv:
            if side != d or a > i or end <= ts[i]:
                continue                        # wrong side, not known yet or expired
            if (d == 1 and p <= e) or (d == -1 and p >= e):
                continue
            seg = h[a:i + 1] > p if side == 1 else l[a:i + 1] < p
            if seg.any():
                continue                        # already taken
            dist = abs(p - e)
            best = dist if np.isnan(best) else min(best, dist)
        out.append(best)
    return np.array(out)


def run():
    rows, samples = [], {}
    for name in ("15m", "30m", "1h"):
        base, h1, h4 = sample(name)
        levels = build_levels(base, h1, h4, base_k=5)
        sig, _ = find_sweeps(base, levels, candle_bars=2)
        sig = add_features(sig, base, h1, h4)
        sig = add_context(base, sig, h1, name)
        S, T = stop_distance(sig, STOP), TARGET * sig["atr"].to_numpy()
        sig["edge"], _ = edges(base, sig, S, T)
        samples[name] = dict(base=base, sig=sig, levels=levels)

    def row(label, group, per_sample):
        r = {"idea": label, "type": group}
        pooled = []
        for name, e in per_sample.items():
            e = pd.Series(e).dropna()
            r[f"{name} n"] = len(e)
            r[f"{name} edge"] = e.mean() if len(e) else np.nan
            pooled.append(e)
        p = pd.concat(pooled)
        r["pooled edge"] = p.mean()
        r["pooled t"] = p.mean() / (p.std() / np.sqrt(len(p))) if len(p) > 2 else np.nan
        r["all 3 positive"] = "yes" if all(r[f"{n} edge"] > 0 for n in per_sample) else ""
        return r

    filt = {
        "all sweeps (baseline)": lambda s: s["i"] >= 0,
        "premium/discount of yesterday's range": lambda s: s["premium_ok"],
        "against premium/discount": lambda s: ~s["premium_ok"],
        "beyond the NY midnight open": lambda s: s["midnight_ok"],
        "volume spike (>1.5x the 20-bar mean)": lambda s: s["vol_ratio"] > 1.5,
        "low volume sweep (<1x)": lambda s: s["vol_ratio"] < 1.0,
        "ICT killzones (London 2-5, NY 7-10 NY time)": lambda s: s["killzone"],
        "silver bullet hours (3, 10, 14 NY)": lambda s: s["silver_bullet"],
        "LBMA auction windows (10:30, 15:00 London)": lambda s: s["lbma"],
        "SMT: silver did not confirm": lambda s: s["smt"],
        "with trend + SMT": lambda s: s["smt"] & (s["with_ema50_1h" if "with_ema50_1h" in s else "with_ema50_4h"] == 1),
        "grade A": lambda s: s["grade"] == "A",
        "grade A + premium/discount": lambda s: (s["grade"] == "A") & s["premium_ok"],
    }
    for label, f in filt.items():
        rows.append(row(label, "filter", {n: v["sig"].loc[f(v["sig"]), "edge"] for n, v in samples.items()}))

    for kind, wait, label in (("fvg", 4, "confirm: FVG (displacement) within 4 bars"),
                              ("mss", 6, "confirm: structure shift (MSS) within 6 bars")):
        per = {}
        for name, v in samples.items():
            cs = confirmed(v["base"], v["sig"], kind, wait)
            S, T = stop_distance(cs, STOP), TARGET * cs["atr"].to_numpy()
            per[name], _ = edges(v["base"], cs, S, T)
        rows.append(row(label, "entry", per))

    per, per_cap = {}, {}
    for name, v in samples.items():
        sig = v["sig"]
        dist = opposite_targets(v["base"], v["levels"], sig) / sig["atr"].to_numpy()
        ok = (dist >= 1.0) & (dist <= 5.0)
        s2 = sig[ok]
        S, T = stop_distance(s2, STOP), (dist[ok] - 0.1) * s2["atr"].to_numpy()
        per[name], _ = edges(v["base"], s2, S, T)
        S2, T2 = stop_distance(s2, STOP), TARGET * s2["atr"].to_numpy()
        per_cap[name], _ = edges(v["base"], s2, S2, T2)
    rows.append(row("target: nearest opposite liquidity (1-5 ATR away)", "target", per))
    rows.append(row("same signals, fixed 2 ATR target (control)", "target", per_cap))

    per = {}
    for name, v in samples.items():
        sig = v["sig"]
        S = np.maximum(stop_distance(sig, STOP), 2.7 * sig["atr"].to_numpy())   # $20 floor on 15m
        per[name], _ = edges(v["base"], sig, S, 2.7 * sig["atr"].to_numpy())
    rows.append(row("minimum stop 2.7 ATR (~$20) with target 2.7 ATR (~$20)", "stop", per))

    df = pd.DataFrame(rows)
    lines = ["# Additions from the liquidity literature - tested", "",
             "Edge = result minus random entries (same NY hour, direction, stop, target), in ATR units per trade; "
             f"stop behind the wick + 0.15 ATR, target 2 ATR unless stated; cost ${COST}. "
             "Samples: 15m Aug-Oct 2026, 30m Jan-Jul 2026, 1h 2025.", "",
             md_table(df.to_dict("records"), 3), ""]
    (RESULTS / "ADDITIONS.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    run()
