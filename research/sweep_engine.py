"""Liquidity-sweep engine for gold (OANDA:XAUUSD).

The idea under test: when a wick or a candle takes out a liquidity level (a
prior swing high/low on the chart timeframe, 1H or 4H, the previous day or
week high/low, or the Asian session range) and price closes back inside, it
then reverses $15-20 before breaking the sweep extreme.

No lookahead anywhere: a pivot is usable only after its right-hand bars have
closed, higher-timeframe values only after their bar has closed, and every
signal is taken at the close of the bar that completes it.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
NY = "America/New_York"
NEVER = 2**62

# How "big" each kind of level is, used for the multi-timeframe score.
KIND_RANK = {"P": 1, "ASIA": 2, "P1H": 3, "PD": 4, "P4H": 5, "PW": 6}


def load(tf: str) -> pd.DataFrame:
    df = pd.read_csv(DATA / f"xauusd_{tf}.csv")
    df.index = pd.to_datetime(df["t"], unit="s", utc=True)
    df.index.name = "time"
    return df[["open", "high", "low", "close", "volume"]].astype(float)


def unix(index: pd.DatetimeIndex) -> np.ndarray:
    return pd.DatetimeIndex(index).as_unit("s").asi8.astype(np.int64)


def bar_seconds(df: pd.DataFrame) -> int:
    return int(pd.Series(unix(df.index)).diff().mode().iloc[0])


def trading_date(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Gold's trading day rolls at 17:00 New York, like TradingView's daily bars."""
    wall = index.tz_convert(NY).tz_localize(None)
    return (wall + pd.Timedelta(hours=7)).normalize()


def ny_hour(index: pd.DatetimeIndex) -> np.ndarray:
    return index.tz_convert(NY).hour.to_numpy()


def session_of(index: pd.DatetimeIndex) -> np.ndarray:
    """Session by New York wall-clock time (keeps London/NY opens right across DST)."""
    h = ny_hour(index)
    return np.select(
        [(h >= 18) | (h < 2), (h >= 2) & (h < 8), (h >= 8) & (h < 12)],
        ["asia", "london", "ny_am"],
        default="ny_pm",
    )


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


# --------------------------------------------------------------------------
# Liquidity levels
# --------------------------------------------------------------------------

@dataclass
class Level:
    price: float
    side: int    # +1: level above price (buy stops rest above), -1: below (sell stops)
    kind: str    # P (chart-timeframe pivot), P1H, P4H, ASIA, PD, PW
    start: int   # usable by bars that open at or after this unix time
    end: int     # not usable by bars that open at or after this unix time
    born: int    # unix time of the bar that made the level


def pivot_levels(df: pd.DataFrame, k: int, kind: str) -> list[Level]:
    """Fractal swing points: higher/lower than k bars on each side.

    Confirmed only when the k-th bar to the right has closed.
    """
    sec = bar_seconds(df)
    ts = unix(df.index)
    h, l = df["high"].to_numpy(), df["low"].to_numpy()
    out = []
    for i in range(k, len(df) - k):
        confirmed = int(ts[i + k] + sec)
        if h[i] > h[i - k:i].max() and h[i] >= h[i + 1:i + k + 1].max():
            out.append(Level(h[i], 1, kind, confirmed, NEVER, int(ts[i])))
        if l[i] < l[i - k:i].min() and l[i] <= l[i + 1:i + k + 1].min():
            out.append(Level(l[i], -1, kind, confirmed, NEVER, int(ts[i])))
    return out


def daily_table(h1: pd.DataFrame) -> pd.DataFrame:
    """Daily OHLC on the 17:00 New York roll, with start/end unix times."""
    td = trading_date(h1.index)
    g = h1.assign(td=td, ts=unix(h1.index)).groupby("td")
    days = pd.DataFrame({
        "open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
        "close": g["close"].last(), "start": g["ts"].min(), "end": g["ts"].max() + 3600,
    })
    return days[days.index.dayofweek < 5]  # drop stray weekend stubs, if any


def calendar_levels(h1: pd.DataFrame) -> list[Level]:
    """Previous day / previous week high-low and the Asian (Tokyo) range."""
    days = daily_table(h1)
    out = []
    prev = None
    for d, row in days.iterrows():
        if prev is not None:
            out.append(Level(prev["high"], 1, "PD", int(row.start), int(row.end), int(prev["start"])))
            out.append(Level(prev["low"], -1, "PD", int(row.start), int(row.end), int(prev["start"])))
        prev = row

    weeks = days.groupby(days.index.to_period("W-FRI")).agg(
        high=("high", "max"), low=("low", "min"), start=("start", "min"), end=("end", "max"))
    prev = None
    for _, row in weeks.iterrows():
        if prev is not None:
            out.append(Level(prev["high"], 1, "PW", int(row.start), int(row.end), int(prev["start"])))
            out.append(Level(prev["low"], -1, "PW", int(row.start), int(row.end), int(prev["start"])))
        prev = row

    # Tokyo session 00:00-06:00 UTC (fixed: Japan has no DST); live until the day ends.
    hrs = h1.index.hour
    asia = h1[(hrs >= 0) & (hrs < 6)]
    g = asia.groupby(trading_date(asia.index))
    for d, grp in g:
        if len(grp) < 5 or d not in days.index:
            continue
        start = int(pd.Timestamp(d.date(), tz="UTC").timestamp()) + 6 * 3600
        end = int(days.loc[d, "end"])
        out.append(Level(grp["high"].max(), 1, "ASIA", start, end, int(unix(grp.index)[0])))
        out.append(Level(grp["low"].min(), -1, "ASIA", start, end, int(unix(grp.index)[0])))
    return out


def drop_taken_before(levels: list[Level], ref: pd.DataFrame, until: int) -> list[Level]:
    """Remove levels that price already traded through before the study window."""
    ts = unix(ref.index)
    h, l = ref["high"].to_numpy(), ref["low"].to_numpy()
    keep = []
    for L in levels:
        if L.end <= until:
            continue
        if L.start < until:
            a, b = np.searchsorted(ts, L.start), np.searchsorted(ts, until)
            seg = h[a:b] if L.side == 1 else l[a:b]
            if len(seg) and ((seg > L.price).any() if L.side == 1 else (seg < L.price).any()):
                continue
        keep.append(L)
    return keep


def build_levels(base: pd.DataFrame, h1: pd.DataFrame, h4: pd.DataFrame, base_k: int = 5,
                 htf_k: int = 3) -> list[Level]:
    start = int(unix(base.index)[0])
    lv = pivot_levels(base, base_k, "P")
    if bar_seconds(base) < 3600:
        lv += pivot_levels(h1, htf_k, "P1H")
    lv += pivot_levels(h4[h4.index >= h1.index[0]], htf_k, "P4H")
    lv += calendar_levels(h1)
    return drop_taken_before(lv, h1, start)


# --------------------------------------------------------------------------
# Sweep detection
# --------------------------------------------------------------------------

def find_sweeps(base: pd.DataFrame, levels: list[Level], candle_bars: int = 2,
                min_pen: float = 0.0) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Walk the bars and record every time a level is taken.

    A level is "taken" when a bar that opened on the near side trades beyond it.
      W (wick sweep):   the same bar closes back inside every level it took.
      C (candle sweep): the bar closes beyond, and one of the next `candle_bars`
                        bars closes back inside the nearest level it took.
    Returns (signals, takes). One signal per bar per side; a bar that sweeps
    both sides is ambiguous and skipped.
    """
    o, h, l, c = (base[x].to_numpy() for x in ("open", "high", "low", "close"))
    ts = unix(base.index)
    levels = sorted(levels, key=lambda L: L.start)
    nxt, active, pending = 0, {1: [], -1: []}, []
    signals, takes = [], []

    for i in range(len(base)):
        t = ts[i]
        while nxt < len(levels) and levels[nxt].start <= t:
            L = levels[nxt]
            nxt += 1
            ref_px = c[i - 1] if i else o[i]
            if (L.side == 1 and L.price > ref_px) or (L.side == -1 and L.price < ref_px):
                active[L.side].append(L)
        for s in (1, -1):
            active[s] = [L for L in active[s] if L.end > t]

        sig = {1: None, -1: None}

        def add(s, kind, lv, ext, ref):
            cur = sig[s]
            if cur is None:
                sig[s] = dict(type=kind, levels=list(lv), ext=ext, ref=ref)
            else:
                cur["type"] = "W+C" if cur["type"] != kind else kind
                cur["levels"] += lv
                cur["ext"] = max(cur["ext"], ext) if s == 1 else min(cur["ext"], ext)
                cur["ref"] = min(cur["ref"], ref) if s == 1 else max(cur["ref"], ref)

        # Candle sweeps completing on this bar (breaks from earlier bars).
        still = []
        for p in pending:
            s = p["side"]
            p["ext"] = max(p["ext"], h[i]) if s == 1 else min(p["ext"], l[i])
            back = c[i] < p["ref"] if s == 1 else c[i] > p["ref"]
            if back:
                add(s, "C", p["levels"], p["ext"], p["ref"])
                takes[p["take"]]["outcome"] = f"C{i - p['i0']}"
            elif i - p["i0"] < candle_bars:
                still.append(p)
        pending = still

        # New levels taken on this bar.
        for s in (1, -1):
            beyond = (h[i] > np.array([L.price + min_pen for L in active[s]])) if s == 1 else \
                     (l[i] < np.array([L.price - min_pen for L in active[s]]))
            if not len(active[s]) or not beyond.any():
                continue
            taken = [L for L, b in zip(active[s], beyond) if b]
            active[s] = [L for L, b in zip(active[s], beyond) if not b]
            crossed = [L for L in taken if (o[i] <= L.price if s == 1 else o[i] >= L.price)]
            if not crossed:
                continue  # gapped through: no sweep to trade
            ref = min(L.price for L in crossed) if s == 1 else max(L.price for L in crossed)
            ext = h[i] if s == 1 else l[i]
            inside = c[i] < ref if s == 1 else c[i] > ref
            takes.append(dict(i=i, side=s, ref=ref, ext=ext, close=c[i],
                              kinds="+".join(sorted({L.kind for L in crossed}, key=KIND_RANK.get)),
                              outcome="W" if inside else "B"))
            if inside:
                add(s, "W", crossed, ext, ref)
            else:
                pending.append(dict(side=s, ref=ref, ext=ext, i0=i, levels=crossed, take=len(takes) - 1))

        if sig[1] and sig[-1]:
            continue
        for s in (1, -1):
            if sig[s]:
                v = sig[s]
                kinds = sorted({L.kind for L in v["levels"]}, key=KIND_RANK.get)
                signals.append(dict(
                    i=i, time=base.index[i], side=s, dir=-s, type=v["type"], entry=c[i],
                    ext=v["ext"], ref=v["ref"], kinds="+".join(kinds), n_kinds=len(kinds),
                    top_rank=max(KIND_RANK[k] for k in kinds),
                    level_age_h=(t - min(L.born for L in v["levels"])) / 3600,
                    n_levels=len(v["levels"]),
                    lv_prices=[L.price for L in v["levels"]],
                ))
    return pd.DataFrame(signals), pd.DataFrame(takes)


# --------------------------------------------------------------------------
# Context features (all known at the signal bar's close)
# --------------------------------------------------------------------------

def add_features(sig: pd.DataFrame, base: pd.DataFrame, h1: pd.DataFrame, h4: pd.DataFrame) -> pd.DataFrame:
    sig = sig.copy()
    sec = bar_seconds(base)
    a = atr(base).to_numpy()
    o, h, l, c = (base[x].to_numpy() for x in ("open", "high", "low", "close"))
    i = sig["i"].to_numpy()
    d = sig["dir"].to_numpy()
    rng = h[i] - l[i]
    sig["atr"] = a[np.maximum(i - 1, 0)]
    sig["bar_range"] = rng
    sig["range_atr"] = rng / sig["atr"]
    # close location: 0 = closed at the sweep end of the bar, 1 = at the far end
    sig["close_loc"] = np.where(d == -1, (h[i] - c[i]) / np.where(rng > 0, rng, np.nan),
                                (c[i] - l[i]) / np.where(rng > 0, rng, np.nan))
    sig["pen"] = np.abs(sig["ext"] - sig["ref"])          # how far beyond the first level
    sig["risk_wick"] = np.abs(sig["ext"] - sig["entry"])  # entry to sweep extreme
    lookback = 8
    prev_c = c[np.maximum(i - lookback, 0)]
    sig["run_in_atr"] = (c[np.maximum(i - 1, 0)] - prev_c) * (-d) / sig["atr"]  # move into the level
    sig["session"] = session_of(sig["time"].pipe(pd.DatetimeIndex))
    sig["ny_hour"] = ny_hour(pd.DatetimeIndex(sig["time"]))
    # Higher-timeframe values come from bars that closed by the signal bar's OPEN - the same
    # thing Pine's request.security(..., expr[1], lookahead_on) gives, so the indicator can match.
    open_time = pd.DatetimeIndex(sig["time"]).as_unit("ns")

    def htf_value(df, series, tf_sec):
        avail = pd.DataFrame({"t": (df.index + pd.Timedelta(seconds=tf_sec)).as_unit("ns"), "v": series.to_numpy()})
        q = pd.DataFrame({"t": open_time}).reset_index()
        m = pd.merge_asof(q.sort_values("t"), avail.sort_values("t"), on="t", direction="backward")
        return m.sort_values("index")["v"].to_numpy()

    ema1h = h1["close"].ewm(span=50, adjust=False).mean()
    ema4h = h4["close"].ewm(span=50, adjust=False).mean()
    sig["ema50_1h"] = htf_value(h1, ema1h, 3600)
    sig["ema50_4h"] = htf_value(h4, ema4h, 14400)
    days = daily_table(h1)
    ema_d = days["close"].ewm(span=20, adjust=False).mean()
    day_end = pd.to_datetime(days["end"].to_numpy(), unit="s", utc=True).as_unit("ns")
    avail = pd.DataFrame({"t": day_end, "ema": ema_d.to_numpy()})
    q = pd.DataFrame({"t": open_time}).reset_index()
    m = pd.merge_asof(q.sort_values("t"), avail.sort_values("t"), on="t", direction="backward")
    sig["ema20_d"] = m.sort_values("index")["ema"].to_numpy()
    # today's open (17:00 NY)
    td = trading_date(base.index)
    day_open = base["open"].groupby(td).transform("first").to_numpy()
    sig["day_open"] = day_open[i]

    # +1 when the trade goes with that trend, -1 against it
    for col in ("ema50_1h", "ema50_4h", "ema20_d", "day_open"):
        sig[f"with_{col}"] = np.sign((sig["entry"] - sig[col]) * d).fillna(0).astype(int)  # 0 = no history yet

    # round numbers: any taken level within $3 of a $50 multiple
    sig["near_round50"] = [min(abs(p - round(p / 50) * 50) for p in ps) <= 3 for ps in sig["lv_prices"]]
    # equal highs/lows: two or more distinct swing prices within $1.5 in the same sweep
    def has_equal(ps):
        u = np.unique(np.round(ps, 2))
        return len(u) > 1 and np.diff(u).min() <= 1.5
    sig["equal_levels"] = [has_equal(ps) for ps in sig["lv_prices"]]
    sig["grade"] = grade(sig, "with_ema50_1h" if sec < 3600 else "with_ema50_4h")
    return sig


def grade(sig: pd.DataFrame, trend_col: str) -> np.ndarray:
    """Research-based context grade. Nothing here is a proven edge (see RESULTS.md):
    AVOID = contexts that lost in every sample; A = the least-bad context; B = the rest."""
    trend = sig[trend_col].to_numpy()
    avoid = (sig["session"].to_numpy() == "asia") | sig["near_round50"].to_numpy() | (trend == -1)
    a = ~avoid & (trend == 1) & np.isin(sig["session"].to_numpy(), ["london", "ny_am"])
    return np.where(avoid, "AVOID", np.where(a, "A", "B"))


def failed_sweeps(base: pd.DataFrame, sig: pd.DataFrame, watch: int) -> pd.DataFrame:
    """Sweeps whose extreme is later closed beyond: re-issued as trades in the break direction."""
    c = base["close"].to_numpy()
    rows = []
    for _, r in sig.iterrows():
        i, d, ext = int(r["i"]), int(r["dir"]), r["ext"]
        for j in range(i + 1, min(i + 1 + watch, len(base) - 1)):
            if (d == -1 and c[j] > ext) or (d == 1 and c[j] < ext):
                r2 = r.copy()
                r2["i"], r2["dir"], r2["entry"], r2["time"] = j, -d, c[j], base.index[j]
                r2["ny_hour"] = int(ny_hour(pd.DatetimeIndex([base.index[j]]))[0])
                rows.append(r2)
                break
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Trade simulation
# --------------------------------------------------------------------------

def stop_distance(sig: pd.DataFrame, rule: tuple) -> np.ndarray:
    kind, x = rule[0], rule[1]
    if kind == "wick":       # beyond the sweep extreme + buffer
        s = sig["risk_wick"].to_numpy() + x
    elif kind == "wickmin":  # beyond the extreme + $1, but never tighter than x
        s = np.maximum(sig["risk_wick"].to_numpy() + 1.0, x)
    elif kind == "fixed":
        s = np.full(len(sig), float(x))
    elif kind == "atr":      # beyond the extreme + x * ATR
        s = sig["risk_wick"].to_numpy() + x * sig["atr"].to_numpy()
    elif kind == "fixed_atr":
        s = x * sig["atr"].to_numpy()
    else:
        raise ValueError(rule)
    return s


def simulate(base: pd.DataFrame, idx: np.ndarray, dirs: np.ndarray, stop: np.ndarray,
             target: np.ndarray, max_bars: int, cost: float) -> pd.DataFrame:
    """Enter at the close of bar idx, exit at stop/target/time.

    Gaps through a level fill at the open. If one bar touches both stop and
    target the stop is assumed first (conservative); such trades are flagged.
    """
    o, h, l, c = (base[x].to_numpy() for x in ("open", "high", "low", "close"))
    n = len(base)
    rows = []
    for i, d, s, t in zip(idx, dirs, stop, target):
        e = c[i]
        sl, tp = e - d * s, e + d * t
        exit_px, why, bars, amb = None, "time", 0, False
        last = min(i + max_bars, n - 1)
        for j in range(i + 1, last + 1):
            bars = j - i
            if d == 1:
                if o[j] <= sl: exit_px, why = o[j], "sl"; break
                if o[j] >= tp: exit_px, why = o[j], "tp"; break
                hit_sl, hit_tp = l[j] <= sl, h[j] >= tp
            else:
                if o[j] >= sl: exit_px, why = o[j], "sl"; break
                if o[j] <= tp: exit_px, why = o[j], "tp"; break
                hit_sl, hit_tp = h[j] >= sl, l[j] <= tp
            if hit_sl:
                exit_px, why, amb = sl, "sl", hit_tp
                break
            if hit_tp:
                exit_px, why = tp, "tp"
                break
        if exit_px is None:
            exit_px = c[last]
        rows.append((d * (exit_px - e) - cost, why, bars, amb, s, t))
    return pd.DataFrame(rows, columns=["pnl", "exit", "bars", "ambiguous", "stop", "target"])


def mfe_before_invalidation(base: pd.DataFrame, sig: pd.DataFrame, buffer: float, max_bars: int) -> np.ndarray:
    """Largest favourable move (in $) before price trades beyond the sweep extreme + buffer."""
    h, l, c = base["high"].to_numpy(), base["low"].to_numpy(), base["close"].to_numpy()
    n = len(base)
    out = []
    for i, d, ext in zip(sig["i"], sig["dir"], sig["ext"]):
        e, best = c[i], 0.0
        inval = ext + buffer if d == -1 else ext - buffer
        for j in range(i + 1, min(i + max_bars, n - 1) + 1):
            if (d == -1 and h[j] >= inval) or (d == 1 and l[j] <= inval):
                break  # same-bar order unknown: count the invalidation first
            best = max(best, (e - l[j]) if d == -1 else (h[j] - e))
        out.append(best)
    return np.array(out)


def random_baseline(base: pd.DataFrame, sig: pd.DataFrame, stop: np.ndarray, target: np.ndarray,
                    max_bars: int, cost: float, per_signal: int = 30, seed: int = 7) -> pd.DataFrame:
    """Same direction, stop and target, but entered at random bars of the same New York hour."""
    rng = np.random.default_rng(seed)
    hours = ny_hour(base.index)
    n = len(base)
    pools = {hh: np.flatnonzero((hours == hh) & (np.arange(n) < n - max_bars - 1)) for hh in range(24)}
    idx, dirs, ss, tt = [], [], [], []
    for (_, row), s, t in zip(sig.iterrows(), stop, target):
        pool = pools[row["ny_hour"]]
        pick = rng.choice(pool, size=per_signal, replace=True)
        idx += list(pick)
        dirs += [row["dir"]] * per_signal
        ss += [s] * per_signal
        tt += [t] * per_signal
    return simulate(base, np.array(idx), np.array(dirs), np.array(ss), np.array(tt), max_bars, cost)


def one_at_a_time(sig: pd.DataFrame, res: pd.DataFrame) -> np.ndarray:
    """Mask of trades you could actually take with one position open at a time."""
    keep, busy_until = [], -1
    for i, bars in zip(sig["i"].to_numpy(), res["bars"].to_numpy()):
        if i > busy_until:
            keep.append(True)
            busy_until = i + max(bars, 1)
        else:
            keep.append(False)
    return np.array(keep)


def summarize(res: pd.DataFrame, p0: np.ndarray | None = None) -> dict:
    n = len(res)
    if n == 0:
        return dict(n=0)
    pnl = res["pnl"].to_numpy()
    win = (res["exit"] == "tp").to_numpy()
    gross_win, gross_loss = pnl[pnl > 0].sum(), -pnl[pnl < 0].sum()
    eq = np.cumsum(pnl)
    dd = (np.maximum.accumulate(np.concatenate([[0], eq]))[1:] - eq).max()
    out = dict(
        n=n, win=win.mean(), sl=(res["exit"] == "sl").mean(), timeout=(res["exit"] == "time").mean(),
        avg_stop=res["stop"].mean(), exp=pnl.mean(), total=pnl.sum(),
        pf=gross_win / gross_loss if gross_loss > 0 else np.inf, maxdd=dd,
        se=pnl.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan,
        amb=res["ambiguous"].mean(),
    )
    if p0 is not None:
        out["p_rand_walk"] = p0.mean()
    return out
