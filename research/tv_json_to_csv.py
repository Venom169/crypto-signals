"""Merge TradingView MCP get_ohlcv JSON pages (format="columns") into one CSV.

Usage:
    python research/tv_json_to_csv.py OUT.csv PAGE1.json [PAGE2.json ...]

Pages may overlap; bars are de-duplicated by timestamp and sorted. If OUT.csv
already exists its bars are kept, so re-running this every few weeks grows the
history beyond the few thousand intraday bars TradingView serves at once.
The newest bar of the merged series is dropped because it is still forming
when the data is fetched.
"""
import csv
import json
import os
import sys
from datetime import datetime, timezone


def load_pages(paths):
    bars = {}
    for path in paths:
        with open(path) as f:
            doc = json.load(f)
        if not doc.get("success", True):
            raise SystemExit(f"{path}: fetch was not successful: {doc.get('error')}")
        cols = doc["bars"]
        for t, o, h, l, c, v in zip(cols["t"], cols["o"], cols["h"], cols["l"], cols["c"], cols["v"]):
            bars[int(t)] = (o, h, l, c, v)
    return bars


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    out, pages = sys.argv[1], sys.argv[2:]
    bars = {}
    if os.path.exists(out):
        with open(out) as f:
            for row in csv.DictReader(f):
                bars[int(row["t"])] = tuple(float(row[k]) for k in ("open", "high", "low", "close", "volume"))
    fetched = load_pages(pages)
    bars.update(fetched)
    del bars[max(fetched)]  # the newest fetched bar was still forming
    times = sorted(bars)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_utc", "t", "open", "high", "low", "close", "volume"])
        for t in times:
            o, h, l, c, v = bars[t]
            iso = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
            w.writerow([iso, t, o, h, l, c, v])
    print(f"{out}: {len(times)} bars, {datetime.fromtimestamp(times[0], tz=timezone.utc):%Y-%m-%d %H:%M} -> "
          f"{datetime.fromtimestamp(times[-1], tz=timezone.utc):%Y-%m-%d %H:%M} UTC")


if __name__ == "__main__":
    main()
