"""Draw example charts of liquidity sweeps on real 15m gold data.

    python research/plot_examples.py      -> research/examples/*.png

Every example is a real signal from research/results/signals_15m.csv, drawn
with the same engine the study uses (levels, sweeps, stop/targets, outcome).
Arabic text needs matplotlib >= 3.10 (built-in shaping and bidi); keep each
string either Arabic-first or Latin-only so its direction is unambiguous.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

from sweep_engine import (NEVER, add_features, build_levels, daily_table, find_sweeps, load,  # noqa: E402
                          session_of, simulate, stop_distance, unix)

OUT = Path(__file__).resolve().parent / "examples"

# Light chart chrome and colors (dataviz reference palette).
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
CLASS_COLOR = {"chart": "#2a78d6", "htf": "#eb6834", "cal": "#1baf7a"}  # categorical slots 1-3
CLASS_NAME = {"chart": "سوينغ على فريم الشارت", "htf": "سوينغ على الساعة أو الأربع ساعات",
              "cal": "قمة وقاع اليوم والأسبوع وآسيا"}
GOOD, CRIT = "#0ca30c", "#d03b3b"  # status: target reached / stop hit
KIND_CLASS = {"P": "chart", "P1H": "htf", "P4H": "htf", "PD": "cal", "PW": "cal", "ASIA": "cal"}
KIND_RANK = {"P": 1, "ASIA": 2, "P1H": 3, "PD": 4, "P4H": 5, "PW": 6}
SESSION_AR = {"asia": "آسيا", "london": "لندن", "ny_am": "صباح نيويورك", "ny_pm": "بعد ظهر نيويورك"}
STOP_BUF, TP1, TP2, MAX_BARS, COST = 1.0, 15.0, 20.0, 32, 0.5
HALO = [pe.withStroke(linewidth=3, foreground=SURFACE)]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.labelcolor": INK2, "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
})


def kind_label(kind, side):
    return {"P": "15m", "P1H": "1H", "P4H": "4H", "PD": "PDH" if side == 1 else "PDL",
            "PW": "PWH" if side == 1 else "PWL", "ASIA": "ASIA H" if side == 1 else "ASIA L"}[kind]


# --------------------------------------------------------------------------
# Data: levels with their life span, signals with outcomes
# --------------------------------------------------------------------------

def prepare():
    base, h1, h4 = load("15m"), load("1h"), load("4h")
    levels = build_levels(base, h1, h4, base_k=5)
    sig, _ = find_sweeps(base, levels, candle_bars=2)
    sig = add_features(sig, base, h1, h4)
    S = stop_distance(sig, ("wick", STOP_BUF))
    for t in (TP1, TP2):
        res = simulate(base, sig["i"].to_numpy(), sig["dir"].to_numpy(), S, np.full(len(sig), t), MAX_BARS, COST)
        sig[f"exit{t:g}"] = res["exit"].to_numpy()
        sig[f"bars{t:g}"] = res["bars"].to_numpy()
    sig["stop_px"] = sig["ext"] - sig["dir"] * STOP_BUF
    return base, h1, h4, level_lives(base, levels), sig


def level_lives(base, levels):
    """Bar span of every level as the engine sees it: active from its start until taken or expired."""
    ts = unix(base.index)
    o, h, l, c = (base[x].to_numpy() for x in ("open", "high", "low", "close"))
    n, rows = len(base), []
    for L in levels:
        a = int(np.searchsorted(ts, L.start))
        if a >= n:
            continue
        ref = c[a - 1] if a else o[a]
        if not ((L.side == 1 and L.price > ref) or (L.side == -1 and L.price < ref)):
            continue
        e = int(np.searchsorted(ts, L.end)) if L.end < NEVER else n
        seg = (h[a:e] > L.price) if L.side == 1 else (l[a:e] < L.price)
        taken = a + int(np.argmax(seg)) if seg.any() else None
        rows.append(dict(price=L.price, side=L.side, kind=L.kind, born=min(int(np.searchsorted(ts, L.born)), a),
                         start=a, stop=taken if taken is not None else e, taken=taken is not None))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Label placement without collisions
# --------------------------------------------------------------------------

class Labels:
    """Places text in data coordinates and skips anything that would overlap what is already there."""

    def __init__(self, ax):
        self.ax, self.boxes = ax, []
        fig = ax.figure
        bb = ax.get_position()
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        self.dx = (x1 - x0) / (bb.width * fig.get_figwidth() * 72)   # data units per point
        self.dy = (y1 - y0) / (bb.height * fig.get_figheight() * 72)

    def box(self, x, y, text, size, ha, va):
        w, h = len(text) * size * 0.62 * self.dx, size * 1.35 * self.dy
        bx = {"left": x, "right": x - w, "center": x - w / 2}[ha]
        by = {"bottom": y, "top": y - h, "center": y - h / 2}[va]
        return bx, bx + w, by, by + h

    def free(self, b):
        return not any(b[0] < o[1] and o[0] < b[1] and b[2] < o[3] and o[2] < b[3] for o in self.boxes)

    def reserve(self, x0, x1, y0, y1):
        self.boxes.append((x0, x1, y0, y1))

    def inside(self, b):
        (x0, x1), (y0, y1) = self.ax.get_xlim(), self.ax.get_ylim()
        return b[0] >= x0 and b[1] <= x1 and b[2] >= y0 and b[3] <= y1

    def put(self, x, y, text, size=8.6, ha="left", va="center", color=INK2, force=False, **kw):
        b = self.box(x, y, text, size, ha, va)
        if not force and not (self.free(b) and self.inside(b)):
            return False
        self.boxes.append(b)
        self.ax.text(x, y, text, fontsize=size, ha=ha, va=va, color=color, zorder=8,
                     bbox=dict(boxstyle="square,pad=0.15", facecolor=SURFACE, edgecolor="none", alpha=0.85), **kw)
        return True


# --------------------------------------------------------------------------
# Drawing helpers
# --------------------------------------------------------------------------

def header(fig, title, subtitle, meta):
    fig.text(0.965, 0.955, title, ha="right", va="top", fontsize=16.5, color=INK, weight="bold")
    fig.text(0.965, 0.905, subtitle, ha="right", va="top", fontsize=11, color=INK2)
    fig.text(0.035, 0.952, meta, ha="left", va="top", fontsize=10, color=MUTED)


def style_axes(ax):
    ax.yaxis.tick_right()
    ax.grid(True, axis="y", color=GRID, linewidth=0.8)
    ax.grid(True, axis="x", color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)
    for side in ("top", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0, labelsize=9)


def draw_candles(ax, base, i0, i1, width=0.62):
    for k, (o, h, l, c) in enumerate(base[["open", "high", "low", "close"]].iloc[i0:i1 + 1].to_numpy()):
        x = i0 + k
        ax.plot([x, x], [l, h], color=INK2, linewidth=0.9, zorder=3, solid_capstyle="round")
        ax.add_patch(Rectangle((x - width / 2, min(o, c)), width, max(abs(c - o), 0.05),
                               facecolor=SURFACE if c >= o else INK2, edgecolor=INK2, linewidth=0.9, zorder=4))


def time_axis(ax, base, i0, i1, every=8):
    ticks = list(range(i0, i1 + 1, every))
    ax.set_xticks(ticks)
    ax.set_xticklabels([base.index[t].strftime("%H:%M") for t in ticks])


def level_groups(lives, i0, i1, ylo, yhi, known_at=None, swept=()):
    """Levels drawn in the window, merged when several timeframes share one price."""
    v = lives[(lives["start"] <= i1) & (lives["stop"] >= i0) & lives["price"].between(ylo, yhi)]
    if known_at is not None:  # only what existed when the signal fired (a candle sweep takes its level earlier)
        was_swept = v["price"].apply(lambda p: any(abs(p - q) < 1e-6 for q in swept)) & v["taken"] & \
            (v["stop"] >= known_at - 3)
        v = v[(v["start"] <= known_at) & ((v["stop"] >= known_at) | was_swept)]
    groups = []
    for _, g in v.groupby([v["side"], v["price"].round(2)]):
        kinds = sorted(set(g["kind"]), key=KIND_RANK.get)
        stop = int(g["stop"].max())
        groups.append(dict(price=g["price"].iloc[0], side=int(g["side"].iloc[0]), kinds=kinds,
                           x0=max(int(g["born"].min()), i0), x1=min(stop, i1), taken=stop <= i1,
                           rank=max(KIND_RANK[k] for k in kinds)))
    return sorted(groups, key=lambda d: -d["rank"])


def draw_levels(ax, labels, groups, highlight=(), label_all=True):
    for d in groups:
        cls = KIND_CLASS[max(d["kinds"], key=KIND_RANK.get)]
        hot = any(abs(d["price"] - p) < 1e-6 for p in highlight)
        ax.plot([d["x0"], d["x1"]], [d["price"]] * 2, color=CLASS_COLOR[cls], linewidth=2.4 if hot else 1.3,
                alpha=1 if hot else 0.8, zorder=2, solid_capstyle="round")
        if d["taken"]:
            ax.plot(d["x1"], d["price"], marker="o", markersize=5, color=CLASS_COLOR[cls],
                    markeredgecolor=SURFACE, markeredgewidth=1.4, zorder=5)
    for d in sorted(groups, key=lambda d: (not any(abs(d["price"] - p) < 1e-6 for p in highlight), -d["rank"])):
        hot = any(abs(d["price"] - p) < 1e-6 for p in highlight)
        if not (hot or label_all):
            continue
        text = " + ".join(kind_label(k, d["side"]) for k in d["kinds"]) + f"  {d['price']:.1f}"
        xs = (d["x0"] + 0.3, max(d["x1"] - 0.3 - len(text) * 8.6 * 0.62 * labels.dx, d["x0"] + 0.3))
        sides = ("bottom", "top") if d["side"] == 1 else ("top", "bottom")  # beyond the level first
        tries = [(x, va) for va in sides for x in xs]
        for x, va in tries:
            y = d["price"] + (labels.dy * 2 if va == "bottom" else -labels.dy * 2)
            if labels.put(x, y, text, size=8.6, ha="left", va=va, weight="bold" if hot else "normal"):
                break


def draw_signal(ax, labels, base, s, yr, featured=False, outcome=False):
    h, l = base["high"].to_numpy(), base["low"].to_numpy()
    i, d = int(s["i"]), int(s["dir"])
    col = MUTED if s["grade"] == "AVOID" else INK
    y = h[i] + yr * 0.022 if d == -1 else l[i] - yr * 0.022
    ax.plot(i, y, marker="v" if d == -1 else "^", markersize=11 if featured else 8.5, color=col,
            markeredgecolor=SURFACE, markeredgewidth=1.4, zorder=9)
    labels.reserve(i - 0.6, i + 0.6, y - yr * 0.015, y + yr * 0.015)
    ty = y + yr * 0.028 if d == -1 else y - yr * 0.028
    text = f"{s['type']} · {s['grade']}"
    labels.put(i, ty, text, size=9 if featured else 8.2, ha="center", va="bottom" if d == -1 else "top",
               color=INK if featured else (MUTED if s["grade"] == "AVOID" else INK2), force=True,
               weight="bold" if featured else "normal")
    if outcome:
        hit = s[f"exit{TP1:g}"] == "tp"
        oy = ty + (yr * 0.045 if d == -1 else -yr * 0.045)
        ax.text(i, oy, "✓" if hit else "✗", color=GOOD if hit else CRIT, fontsize=12, ha="center",
                va="center", weight="bold", zorder=9, path_effects=HALO, clip_on=True)
        labels.reserve(i - 0.7, i + 0.7, oy - yr * 0.02, oy + yr * 0.02)


def draw_plan(ax, labels, s, i1):
    """Entry / stop / targets for one signal, with risk and reward washes and the outcomes."""
    i, d, e = int(s["i"]), int(s["dir"]), s["entry"]
    sl, tp1, tp2 = s["stop_px"], e + d * TP1, e + d * TP2
    end = min(i + max(int(s[f"bars{TP1:g}"]), int(s[f"bars{TP2:g}"]), 4) + 2, i1)
    ax.add_patch(Rectangle((i, min(e, sl)), end - i, abs(sl - e), facecolor=CRIT, alpha=0.10, zorder=1))
    ax.add_patch(Rectangle((i, min(e, tp2)), end - i, abs(tp2 - e), facecolor=GOOD, alpha=0.08, zorder=1))
    rows = [(e, INK2, 1.5, f"Entry {e:.1f}"), (sl, CRIT, 1.7, f"SL {sl:.1f}  (-${abs(sl - e):.1f})"),
            (tp1, GOOD, 1.4, f"TP1 {tp1:.1f}  (+${TP1:.0f})"), (tp2, GOOD, 1.7, f"TP2 {tp2:.1f}  (+${TP2:.0f})")]
    for y, col, lw, _ in rows:
        ax.plot([i, end], [y, y], color=col, linewidth=lw, zorder=3, solid_capstyle="round")
    # labels to the right of the plan, nudged apart when TP1/TP2 sit close together
    ys = sorted(((y, txt) for y, _, _, txt in rows), key=lambda t: t[0])
    min_gap = labels.dy * 13
    placed = []
    for y, txt in ys:
        yy = max(y, placed[-1] + min_gap) if placed else y
        placed.append(yy)
        labels.put(end + 0.5, yy, txt, size=8.8, ha="left", va="center", force=True)
    for t, ty in ((TP1, tp1), (TP2, tp2)):
        hit = s[f"exit{t:g}"] == "tp"
        j = i + int(s[f"bars{t:g}"])
        if j <= i1:
            ax.text(j + 0.45, ty if hit else sl, "✓" if hit else "✗", color=GOOD if hit else CRIT, fontsize=15,
                    ha="center", va="center", weight="bold", zorder=10, path_effects=HALO)


def legend_items(with_signals=False, rtl_row=False):
    items = [(Line2D([0], [0], color=CLASS_COLOR[k], linewidth=2.2), CLASS_NAME[k]) for k in CLASS_COLOR]
    if rtl_row:  # a single row reads right to left: first item on the right
        return items[::-1]
    if with_signals:
        items += [(Line2D([0], [0], marker="v", color=INK, linestyle="", markersize=8), "إشارة سحب A أو B"),
                  (Line2D([0], [0], marker="v", color=MUTED, linestyle="", markersize=8), "إشارة سحب AVOID"),
                  (Line2D([0], [0], marker="$✓$", color=GOOD, linestyle="", markersize=9), "وصل 15$ قبل الستوب"),
                  (Line2D([0], [0], marker="$✗$", color=CRIT, linestyle="", markersize=9), "ضرب الستوب أولاً")]
    return items


def y_limits(base, i0, i1, extra=()):
    lo = min([base["low"].iloc[i0:i1 + 1].min(), *extra])
    hi = max([base["high"].iloc[i0:i1 + 1].max(), *extra])
    pad = (hi - lo) * 0.09
    return lo - pad, hi + pad


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------

def example(base, lives, sig, when, title, subtitle, note, fname, pre=36, post=30):
    s = sig[sig["time"] == pd.Timestamp(when, tz="UTC")].iloc[0]
    i = int(s["i"])
    i0, i1 = max(i - pre, 0), min(i + post, len(base) - 1)
    d, e = int(s["dir"]), s["entry"]
    ylo, yhi = y_limits(base, i0, i1, (s["stop_px"], e + d * TP2))
    fig = plt.figure(figsize=(13, 7.6), dpi=130)
    ax = fig.add_axes([0.035, 0.17, 0.875, 0.68])
    style_axes(ax)
    header(fig, title, subtitle, f"OANDA:XAUUSD · 15m · {s['time']:%Y-%m-%d %H:%M} UTC")
    ax.set_xlim(i0 - 1, i1 + 12)
    ax.set_ylim(ylo, yhi)
    labels = Labels(ax)
    draw_candles(ax, base, i0, i1)
    window = sig[(sig["i"] >= i0) & (sig["i"] <= i1)]
    for _, w in window.iterrows():
        draw_signal(ax, labels, base, w, yhi - ylo, featured=int(w["i"]) == i)
    draw_plan(ax, labels, s, i1)
    draw_levels(ax, labels, level_groups(lives, i0, i1, ylo, yhi, known_at=i, swept=s["lv_prices"]),
                highlight=s["lv_prices"])
    time_axis(ax, base, i0, i1)
    fig.legend(*zip(*legend_items(rtl_row=True)), loc="lower right", bbox_to_anchor=(0.965, 0.065), ncol=3,
               fontsize=9.5,
               frameon=False, labelcolor=INK2, markerfirst=False, columnspacing=2.2, handlelength=2.2)
    fig.text(0.965, 0.025, note, ha="right", va="bottom", fontsize=10.5, color=INK2)
    fig.savefig(OUT / fname)
    plt.close(fig)


def concept(fname):
    """Schematic: wick sweep, candle sweep, real break - and how often each happened."""
    fig = plt.figure(figsize=(13, 6.8), dpi=130)
    fig.text(0.965, 0.955, "ماذا يحدث عندما يأخذ السعر السيولة فوق قمة سابقة؟", ha="right", va="top",
             fontsize=16.5, color=INK, weight="bold")
    fig.text(0.965, 0.9, "فوق القمة تتجمع ستوبات البائعين وأوامر الشراء على الكسر. ثلاث نهايات ممكنة، "
             "ونسبة كل منها من 475 مرة أُخذ فيها مستوى على 15 دقيقة:", ha="right", va="top", fontsize=11, color=INK2)
    level = 100.0
    lead = [(96, 97.2, 95.4, 96.8), (96.8, 98.6, 96.4, 98.2), (98.2, 100.0, 97.6, 98.4),
            (98.4, 98.9, 96.9, 97.3), (97.3, 98.1, 96.2, 97.9), (97.9, 99.1, 97.5, 98.8)]
    endings = {
        "W": [(98.8, 101.6, 98.5, 99.0), (99.0, 99.4, 97.6, 97.9), (97.9, 98.3, 96.8, 97.1)],
        "C": [(98.8, 101.4, 98.6, 101.0), (101.0, 101.3, 99.2, 99.5), (99.5, 99.8, 97.9, 98.2)],
        "B": [(98.8, 101.5, 98.6, 101.2), (101.2, 102.6, 100.7, 102.3), (102.3, 103.4, 101.8, 103.1)],
    }
    meta = {
        "W": ("سحب بالذيل (W)", "الذيل يتجاوز القمة،\nوالشمعة نفسها تُغلق تحتها", "48%", 6),
        "C": ("سحب بالشمعة (C)", "إغلاق فوق القمة،\nثم عودة تحتها خلال شمعة أو شمعتين", "22%", 7),
        "B": ("كسر حقيقي", "إغلاق فوق القمة،\nوالسعر يبقى فوقها", "30%", None),
    }
    for k, key in enumerate(("W", "C", "B")):
        left = 0.04 + (2 - k) * 0.32
        ax = fig.add_axes([left, 0.25, 0.28, 0.53])
        bars = lead + endings[key]
        ax.add_patch(Rectangle((2, level), len(bars) - 2.5, 0.9, facecolor=CLASS_COLOR["htf"], alpha=0.10, zorder=1))
        ax.plot([2, len(bars) - 0.5], [level, level], color=CLASS_COLOR["htf"], linewidth=2.2, zorder=2)
        for x, (o, h, lo, c) in enumerate(bars):
            ax.plot([x, x], [lo, h], color=INK2, linewidth=1.1, zorder=3)
            ax.add_patch(Rectangle((x - 0.3, min(o, c)), 0.6, max(abs(c - o), 0.05),
                                   facecolor=SURFACE if c >= o else INK2, edgecolor=INK2, linewidth=1.0, zorder=4))
        ax.text(2.1, level + 0.45, "ستوبات البائعين", fontsize=9, color=INK2, va="center", ha="left", zorder=5)
        ax.text(2.1, level - 0.15, "قمة سابقة", fontsize=9, color=INK2, va="top", ha="left", zorder=5)
        title, desc, pct, sig_bar = meta[key]
        if sig_bar is not None:
            top = bars[sig_bar][1]
            ax.plot(sig_bar, top + 0.45, marker="v", markersize=11, color=INK, markeredgecolor=SURFACE,
                    markeredgewidth=1.4, zorder=6)
            ax.text(sig_bar, top + 0.85, "الإشارة هنا", fontsize=9.5, color=INK, ha="center", va="bottom", zorder=6)
        else:
            ax.text(7, 104.0, "لا إشارة", fontsize=9.5, color=MUTED, ha="center", va="bottom", zorder=6)
        ax.set_xlim(-0.8, len(bars) - 0.2)
        ax.set_ylim(94.8, 105.0)
        ax.axis("off")
        cx = left + 0.14
        fig.text(cx, 0.8, title, ha="center", fontsize=13.5, color=INK, weight="bold")
        fig.text(cx, 0.215, f"{pct} من المرات", ha="center", fontsize=12.5, color=INK, weight="bold")
        fig.text(cx, 0.19, desc, ha="center", va="top", fontsize=10, color=INK2, linespacing=1.5)
    fig.text(0.965, 0.03, "70% من مرات أخذ السيولة تعود للداخل، لكن العودة ليست ارتداداً: الوصول إلى 15$ قبل كسر "
             "طرف الذيل حدث في 28.9% فقط، والعشوائية تعطي 33.3%.", ha="right", va="bottom", fontsize=10.5, color=INK2)
    fig.savefig(OUT / fname)
    plt.close(fig)


def htf_value(df, series, tf_sec, t_open):
    """Value of a higher-timeframe series from the last bar closed by t_open (no lookahead)."""
    closed = df.index + pd.Timedelta(seconds=tf_sec) <= t_open
    return series[closed].iloc[-1]


def mockup(base, h1, h4, lives, sig, day_start, day_end, fname):
    """What the indicator should look like over one trading day."""
    t0, t1 = pd.Timestamp(day_start, tz="UTC"), pd.Timestamp(day_end, tz="UTC")
    idx = np.flatnonzero((base.index >= t0) & (base.index < t1))
    i0, i1 = int(idx[0]), int(idx[-1])
    ylo, yhi = y_limits(base, i0, i1)
    span = yhi - ylo
    ylo, yhi = ylo - span * 0.06, yhi + span * 0.1  # room for markers, labels and outcome marks
    fig = plt.figure(figsize=(15.5, 8.6), dpi=125)
    ax = fig.add_axes([0.03, 0.09, 0.59, 0.76])
    style_axes(ax)
    header(fig, "نموذج: شكل المؤشر على الشارت خلال يوم كامل",
           "إشارات حقيقية من البحث، بنفس قواعد المواصفات", f"OANDA:XAUUSD · 15m · {t0:%Y-%m-%d} → {t1:%Y-%m-%d} UTC")
    ax.set_xlim(i0 - 1, i1 + 2)
    ax.set_ylim(ylo, yhi)
    labels = Labels(ax)
    draw_candles(ax, base, i0, i1, width=0.6)
    day = sig[(sig["i"] >= i0) & (sig["i"] <= i1)]
    for _, s in day.iterrows():
        draw_signal(ax, labels, base, s, yhi - ylo, outcome=True)
    hot = [p for ps in day["lv_prices"] for p in ps]
    draw_levels(ax, labels, level_groups(lives, i0, i1, ylo, yhi), highlight=hot, label_all=False)
    time_axis(ax, base, i0, i1, every=8)

    # ---- right column: reading panel, stats table, legend ----
    t_open, px = base.index[i1], base["close"].iloc[i1]
    ema1 = htf_value(h1, h1["close"].ewm(span=50, adjust=False).mean(), 3600, t_open)
    ema4 = htf_value(h4, h4["close"].ewm(span=50, adjust=False).mean(), 14400, t_open)
    days = daily_table(h1)
    emad = days["close"].ewm(span=20, adjust=False).mean()
    emad = emad[pd.to_datetime(days["end"].to_numpy(), unit="s", utc=True) <= t_open].iloc[-1]
    arrow = lambda ema: "▲ صاعد" if px > ema else "▼ هابط"  # noqa: E731
    act = lives[(lives["start"] <= i1) & (lives["stop"] > i1)]
    up = act[act["price"] > px].nsmallest(1, "price")
    dn = act[act["price"] < px].nlargest(1, "price")

    def near(row):
        if row.empty:
            return "—"
        r = row.iloc[0]
        kinds = act[np.isclose(act["price"], r["price"])]["kind"]
        names = " + ".join(kind_label(k, int(r["side"])) for k in sorted(set(kinds), key=KIND_RANK.get))
        return f"{r['price']:.1f}  ({names})  {abs(r['price'] - px):.1f}$"

    last = day.iloc[-1]
    res = "✓ وصل الهدف" if last[f"exit{TP1:g}"] == "tp" else "✗ ضرب الستوب"
    rows = [("ترند الساعة", arrow(ema1)), ("ترند 4 ساعات", arrow(ema4)), ("الترند اليومي", arrow(emad)),
            ("الجلسة", SESSION_AR[session_of(pd.DatetimeIndex([t_open]))[0]]),
            ("ATR(14)", f"{last['atr']:.1f}$"), ("أقرب سيولة فوق", near(up)), ("أقرب سيولة تحت", near(dn)),
            ("آخر إشارة", f"{'بيع' if last['dir'] == -1 else 'شراء'} · {last['type']} · {last['grade']} · {res}")]

    def panel(y_top, height):
        fig.patches.append(FancyBboxPatch((0.668, y_top - height), 0.305, height, transform=fig.transFigure,
                                          boxstyle="round,pad=0.003,rounding_size=0.006", facecolor=SURFACE,
                                          edgecolor=GRID, linewidth=1.1))

    panel(0.845, 0.33)
    fig.text(0.962, 0.83, "لوحة القراءة", ha="right", va="top", fontsize=12.5, color=INK, weight="bold")
    for k, (name, val) in enumerate(rows):
        y = 0.79 - k * 0.0355
        fig.text(0.962, y, name, ha="right", va="top", fontsize=10, color=INK2)
        fig.text(0.68, y, val, ha="left", va="top", fontsize=9.6, color=INK)

    panel(0.495, 0.235)
    fig.text(0.962, 0.48, "جدول الإحصاءات الحي", ha="right", va="top", fontsize=12.5, color=INK, weight="bold")
    fig.text(0.962, 0.452, "الأرقام هنا من البحث كاملاً (11 أسبوعاً، 322 إشارة)", ha="right", va="top",
             fontsize=9, color=MUTED)
    stats = [("التصنيف", "العدد", "ربح 15$", "رمي عملة", "$ للصفقة"),
             ("الكل", "322", "28.9%", "33.3%", "-1.55"), ("A", "38", "31.6%", "35.3%", "-0.62"),
             ("B", "10", "40.0%", "32.1%", "+1.21"), ("AVOID", "274", "28.1%", "33.1%", "-1.78")]
    cols = [0.962, 0.885, 0.825, 0.76, 0.7]
    for r, row in enumerate(stats):
        for cx, cell in zip(cols, row):
            fig.text(cx, 0.418 - r * 0.0265, cell, ha="right", va="top", fontsize=9.6,
                     color=INK if r == 0 else INK2, weight="bold" if r == 0 else "normal")
    fig.text(0.962, 0.29, "الربح أقل من رمي العملة في كل الصفوف تقريباً: لا ميزة مثبتة بعد.",
             ha="right", va="top", fontsize=9, color=INK2)

    fig.legend(*zip(*legend_items(with_signals=True)), loc="upper right", bbox_to_anchor=(0.975, 0.245), ncol=1,
               fontsize=9.5, frameon=False, labelcolor=INK2, markerfirst=False, handlelength=2.2)
    fig.text(0.62, 0.025, "▼ سحب قمم (بيع) · ▲ سحب قيعان (شراء) · الوسم = نوع السحب (W ذيل، C شمعة) · التصنيف · "
             "✓ / ✗ = نتيجة الهدف الأول 15$", ha="right", va="bottom", fontsize=10, color=INK2)
    fig.savefig(OUT / fname)
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    base, h1, h4, lives, sig = prepare()
    concept("01_concept.png")
    example(base, lives, sig, "2026-10-15 12:30",
            "سحب قاع في صباح نيويورك، ووصل الهدفين",
            "سحب بالذيل لقاع على فريمي 15 دقيقة والساعة · تصنيف A · مع ترند الساعة",
            "مثال ناجح، لكن لاحظ حجم الستوب: 17$ لأن الذيل طويل. الهدف 15$ ثم 20$ تحققا خلال ساعة.",
            "02_win_A.png", pre=34, post=26)
    example(base, lives, sig, "2026-08-19 07:30",
            "ذيل «جميل» فوق قمة، ثم ضرب الستوب وصعد السعر نحو 145$",
            "سحب بالذيل لقمة على 15 دقيقة والساعة وقمة آسيا · تصنيف A · جلسة لندن",
            "الرفض القوي لا يضمن شيئاً. هذه هي النتيجة الأكثر تكراراً: نحو 71% من الإشارات لم تصل 15$ قبل الستوب.",
            "03_loss_A.png", pre=30, post=34)
    example(base, lives, sig, "2026-09-04 07:00",
            "سحب بالشمعة: إغلاق تحت القاع، ثم عودة فوقه",
            "سحب بالشمعة لقاع على 15 دقيقة وقاع آسيا · تصنيف A · جلسة لندن",
            "شمعة أغلقت تحت القاع، والتي بعدها أغلقت فوقه. الإشارة تظهر عند إغلاق شمعة العودة، لا قبلها.",
            "04_candle_sweep.png", pre=30, post=16)
    example(base, lives, sig, "2026-10-02 06:00",
            "«السيولة على كل الفريمات»: ذيل واحد أخذ خمسة مستويات معاً",
            "15 دقيقة والساعة والأربع ساعات وقمة أمس وقمة آسيا ضمن دولار واحد · تصنيف AVOID",
            "تعدد الفريمات لم يعطِ ارتداداً أقوى في البحث. هنا نجح (20$)، لكنه مصنف AVOID لأنه عكس ترند الساعة.",
            "05_multi_timeframe.png", pre=40, post=22)
    mockup(base, h1, h4, lives, sig, "2026-08-23 21:00", "2026-08-24 21:00", "06_indicator_mockup.png")
    print("written:", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
