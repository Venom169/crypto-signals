"""Run the full liquidity-sweep study and write research/results/RESULTS.md.

    python research/run_study.py

Three samples, never mixed:
  * 15m, Aug 2 - Oct 21 2026  - the trader's own chart; targets in dollars ($15 / $20)
  * 30m, Jan 1 - Aug 2 2026   - out of sample (earlier period, rally then crash)
  * 1h,  Jan 1 - Dec 31 2025  - out of sample (strong uptrend year)
Out-of-sample targets and stops are scaled by ATR so "$15 on 15m" means the same
thing on a slower chart: $15 was 2.0x the median 15m ATR(14) in the main sample.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from sweep_engine import (add_features, build_levels, failed_sweeps, find_sweeps, load,
                          mfe_before_invalidation, one_at_a_time, random_baseline, simulate,
                          stop_distance, summarize)

RESULTS = Path(__file__).resolve().parent / "results"
COST = 0.5          # spread + slippage per trade, $ per ounce
MAX_BARS = 32       # time stop
WATCH = 16          # bars to watch for a failed sweep
RAND_PER_SIGNAL = 40


def sample(name):
    h1, h4 = load("1h"), load("4h")
    if name == "15m":
        base = load("15m")
    elif name == "30m":
        base = load("30m").loc["2026-01-01":"2026-08-02 21:00"]
    elif name == "1h":
        base = h1.loc["2025-01-01":"2025-12-31"]
    return base, h1, h4


def targets(sig, unit, x):
    return np.full(len(sig), float(x)) if unit == "$" else x * sig["atr"].to_numpy()


def trade_row(base, sig, rule, unit, t, label):
    S = stop_distance(sig, rule)
    T = targets(sig, unit, t)
    res = simulate(base, sig["i"].to_numpy().astype(int), sig["dir"].to_numpy(), S, T, MAX_BARS, COST)
    rb = random_baseline(base, sig, S, T, MAX_BARS, COST, per_signal=RAND_PER_SIGNAL)
    a, b = summarize(res, S / (S + T)), summarize(rb)
    solo = summarize(res[one_at_a_time(sig, res)])
    return {
        "setup": label, "trades": a["n"], "win %": 100 * a["win"], "coin-flip win %": 100 * a["p_rand_walk"],
        "random-entry win %": 100 * b["win"], "$/trade": a["exp"], "random $/trade": b["exp"],
        "edge $/trade": a["exp"] - b["exp"], "t-stat": (a["exp"] - b["exp"]) / a["se"],
        "PF": a["pf"], "total $ (1 position)": solo["total"], "max DD $ (1 position)": solo["maxdd"],
    }


def study(name, unit):
    base, h1, h4 = sample(name)
    lv = build_levels(base, h1, h4, base_k=5)
    sig, takes = find_sweeps(base, lv, candle_bars=2)
    sig = add_features(sig, base, h1, h4)
    trend_col = "with_ema50_1h" if name != "1h" else "with_ema50_4h"
    if unit == "$":
        buf, fixed, t1, t2, reach = ("wick", 1.0), ("fixed", 10), 15, 20, [10, 15, 20]
        fail_stops = [("fixed", 8), ("fixed", 10), ("fixed", 15)]
    else:
        buf, fixed, t1, t2, reach = ("atr", 0.15), ("fixed_atr", 1.35), 2.0, 2.7, [1.35, 2.0, 2.7]
        fail_stops = [("fixed_atr", 1.1), ("fixed_atr", 1.35), ("fixed_atr", 2.0)]
    u = (lambda x: f"${x:g}") if unit == "$" else (lambda x: f"{x:g}xATR")
    out = {"name": name, "bars": len(base), "from": str(base.index[0])[:10], "to": str(base.index[-1])[:10],
           "median_atr": float(np.median(sig["atr"])), "signals": len(sig)}

    # 1. what happens when a level is taken
    oc = takes["outcome"].map(lambda s: s if s in ("W", "B") else "C").value_counts(normalize=True)
    out["takes"] = {"n": len(takes), "wick back inside %": 100 * oc.get("W", 0),
                    "candle back inside (1-2 bars) %": 100 * oc.get("C", 0), "held beyond %": 100 * oc.get("B", 0)}

    # 2. does price reach the target before breaking the sweep extreme?
    buffer = 1.0 if unit == "$" else 0.15 * np.median(sig["atr"])
    m = mfe_before_invalidation(base, sig, buffer, MAX_BARS)
    S = sig["risk_wick"].to_numpy() + buffer
    out["reach"] = []
    for x in reach:
        T = targets(sig, unit, x)
        out["reach"].append({"target": u(x), "reached before sweep extreme broke %": 100 * np.mean(m >= T),
                             "coin-flip expectation %": 100 * np.mean(S / (S + T))})

    # 2b. even with no stop at all: does price get there more often than from a random entry?
    c, h, l = base["close"].to_numpy(), base["high"].to_numpy(), base["low"].to_numpy()
    hours = pd.DatetimeIndex(base.index).tz_convert("America/New_York").hour.to_numpy()
    rng = np.random.default_rng(1)
    WIN = 16

    def best_move(j, d):
        return (c[j] - l[j + 1:j + 1 + WIN].min()) if d == -1 else (h[j + 1:j + 1 + WIN].max() - c[j])

    sweep_mv = np.array([best_move(i, d) for i, d in zip(sig["i"], sig["dir"])])
    rand_mv, rand_atr = [], []
    for _, r in sig.iterrows():
        pool = np.flatnonzero((hours == r["ny_hour"]) & (np.arange(len(base)) < len(base) - WIN - 1))
        for j in rng.choice(pool, RAND_PER_SIGNAL):
            rand_mv.append(best_move(j, r["dir"]))
            rand_atr.append(r["atr"])
    rand_mv, rand_atr = np.array(rand_mv), np.array(rand_atr)
    out["no_stop"] = []
    for x in reach:
        ts, tr = (x, x) if unit == "$" else (x * sig["atr"].to_numpy(), x * rand_atr)
        out["no_stop"].append({"target": u(x), f"sweep reached it within {WIN} bars %": 100 * np.mean(sweep_mv >= ts),
                               "random entry reached it %": 100 * np.mean(rand_mv >= tr)})

    # 3. fade the sweep (the idea as stated)
    out["fade"] = [trade_row(base, sig, rule, unit, t, f"stop {lab}, target {u(t)}")
                   for rule, lab in [(buf, "behind wick"), (fixed, "fixed " + u(fixed[1]))] for t in (t1, t2)]
    # 4. with vs against the higher-timeframe trend
    out["trend"] = [trade_row(base, sig[sig[trend_col] == s], buf, unit, t1, f"{lab} ({trend_col[5:]})")
                    for s, lab in [(1, "with trend"), (-1, "against trend")]]
    # 5. the sweep fails: trade the break of the sweep extreme
    fs = failed_sweeps(base, sig, WATCH)
    out["failed_share %"] = 100 * len(fs) / len(sig)
    c, h, l = base["close"].to_numpy(), base["high"].to_numpy(), base["low"].to_numpy()
    idx = np.random.default_rng(3).choice(len(base) - WATCH - 1, 4000)
    out["random_bar_retaken %"] = 100 * np.mean([(c[j + 1:j + 1 + WATCH] > h[j]).any() for j in idx] +
                                                [(c[j + 1:j + 1 + WATCH] < l[j]).any() for j in idx])
    out["failed"] = [trade_row(base, fs, rule, unit, t, f"stop {u(rule[1])}, target {u(t)}")
                     for rule in fail_stops for t in (t1, t2)]
    out["failed_trend"] = [trade_row(base, fs[fs[trend_col] == s], fail_stops[1], unit, t2,
                                     f"{lab}, stop {u(fail_stops[1][1])}, target {u(t2)}")
                           for s, lab in [(1, "with trend"), (-1, "against trend")]]
    if name == "15m" and unit == "$":
        export_reference(base, sig)
    return out


def export_reference(base, sig):
    """Every 15m signal with context and outcome - the answer key for the Pine indicator."""
    ref = sig.drop(columns=["lv_prices"]).copy()
    S = stop_distance(sig, ("wick", 1.0))
    ref["stop_dist"] = S
    for t in (15, 20):
        res = simulate(base, sig["i"].to_numpy(), sig["dir"].to_numpy(), S, np.full(len(sig), float(t)), MAX_BARS, COST)
        ref[f"tp{t}_exit"] = res["exit"].to_numpy()
        ref[f"tp{t}_pnl"] = res["pnl"].to_numpy().round(3)
        ref[f"coinflip_tp{t}"] = (S / (S + t)).round(4)
    ref.to_csv(RESULTS / "signals_15m.csv", index=False, float_format="%.4f")


# Filters fixed in advance; one only counts if it helps in every sample.
FILTERS = {
    "all sweeps": lambda s: s["i"] >= 0,
    "wick sweeps only (W)": lambda s: s["type"] == "W",
    "candle sweeps only (C)": lambda s: s["type"] == "C",
    "with HTF trend": lambda s: s["trend"] == 1,
    "against HTF trend": lambda s: s["trend"] == -1,
    "pullback sweep (run-in < 0)": lambda s: s["run_in_atr"] < 0,
    "after a run-up (run-in > 1.5 ATR)": lambda s: s["run_in_atr"] > 1.5,
    "with trend + pullback": lambda s: (s["trend"] == 1) & (s["run_in_atr"] < 0),
    "HTF level (1H/4H/day/week)": lambda s: s["kinds"].str.contains("P1H|P4H|PD|PW"),
    "day/week level (PD/PW)": lambda s: s["kinds"].str.contains("PD|PW"),
    "chart-TF swing only": lambda s: s["kinds"] == "P",
    "Asia range level": lambda s: s["kinds"].str.contains("ASIA"),
    "Asia session": lambda s: s["session"] == "asia",
    "London session": lambda s: s["session"] == "london",
    "NY morning": lambda s: s["session"] == "ny_am",
    "London + NY morning": lambda s: s["session"].isin(["london", "ny_am"]),
    "close mid-bar (0.33-0.66)": lambda s: s["close_loc"].between(0.33, 0.66),
    "strong rejection (close_loc > 0.66)": lambda s: s["close_loc"] > 0.66,
    "big bar (range > 1.5 ATR)": lambda s: s["range_atr"] > 1.5,
    "small bar (range < 1 ATR)": lambda s: s["range_atr"] < 1.0,
    "deep penetration (> 0.5 ATR)": lambda s: s["pen"] > 0.5 * s["atr"],
    "shallow penetration (< 0.15 ATR)": lambda s: s["pen"] < 0.15 * s["atr"],
    "equal highs/lows": lambda s: s["equal_levels"],
    "near a $50 round number": lambda s: s["near_round50"],
    "with trend + London/NY morning": lambda s: (s["trend"] == 1) & s["session"].isin(["london", "ny_am"]),
}


def filter_table():
    """Edge vs random entries, in ATR units, for every filter in every sample (stop behind wick, target 2 ATR)."""
    samples = {}
    for name in ("15m", "30m", "1h"):
        base, h1, h4 = sample(name)
        sig, _ = find_sweeps(base, build_levels(base, h1, h4, base_k=5), candle_bars=2)
        sig = add_features(sig, base, h1, h4)
        S, T = stop_distance(sig, ("atr", 0.15)), 2.0 * sig["atr"].to_numpy()
        res = simulate(base, sig["i"].to_numpy(), sig["dir"].to_numpy(), S, T, MAX_BARS, COST)
        rb = random_baseline(base, sig, S, T, MAX_BARS, COST, per_signal=RAND_PER_SIGNAL)
        rand = rb["pnl"].to_numpy().reshape(len(sig), RAND_PER_SIGNAL).mean(axis=1)
        sig["edge_atr"] = (res["pnl"].to_numpy() - rand) / sig["atr"].to_numpy()
        sig["trend"] = sig["with_ema50_1h"] if name != "1h" else sig["with_ema50_4h"]
        samples[name] = sig
    rows = []
    for fname, f in FILTERS.items():
        row, pooled = {"filter": fname}, []
        for name, s in samples.items():
            e = s.loc[f(s), "edge_atr"]
            row[f"{name} n"] = len(e)
            row[f"{name} edge"] = e.mean()
            row[f"{name} t"] = e.mean() / (e.std() / np.sqrt(len(e))) if len(e) > 2 else np.nan
            pooled.append(e)
        p = pd.concat(pooled)
        row["pooled edge"], row["pooled t"] = p.mean(), p.mean() / (p.std() / np.sqrt(len(p)))
        row["positive in all 3"] = "yes" if all(row[f"{n} edge"] > 0 for n in samples) else ""
        row["negative in all 3"] = "yes" if all(row[f"{n} edge"] < 0 for n in samples) else ""
        rows.append(row)
    return rows


def grade_table():
    """The indicator's grades (built FROM the filter table, so in-sample by construction)."""
    rows = []
    for name, unit in (("15m", "$"), ("30m", "atr"), ("1h", "atr")):
        base, h1, h4 = sample(name)
        sig, _ = find_sweeps(base, build_levels(base, h1, h4, base_k=5), candle_bars=2)
        sig = add_features(sig, base, h1, h4)
        rule, t = (("wick", 1.0), 15) if unit == "$" else (("atr", 0.15), 2.0)
        for g in ("A", "B", "AVOID"):
            s = sig[sig["grade"] == g]
            if len(s) < 3:
                continue
            r = trade_row(base, s, rule, unit, t, f"{name} grade {g}")
            rows.append({key: r[key] for key in ("setup", "trades", "win %", "coin-flip win %",
                                                 "random-entry win %", "$/trade", "edge $/trade", "t-stat")})
    return rows


def robustness_15m():
    """The headline 15m result under other definitions of a swing and of a candle sweep."""
    base, h1, h4 = sample("15m")
    rows = []
    for k in (3, 5, 8):
        lv = build_levels(base, h1, h4, base_k=k)
        for cb in (1, 2, 3):
            sig, _ = find_sweeps(base, lv, candle_bars=cb)
            sig = add_features(sig, base, h1, h4)
            r = trade_row(base, sig, ("wick", 1.0), "$", 15, f"swing k={k}, candle sweep within {cb} bar(s)")
            rows.append({key: r[key] for key in ("setup", "trades", "win %", "coin-flip win %",
                                                 "random-entry win %", "$/trade", "edge $/trade", "t-stat")})
    return rows


def md_table(rows, digits=2):
    df = pd.DataFrame(rows)
    return df.to_markdown(index=False, floatfmt=f".{digits}f")


def main():
    RESULTS.mkdir(exist_ok=True)
    runs = [study("15m", "$"), study("15m", "atr"), study("30m", "atr"), study("1h", "atr")]
    filters, grades, robust = filter_table(), grade_table(), robustness_15m()
    (RESULTS / "results.json").write_text(json.dumps(
        {"runs": runs, "filters": filters, "grades": grades, "robustness_15m": robust}, indent=1, default=float))
    lines = ["# Gold liquidity-sweep study - raw results", "",
             f"Cost per trade ${COST}, time stop {MAX_BARS} bars, failed-sweep watch {WATCH} bars, "
             f"random baseline = {RAND_PER_SIGNAL} random entries per signal, same New York hour, same direction, "
             "same stop and target. 'coin-flip win %' = stop/(stop+target), what a driftless market gives.", ""]
    for r in runs:
        unit = "dollars" if r is runs[0] else "ATR multiples"
        lines += [f"## {r['name']} chart, {r['from']} to {r['to']} ({r['bars']} bars, targets in {unit}, "
                  f"median ATR ${r['median_atr']:.2f})", "",
                  f"Sweep signals: {r['signals']}", "", "### When a level is taken", "", md_table([r["takes"]], 1), "",
                  "### Reversal before the sweep extreme breaks", "", md_table(r["reach"], 1), "",
                  "### Reversal with no stop at all, vs random entries (same hour, same direction)", "",
                  md_table(r["no_stop"], 1), "",
                  "### Fading the sweep", "", md_table(r["fade"]), "",
                  "### Fading the sweep, by trend", "", md_table(r["trend"]), "",
                  f"### The sweep fails (closes beyond its extreme within {WATCH} bars: "
                  f"{r['failed_share %']:.1f}% of sweeps; a random bar's high/low: "
                  f"{r['random_bar_retaken %']:.1f}%) - trade the break", "", md_table(r["failed"]), "",
                  md_table(r["failed_trend"]), ""]
    lines += ["## Filters, all three samples (edge vs random entries in ATR units; stop behind wick, target 2 ATR)", "",
              "Fixed in advance. With 25 filters, one or two positive-in-all-3 rows are expected by luck alone.", "",
              md_table(filters, 3), "",
              "## The indicator's grades (AVOID = Asia session, near a $50 round number, or against the trend; "
              "A = with trend in London/NY morning; B = the rest)", "",
              "Derived from the filter table above, so this is in-sample by construction - not proof of an edge.", "",
              md_table(grades), "",
              "## 15m robustness: other swing sizes and candle-sweep windows (stop behind wick + $1, target $15)", "",
              md_table(robust), ""]
    (RESULTS / "RESULTS.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
