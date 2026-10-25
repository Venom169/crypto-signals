#!/usr/bin/env python3
"""Generate the illustrative PNGs for docs/xauusd-crt-strategy-spec.md.

Every annotation (sweep, FVG, entry, SL/TP, exit, cancellations) is computed by
`simulate`, a small reference implementation of spec sections 5 and 6, so the
pictures follow the written rules exactly. Prices are synthetic.

Run:  python3 docs/img/generate_diagrams.py   (needs matplotlib)
"""
from dataclasses import dataclass, field, replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

OUT = Path(__file__).resolve().parent
TF = 5  # chart timeframe in minutes

C_BULL, C_BEAR, C_EDGE = "#c3c8cf", "#1f2328", "#30363d"
C_RANGE, C_REF = "#6e7781", "#ddf4ff"
C_FVG, C_FVG_EDGE = "#fff1a8", "#d4a72c"
C_RISK, C_REWARD = "#ffd8d3", "#d2f4dc"
C_ENTRY, C_LIQ, C_CANCEL = "#0969da", "#8250df", "#cf222e"
C_WIN, C_LOSS, C_TIME = "#1a7f37", "#cf222e", "#57606a"


# --------------------------------------------------------------------------
# Reference implementation of the spec (sections 5-6)
# --------------------------------------------------------------------------
@dataclass
class Bar:
    t: int  # bar open time, minutes after midnight, America/New_York
    o: float
    h: float
    l: float
    c: float


@dataclass
class Params:
    atr: float = 4.0  # ATR(14), fixed for the illustrations
    sweep_min_dist: float = 0.0
    sweep_max_atr: float = 0.0
    fvg_min_atr: float = 0.1
    fvg_inside_range: bool = True
    entry_mode: str = "Edge"  # Edge | Midpoint | Close
    sl_mode: str = "Beyond FVG"  # Beyond FVG | Beyond Sweep
    sl_buffer_atr: float = 0.1
    tp_mode: str = "Opposite Level"  # Opposite Level | Fixed RR
    rr_fixed: float = 2.0
    min_rr: float = 0.0
    window_end: int = 12 * 60
    force_exit: int = 16 * 60
    max_trades: int = 1
    allow_long: bool = True
    allow_short: bool = True


@dataclass
class Setup:
    dir: int  # +1 long, -1 short
    sweep_k: int
    ext: float  # sweepExt
    ext_k: int  # sweepExtBar
    fvg: tuple | None = None  # (k_i, top, bot)
    invalidated: list = field(default_factory=list)  # [(k_i, top, bot, k_invalidated)]
    entry: tuple | None = None  # (k, price, sl, tp, rr)
    exit: tuple | None = None  # (k, price, kind, R)
    end: tuple | None = None  # (k, reason) when cancelled without a trade


def find_fvg(bars, k, s, rH, rL, p):
    if k - 2 < s.ext_k:
        return None
    a, c = bars[k - 2], bars[k]
    if s.dir == 1:
        if not c.l > a.h:
            return None
        top, bot = c.l, a.h
    else:
        if not c.h < a.l:
            return None
        top, bot = a.l, c.h
    if top - bot < p.fvg_min_atr * p.atr:
        return None
    if p.fvg_inside_range and not (bot >= rL and top <= rH):
        return None
    return top, bot


def trade_levels(s, price, rH, rL, p):
    _, top, bot = s.fvg
    buf = p.sl_buffer_atr * p.atr
    if s.dir == 1:
        sl = (bot if p.sl_mode == "Beyond FVG" else s.ext) - buf
        tp = rH if p.tp_mode == "Opposite Level" else price + p.rr_fixed * (price - sl)
        rr = (tp - price) / (price - sl)
    else:
        sl = (top if p.sl_mode == "Beyond FVG" else s.ext) + buf
        tp = rL if p.tp_mode == "Opposite Level" else price - p.rr_fixed * (sl - price)
        rr = (price - tp) / (sl - price)
    return sl, tp, rr


def simulate(bars, rH, rL, p):
    """bars start at the first bar after the reference hour (range ready)."""
    state, setups, trades, s, day_end = "WAIT_SWEEP", [], 0, None, None

    def flip(k, b, d):
        new = Setup(-d, k, b.h if d == 1 else b.l, k)
        setups.append(new)
        return new

    for k, b in enumerate(bars):
        if state in ("WAIT_SWEEP", "WAIT_FVG", "WAIT_ENTRY") and b.t >= p.window_end:
            if s and s.entry is None and s.end is None:
                s.end = (k, "expired")
            day_end = (k, "expired")
            state = "DONE"

        if state == "WAIT_SWEEP":
            lo = p.allow_long and b.l < rL - p.sweep_min_dist
            hi = p.allow_short and b.h > rH + p.sweep_min_dist
            if lo and hi:
                day_end, state = (k, "both sides swept in one bar"), "DONE"
            elif lo or hi:
                s = Setup(1 if lo else -1, k, b.l if lo else b.h, k)
                setups.append(s)
                state = "WAIT_FVG"

        elif state == "WAIT_FVG":
            d = s.dir
            if (b.l < s.ext) if d == 1 else (b.h > s.ext):
                s.ext, s.ext_k = (b.l if d == 1 else b.h), k
            depth = (rL - s.ext) if d == 1 else (s.ext - rH)
            if p.sweep_max_atr > 0 and depth > p.sweep_max_atr * p.atr:
                s.end, state = (k, "real breakout"), "DONE"
            elif (b.h > rH) if d == 1 else (b.l < rL):
                s.end = (k, "opposite level broken")
                if p.allow_short if d == 1 else p.allow_long:
                    s = flip(k, b, d)
                else:
                    state = "DONE"
            else:
                fvg = find_fvg(bars, k, s, rH, rL, p)
                if fvg:
                    s.fvg, state = (k, *fvg), "WAIT_ENTRY"

        elif state == "WAIT_ENTRY":
            d = s.dir
            k_i, top, bot = s.fvg
            edge, mid = (top if d == 1 else bot), (top + bot) / 2
            touched = (b.l <= edge) if d == 1 else (b.h >= edge)
            if (b.h >= rH) if d == 1 else (b.l <= rL):
                s.end = (k, "target reached before entry")
                if p.allow_short if d == 1 else p.allow_long:
                    s, state = flip(k, b, d), "WAIT_FVG"
                else:
                    state = "DONE"
                continue
            price = None
            if p.entry_mode == "Edge" and touched:
                price = min(b.o, edge) if d == 1 else max(b.o, edge)
            elif p.entry_mode == "Midpoint" and ((b.l <= mid) if d == 1 else (b.h >= mid)):
                price = min(b.o, mid) if d == 1 else max(b.o, mid)
            elif p.entry_mode == "Close" and touched:
                if (b.c >= bot) if d == 1 else (b.c <= top):
                    price = b.c
                else:
                    s.invalidated.append((k_i, top, bot, k))
                    s.fvg, state = None, "WAIT_FVG"
            if price is not None:
                sl, tp, rr = trade_levels(s, price, rH, rL, p)
                if rr <= 0 or rr < p.min_rr:
                    s.end, state = (k, "RR too low"), "DONE"
                else:
                    trades += 1
                    s.entry, state = (k, price, sl, tp, rr), "IN_TRADE"
                    if (b.l <= sl) if d == 1 else (b.h >= sl):  # entry bar: SL only
                        s.exit = (k, sl, "SL", -1.0)

        elif state == "IN_TRADE":
            d = s.dir
            _, price, sl, tp, rr = s.entry
            if (b.l <= sl) if d == 1 else (b.h >= sl):
                s.exit = (k, sl, "SL", -1.0)
            elif (b.h >= tp) if d == 1 else (b.l <= tp):
                s.exit = (k, tp, "TP", rr)
            elif b.t + TF >= p.force_exit:
                s.exit = (k, b.c, "Time", d * (b.c - price) / abs(price - sl))

        if state == "IN_TRADE" and s.exit:
            state = "WAIT_SWEEP" if trades < p.max_trades and b.t < p.window_end else "DONE"

    return setups, day_end, state


# --------------------------------------------------------------------------
# Data helpers
# --------------------------------------------------------------------------
def hm(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def fmt_t(t):
    return f"{t // 60:02d}:{t % 60:02d}"


def series(start, ohlc):
    t0 = hm(start)
    return [Bar(t0 + i * TF, *x) for i, x in enumerate(ohlc)]


def at(start, ohlc):
    """Bars with explicit start time, continuing a previous series after a gap."""
    return series(start, ohlc)


def mirror(bars, m):
    return [Bar(b.t, m - b.o, m - b.l, m - b.h, m - b.c) for b in bars]


RH, RL = 4036.0, 4016.0

REF_LONG = series("08:00", [
    (4030, 4033, 4028, 4032), (4032, 4036, 4031, 4034), (4034, 4035, 4030, 4031),
    (4031, 4032, 4027, 4028), (4028, 4030, 4025, 4029), (4029, 4031, 4026, 4027),
    (4027, 4028, 4022, 4023), (4023, 4026, 4021, 4025), (4025, 4026, 4019, 4020),
    (4020, 4022, 4016, 4017), (4017, 4021, 4016.5, 4020), (4020, 4022, 4018, 4019),
])

# 09:00 -> 10:10 : shared by most long scenarios (sweep, FVG, pull-back above FVG)
POST_BASE = [
    (4019, 4024, 4018, 4023), (4023, 4027, 4022, 4025), (4025, 4026, 4021, 4022),
    (4022, 4025, 4020, 4024), (4024, 4025, 4019, 4020), (4020, 4021, 4017, 4018),
    (4018, 4019, 4013, 4014),        # 09:30 sweep below Low
    (4014, 4015, 4010.5, 4012),      # 09:35 sweep extreme
    (4012, 4017, 4011, 4016.5),      # 09:40 candle i-2
    (4016.5, 4027, 4014.8, 4026),    # 09:45 candle i-1 (displacement)
    (4026, 4028, 4021, 4027),        # 09:50 candle i  -> bullish FVG 4017-4021
    (4027, 4031, 4025, 4029), (4029, 4032, 4026, 4027), (4027, 4028, 4022, 4023),
]
POST_LONG = series("09:00", POST_BASE + [
    (4023, 4024, 4020, 4022),        # 10:10 retest -> entry
    (4022, 4026, 4021, 4025), (4025, 4029, 4024, 4028), (4028, 4030, 4026, 4027),
    (4027, 4032, 4026.5, 4031), (4031, 4034, 4030, 4033), (4033, 4034.5, 4031, 4032),
    (4032, 4037, 4031.5, 4036.5),    # 10:45 target
    (4036.5, 4038, 4034, 4035), (4035, 4036, 4032, 4033),
])


# --------------------------------------------------------------------------
# Drawing
# --------------------------------------------------------------------------
def candles(ax, xs, bars, w=0.62):
    for x, b in zip(xs, bars):
        bull = b.c >= b.o
        ax.vlines(x, b.l, b.h, color=C_EDGE, lw=1, zorder=3)
        lo, hi = sorted((b.o, b.c))
        ax.add_patch(Rectangle((x - w / 2, lo), w, max(hi - lo, 0.12),
                               facecolor=C_BULL if bull else C_BEAR, edgecolor=C_EDGE,
                               lw=0.8, zorder=4))


def label(ax, x, y, text, color="#24292f", size=9, ha="center", va="center", **kw):
    ax.text(x, y, text, color=color, fontsize=size, ha=ha, va=va, zorder=8,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.85), **kw)


def draw(ax, bars, setups, day_end, p, rH=RH, rL=RL, ref=None, k_from=0, k_to=None,
         compact=False, tick_every=30, title=None, notes=()):
    k_to = len(bars) if k_to is None else k_to
    shown = list(range(k_from, k_to))
    off = len(ref) if ref else 0
    x_of = {k: off + i for i, k in enumerate(shown)}
    x_end = off + len(shown) - 0.5
    fs = 8 if compact else 9

    def X(k):
        return x_of.get(k, x_of[shown[0]] if k < shown[0] else x_of[shown[-1]])

    # reference hour
    if ref:
        ax.axvspan(-0.5, off - 0.5, color=C_REF, zorder=0)
        label(ax, (off - 1) / 2, rH + 2.6, "Reference 1H candle\n08:00–09:00 NY (BUILD_RANGE)",
              color="#0550ae", size=fs)
        candles(ax, range(off), ref)
        ax.axvline(off - 0.5, color="#0550ae", ls=":", lw=1.2, zorder=2)
        label(ax, off - 0.4, rL - 4.6, "09:00 range ready\n→ WAIT_SWEEP", color="#0550ae",
              size=fs, ha="left")

    # range lines
    x0 = -0.5 if ref else x_of[shown[0]] - 0.5
    for y, name in ((rH, "High"), (rL, "Low")):
        ax.hlines(y, x0, x_end, colors=C_RANGE, linestyles=(0, (6, 4)), lw=1.6, zorder=2)
        label(ax, x0 - 0.3, y, f"{name}\n{y:.1f}", color=C_RANGE, size=fs, ha="right")

    # time gaps (omitted bars)
    for a, b in zip(shown, shown[1:]):
        if bars[b].t - bars[a].t > TF:
            xm = (x_of[a] + x_of[b]) / 2
            ax.axvspan(xm - 0.35, xm + 0.35, color="#eaeef2", zorder=1)
            ax.text(xm, rL - 1.2, "bars\nomitted", fontsize=7, ha="center", va="top",
                    color=C_TIME, zorder=8)

    # session time limits
    for k in shown:
        t = bars[k].t
        if t == p.window_end:
            ax.axvline(x_of[k] - 0.5, color=C_CANCEL, ls="--", lw=1.2, zorder=2)
            label(ax, x_of[k] - 0.5, rH + 1.5, "12:00 tradeWindowEnd", color=C_CANCEL, size=fs)
        if t + TF == p.force_exit:
            ax.axvline(x_of[k] + 0.5, color=C_CANCEL, ls="--", lw=1.2, zorder=2)
            label(ax, x_of[k] + 0.5, rH + 1.5, "16:00 forceExitTime", color=C_CANCEL,
                  size=fs, ha="right")

    candles(ax, [x_of[k] for k in shown], [bars[k] for k in shown])

    ys = [b.l for b in bars[k_from:k_to]] + [b.h for b in bars[k_from:k_to]] + [rH, rL]
    for s in setups:
        d = s.dir
        # liquidity sweep
        if k_from <= s.ext_k < k_to:
            ax.scatter([X(s.ext_k)], [s.ext], s=700 if compact else 900, facecolors="none",
                       edgecolors=C_LIQ, linewidths=1.6, zorder=6)
            label(ax, X(s.ext_k), s.ext - (1.9 if not compact else 2.4) * d, "Liq\n(sweepExt)" if not compact else "Liq",
                  color=C_LIQ, size=fs)
        # FVGs (invalidated + active)
        for k_i, top, bot, k_inv in s.invalidated:
            ax.add_patch(Rectangle((X(k_i - 2) - 0.4, bot), X(k_inv) - X(k_i - 2) + 0.4,
                                   top - bot, facecolor="#eaeef2", edgecolor=C_TIME,
                                   hatch="///", lw=1, zorder=2))
            label(ax, (X(k_i - 2) + X(k_inv)) / 2, top + 0.9, "FVG invalidated", color=C_TIME,
                  size=fs)
        if s.fvg:
            k_i, top, bot = s.fvg
            k_stop = (s.entry[0] if s.entry else s.end[0] if s.end else
                      day_end[0] if day_end else k_to - 1)
            xa = X(k_i - 2) - 0.4
            ax.add_patch(Rectangle((xa, bot), X(k_stop) + 0.4 - xa, top - bot,
                                   facecolor=C_FVG, edgecolor=C_FVG_EDGE, lw=1.2,
                                   zorder=2, alpha=0.9))
            txt = "FVG" if compact else f"FVG  top {top:.1f} / bot {bot:.1f}"
            xl = (X(k_i) + 0.5 + X(k_stop) + 0.4) / 2 if X(k_stop) > X(k_i) + 1 else \
                (xa + X(k_stop) + 0.4) / 2
            label(ax, xl, (top + bot) / 2, txt, color="#7d4e00", size=fs)
            if not compact:
                for j, name in ((k_i - 2, "i-2"), (k_i - 1, "i-1"), (k_i, "i")):
                    b = bars[j]
                    y = b.h + 1.0 if d == 1 else b.l - 1.0
                    ax.text(X(j), y, name, fontsize=7.5, ha="center", color="#7d4e00", zorder=8)
        # trade
        if s.entry:
            k_e, price, sl, tp, rr = s.entry
            k_x = s.exit[0] if s.exit else k_to - 1
            xa, xb = X(k_e) - 0.4, X(k_x) + 0.4
            ax.add_patch(Rectangle((xa, min(price, sl)), xb - xa, abs(price - sl),
                                   facecolor=C_RISK, edgecolor=C_LOSS, lw=0.8, zorder=1.5,
                                   alpha=0.85))
            ax.add_patch(Rectangle((xa, min(price, tp)), xb - xa, abs(tp - price),
                                   facecolor=C_REWARD, edgecolor=C_WIN, lw=0.8, zorder=1.5,
                                   alpha=0.85))
            ax.scatter([X(k_e)], [price], marker=">", s=90, color=C_ENTRY, zorder=7)
            lx = max(xb, x_end) + 0.3
            label(ax, lx, price, f"Entry {price:.1f}", color=C_ENTRY, size=fs, ha="left")
            label(ax, lx, sl, f"SL {sl:.1f}", color=C_LOSS, size=fs, ha="left",
                  va="top" if d == 1 else "bottom")
            label(ax, lx, tp, f"TP {tp:.1f}  (RR {rr:.2f})", color=C_WIN, size=fs, ha="left",
                  va="bottom" if d == 1 else "top")
            ys += [sl, tp]
            if s.exit:
                k_x, px, kind, r = s.exit
                color = {"TP": C_WIN, "SL": C_LOSS, "Time": C_TIME}[kind]
                mark = {"TP": "TP ✓", "SL": "SL ✗", "Time": "Time exit"}[kind]
                ax.scatter([X(k_x)], [px], marker="X", s=80, color=color, zorder=7)
                yo = (2.2 if kind == "TP" else -2.2) * d if kind != "Time" else -2.6 * d
                label(ax, X(k_x), px + yo, f"{mark} {r:+.2f}R", color=color, size=fs,
                      weight="bold")
        if s.end and k_from <= s.end[0] < k_to:
            k_c, reason = s.end
            b = bars[k_c]
            ax.annotate(f"{'LONG' if d == 1 else 'SHORT'} cancelled:\n{reason}",
                        xy=(X(k_c), b.h if d == 1 else b.l),
                        xytext=(-75, -45) if reason == "real breakout" else (-70, 28 if d == 1 else -40),
                        textcoords="offset points", ha="center", fontsize=fs, color=C_CANCEL,
                        weight="bold", zorder=9,
                        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.9),
                        arrowprops=dict(arrowstyle="->", color=C_CANCEL, lw=1.1))
    if day_end and k_from <= day_end[0] < k_to and not any(s.end and s.end[1] == day_end[1]
                                                          for s in setups):
        k_c, reason = day_end
        label(ax, X(k_c), bars[k_c].h + 2.0, f"DONE: {reason}", color=C_CANCEL, size=fs,
              weight="bold")

    for i, (xn, yn, txt) in enumerate(notes):
        label(ax, xn, yn, txt, color="#24292f", size=fs, ha="left")

    # axes
    all_x = list(range(off)) + [x_of[k] for k in shown]
    all_b = (ref or []) + [bars[k] for k in shown]
    ticks = [(x, fmt_t(b.t)) for x, b in zip(all_x, all_b) if b.t % tick_every == 0]
    ax.set_xticks([x for x, _ in ticks], [t for _, t in ticks], fontsize=fs)
    ax.set_xlim(x0 - (4.2 if not compact else 3.6), x_end + (7 if not compact else 5.5))
    ax.set_ylim(min(ys) - 5.5, max(ys) + 5.0)
    ax.tick_params(axis="y", labelsize=fs)
    ax.grid(axis="y", color="#eaeef2", lw=0.8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    if title:
        ax.set_title(title, fontsize=10.5 if compact else 13, loc="left", weight="bold")


def steps_text(setups, bars, p, rH, rL):
    s = next(x for x in setups if x.entry)
    k_i, top, bot = s.fvg
    k_e, price, sl, tp, rr = s.entry
    k_x, px, kind, r = s.exit
    long_ = s.dir == 1
    side, lvl, opp = ("LONG", "Low", "High") if long_ else ("SHORT", "High", "Low")
    cmp_sweep = "low < rangeLow" if long_ else "high > rangeHigh"
    cmp_fvg = "low[i] > high[i-2]" if long_ else "high[i] < low[i-2]"
    edge = "fvgTop" if long_ else "fvgBot"
    sl_txt = "fvgBot − 0.1×ATR" if long_ else "fvgTop + 0.1×ATR"
    return "\n".join([
        f"1) 08:00–09:00  Reference 1H candle → rangeHigh {rH:.1f} / rangeLow {rL:.1f} (wicks included)",
        "2) 09:00        Range ready → watch the 5-minute chart (WAIT_SWEEP)",
        f"3) {fmt_t(bars[s.sweep_k].t)}        {cmp_sweep} → liquidity sweep of {lvl} → {side} setup; "
        f"sweepExt = {s.ext:.1f} at {fmt_t(bars[s.ext_k].t)}",
        f"4) {fmt_t(bars[k_i].t)}        {'Bullish' if long_ else 'Bearish'} FVG: {cmp_fvg}, inside the range "
        f"→ zone {bot:.1f}–{top:.1f}",
        f"5) {fmt_t(bars[k_e].t)}        Retest touches {edge} → entry {price:.1f} (entryMode = Edge)",
        f"6) SL = {sl_txt} = {sl:.1f}   TP = range{opp} = {tp:.1f}   RR = {rr:.2f}   (ATR(14) = {p.atr} assumed)",
        f"7) {fmt_t(bars[k_x].t)}        {kind} hit → {r:+.2f}R",
    ])


def fig_example(path, ref, post, title):
    p = Params()
    setups, day_end, _ = simulate(post, RH, RL, p)
    fig = plt.figure(figsize=(14, 9.2))
    ax = fig.add_axes([0.06, 0.30, 0.92, 0.64])
    draw(ax, post, setups, day_end, p, ref=ref, title=title)
    fig.text(0.06, 0.03, steps_text(setups, post, p, RH, RL), fontsize=10.5, family="DejaVu Sans Mono",
             va="bottom", ha="left", linespacing=1.55,
             bbox=dict(boxstyle="round,pad=0.6", fc="#f6f8fa", ec="#d0d7de"))
    fig.savefig(OUT / path, dpi=130)
    plt.close(fig)
    return setups


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------
def fig_timeline():
    fig, ax = plt.subplots(figsize=(16, 5))
    rows = {"Optional session shading\n(visual only)": 2.0, "Setup search": 1.0, "Trade management": 0.0}
    def bar(row, a, b, text, color, tc="#24292f", size=9.5):
        y = rows[row]
        ax.add_patch(Rectangle((a, y - 0.32), b - a, 0.64, facecolor=color, edgecolor="#8c959f", lw=0.8))
        ax.text((a + b) / 2, y, text, ha="center", va="center", fontsize=size, color=tc)
    row0 = list(rows)[0]
    bar(row0, -4, 0, "Asia 20:00–00:00\nPhase 1 · Accumulation", "#f6f8fa")
    bar(row0, 2, 5, "London 02:00–05:00\nPhase 2 · Manipulation", "#f6f8fa")
    bar(row0, 7, 10, "New York 07:00–10:00\nPhase 3 · Distribution", "#f6f8fa")
    bar("Setup search", 8, 9, "1H ref\ncandle", C_REF, "#0550ae", size=8)
    bar("Setup search", 9, 12, "sweep → FVG → entry\n(5-minute chart)", C_FVG, "#7d4e00")
    bar("Trade management", 9, 16, "IN_TRADE: exit at SL / TP, or forced at 16:00", C_REWARD, C_WIN)
    for x, txt, y in ((8, "08:00 refHour", 2.62), (9, "09:00 range ready", 2.9),
                      (12, "12:00 tradeWindowEnd", 2.62), (16, "16:00 forceExitTime", 2.62),
                      (17, "17:00 gold daily close", 2.9)):
        ax.axvline(x, color=C_CANCEL if x in (12, 16) else "#0550ae" if x < 12 else C_TIME,
                   ls="--", lw=1)
        ax.text(x, y, txt, ha="center", va="bottom", fontsize=8.5, color="#24292f",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))
    ax.set_yticks(list(rows.values()), list(rows), fontsize=9.5)
    ticks = list(range(-6, 18, 2))
    ax.set_xticks(ticks, [f"{(h % 24):02d}:00" for h in ticks], fontsize=9)
    ax.set_xlim(-6.2, 17.6)
    ax.set_ylim(-0.6, 3.25)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.set_title("Daily timeline — all times America/New_York (DST handled by the timezone)",
                 loc="left", fontsize=13, weight="bold", pad=22)
    fig.tight_layout()
    fig.savefig(OUT / "01-daily-timeline.png", dpi=130)
    plt.close(fig)


def fig_fvg_definition():
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.2))
    cases = [
        ("Bullish FVG (for LONG)", [(10, 12, 9, 11.5), (11.5, 17, 11, 16.5), (16.5, 18, 14, 17)], 1),
        ("Bearish FVG (for SHORT)", [(17, 18, 15, 15.5), (15.5, 16, 10, 10.5), (10.5, 13, 9, 10)], -1),
        ("NOT an FVG (wicks overlap)", [(10, 12, 9, 11.5), (11.5, 17, 11, 16.5), (16.5, 18, 11.5, 17)], 0),
    ]
    for ax, (title, ohlc, d) in zip(axes, cases):
        bars = [Bar(0, *x) for x in ohlc]
        candles(ax, range(3), bars, w=0.5)
        for x, name in enumerate(("i-2", "i-1", "i")):
            ax.text(x, 7.6, name, ha="center", fontsize=11, weight="bold")
        a, c = bars[0], bars[2]
        if d == 1:
            top, bot = c.l, a.h
            rule = "low[i] > high[i-2]\nfvgTop = low[i]\nfvgBot = high[i-2]"
        elif d == -1:
            top, bot = a.l, c.h
            rule = "high[i] < low[i-2]\nfvgTop = low[i-2]\nfvgBot = high[i]"
        else:
            top, bot = a.h, c.l
            rule = "low[i] ≤ high[i-2]\n→ no gap, ignore"
        if d:
            ax.add_patch(Rectangle((-0.3, bot), 2.6, top - bot, facecolor=C_FVG,
                                   edgecolor=C_FVG_EDGE, lw=1.2, zorder=1))
            ax.text(2.42, top, f"fvgTop {top:g}", va="center", fontsize=9.5, color="#7d4e00")
            ax.text(2.42, bot, f"fvgBot {bot:g}", va="center", fontsize=9.5, color="#7d4e00")
        else:
            ax.hlines([a.h, c.l], -0.3, 2.3, colors=C_CANCEL, linestyles="--", lw=1)
        ax.text(1, 19.3, rule, ha="center", va="bottom", fontsize=10.5,
                family="DejaVu Sans Mono",
                bbox=dict(boxstyle="round,pad=0.4", fc="#f6f8fa", ec="#d0d7de"))
        ax.set_xlim(-0.8, 3.4)
        ax.set_ylim(7, 23.5)
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_title(title, fontsize=12, weight="bold")
    fig.suptitle("FVG = 3-candle pattern, evaluated on the close of candle i "
                 "(i-2 must not be before the sweep extreme)", fontsize=12.5, y=0.995)
    fig.tight_layout()
    fig.savefig(OUT / "04-fvg-definition.png", dpi=130)
    plt.close(fig)


def fig_entry_modes():
    retest_after = {  # bars appended after POST_BASE (from 10:10)
        "Edge": [(4023, 4024, 4020, 4022), (4022, 4026, 4021, 4025), (4025, 4028, 4024, 4027)],
        "Midpoint": [(4023, 4024, 4020, 4022), (4022, 4023, 4018.5, 4021),
                     (4021, 4025, 4020, 4024), (4024, 4027, 4023, 4026)],
        "Close": [(4023, 4024, 4018, 4022.5), (4022.5, 4026, 4022, 4025), (4025, 4028, 4024, 4027)],
        "Close (invalidated)": [(4023, 4023.5, 4015.5, 4016.2), (4016.2, 4018, 4015, 4017.5),
                                (4017.5, 4024, 4017, 4023.5), (4023.5, 4026, 4020, 4025),
                                (4025, 4026, 4021, 4022)],
    }
    subtitles = {
        "Edge": "entryMode = \"Edge\": first touch of fvgTop → limit fill at fvgTop",
        "Midpoint": "entryMode = \"Midpoint\": 10:10 touches top only (no fill); 10:15 reaches 50% → fill",
        "Close": "entryMode = \"Close\": touch + close ≥ fvgBot → enter at that close",
        "Close (invalidated)": "entryMode = \"Close\": touch + close < fvgBot → FVG invalidated,\n"
                               "back to WAIT_FVG → a new FVG forms at 10:25",
    }
    fig, axes = plt.subplots(2, 2, figsize=(16, 10.5))
    for ax, (name, extra) in zip(axes.flat, retest_after.items()):
        p = Params(entry_mode="Close" if name.startswith("Close") else name)
        post = series("09:00", POST_BASE + extra)
        setups, day_end, _ = simulate(post, RH, RL, p)
        draw(ax, post, setups, day_end, p, k_from=5, compact=True, tick_every=15,
             title=subtitles[name])
        if name == "Midpoint":
            _, top, bot = setups[0].fvg
            ax.hlines((top + bot) / 2, 4.5, len(post) - 5.5, colors="#7d4e00", linestyles=":",
                      lw=1.2, zorder=5)
    fig.suptitle("Entry modes (LONG shown; SHORT is the mirror)", fontsize=14, weight="bold",
                 x=0.02, ha="left")
    fig.tight_layout()
    fig.savefig(OUT / "05-entry-modes.png", dpi=120)
    plt.close(fig)


def fig_edge_cases():
    base = POST_BASE[:11]  # through the 09:50 FVG candle
    entered = POST_BASE + [(4023, 4024, 4020, 4022)]  # through the 10:10 entry
    cases = [
        ("Target reached before the retest → LONG cancelled;\nthat move swept High → SHORT setup starts",
         Params(), series("09:00", base + [
             (4027, 4031, 4025, 4030), (4030, 4034, 4029, 4033), (4033, 4037.5, 4032, 4036.8),
             (4036.8, 4038, 4035, 4035.5), (4035.5, 4036, 4031, 4032), (4032, 4033, 4028, 4029),
             (4029, 4031, 4027, 4030)]), 4),
        ("Real breakout: price went more than sweepMaxATR×ATR\nbeyond Low before any FVG (sweepMaxATR = 1.5)",
         Params(sweep_max_atr=1.5), series("09:00", POST_BASE[:6] + [
             (4018, 4019, 4013, 4014), (4014, 4015, 4011, 4011.5), (4011.5, 4012, 4008, 4008.5),
             (4008.5, 4010, 4005, 4006), (4006, 4008, 4003, 4004)]), 2),
        ("Expired: FVG formed but no retest before 12:00\n→ the 12:00 touch is ignored",
         Params(), at("11:20", [
             (4020, 4022, 4018, 4019), (4019, 4019.5, 4014, 4015), (4015, 4018, 4014.5, 4017.5),
             (4017.5, 4025, 4016.5, 4024.5), (4024.5, 4027, 4022, 4026), (4026, 4028, 4024, 4025),
             (4025, 4026, 4023, 4023.5), (4023.5, 4025, 4022.5, 4024), (4024, 4024.5, 4019, 4020),
             (4020, 4023, 4019.5, 4022)]), 0),
        ("Both sides swept in one bar (news spike)\n→ no setup today",
         Params(), series("09:00", [
             (4024, 4027, 4022, 4025), (4025, 4026, 4023, 4024), (4024, 4038, 4013, 4020),
             (4020, 4023, 4018, 4022), (4022, 4025, 4020, 4021), (4021, 4024, 4019, 4023)]), 0),
        ("SL and TP inside the same bar\n→ counted as SL (conservative)",
         Params(), series("09:00", entered + [(4022, 4038, 4015, 4030), (4030, 4032, 4027, 4028)]), 5),
        ("Still open at 16:00 → closed at the close of the\n15:55 bar (time_close ≥ forceExitTime)",
         Params(), series("09:00", entered + [(4022, 4026, 4021, 4025), (4025, 4027, 4023, 4024)])
         + at("15:40", [(4026, 4028, 4025, 4027), (4027, 4029, 4026, 4028.5),
                        (4028.5, 4029, 4026.5, 4027), (4027, 4028, 4025.5, 4026)]), 5),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(19, 11))
    for ax, (title, p, post, k_from) in zip(axes.flat, cases):
        setups, day_end, _ = simulate(post, RH, RL, p)
        draw(ax, post, setups, day_end, p, k_from=k_from, compact=True, tick_every=15, title=title)
        if p.sweep_max_atr:
            y = RL - p.sweep_max_atr * p.atr
            ax.hlines(y, k_from - 0.5, len(post) - 0.5, colors=C_CANCEL, linestyles=":", lw=1.2)
            label(ax, k_from - 0.3, y + 0.5, "Low − 1.5×ATR", color=C_CANCEL, size=8, ha="left",
                  va="bottom")
    fig.suptitle("Cancellation and exit rules (LONG shown; SHORT is the mirror)", fontsize=14,
                 weight="bold", x=0.02, ha="left")
    fig.tight_layout()
    fig.savefig(OUT / "06-edge-cases.png", dpi=115)
    plt.close(fig)


def main():
    fig_timeline()
    fig_example("02-long-example.png", REF_LONG, POST_LONG,
                "Example 1 — LONG: sweep of Low → bullish FVG → retest → target High (XAUUSD, 5-minute)")
    m = RH + RL
    fig_example("03-short-example.png", mirror(REF_LONG, m), mirror(POST_LONG, m),
                "Example 2 — SHORT (mirror): sweep of High → bearish FVG → retest → target Low")
    fig_fvg_definition()
    fig_entry_modes()
    fig_edge_cases()
    print("written to", OUT)


if __name__ == "__main__":
    main()
