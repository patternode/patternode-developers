"""Finance: trades into Delve, with nanosecond times, live and in backtest.

    PATTERNODE_API_KEY=pnk_live_... python examples/industries/finance/trades_to_delve.py

Reads trades (symbol, time_ns, price, size) as a market data feed or a tick store gives them.
For each instrument it:

1. Builds one-second bars from trades, open and close the first and last trade, high and low
   the extremes. A second with no trade is a gap, not a flat bar.
2. Keeps nanosecond times end to end (time_unit "ns", sent as strings in JSON).
3. Backtests: segments the whole day as a finished series with a pinned profile version, and
   checks a second run gives the same segments, bit for bit.
4. Goes live: opens a stream per instrument and sends every instrument's new bar in one
   request as each second closes. At full scale use the gRPC transport instead (Mission
   Critical): the same operations on one connection.

The instruments and trades are invented.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "python"))

from patternode_client import Patternode  # noqa: E402

BAR_NS = 1_000_000_000
PROFILE = "standard@2026-11"   # pinned: a backtest must reproduce


def bars_from_trades(trades: list[tuple[int, float]]) -> list[list]:
    buckets = defaultdict(list)
    for t, px in trades:
        buckets[t // BAR_NS].append((t, px))
    bars = []
    for _, ts in sorted(buckets.items()):
        prices = [p for _, p in ts]
        bars.append([str(ts[0][0]), str(ts[-1][0]), prices[0], max(prices), min(prices), prices[-1]])
    return bars


def main(path: Path = HERE / "trades.csv") -> None:
    trades = defaultdict(list)
    with path.open() as f:
        for row in csv.DictReader(f):
            trades[row["symbol"]].append((int(row["time_ns"]), float(row["price"])))
    pn = Patternode()

    live = {}
    for symbol, ts in trades.items():
        bars = bars_from_trades(ts)
        history, tail = bars[:-20], bars[-20:]
        body = {"series": f"eq/{symbol.lower()}/1s", "profile": PROFILE, "time_unit": "ns", "bars": history}
        a = pn.post("/v1/segmentations", body)
        b = pn.post("/v1/segmentations", body)
        same = a["segments"] == b["segments"]
        print(f"{symbol}: {len(ts)} trades -> {a['bars']} bars -> {len(a['segments'])} segments, "
              f"{a['profile_version']}, reproducible: {same}")
        if not same:
            raise SystemExit("two runs of one profile version differed")
        opened = pn.post("/v1/streams", {"series": f"eq/{symbol.lower()}/1s", "profile": PROFILE,
                                         "time_unit": "ns", "bar": tail[0]})
        live[symbol] = {"id": opened["stream_id"], "sequence": 1, "pending": tail[1:]}

    closed = 0
    while any(s["pending"] for s in live.values()):
        batch = [{"stream_id": s["id"], "sequence": s["sequence"] + 1, "bar": s["pending"].pop(0)}
                 for s in live.values() if s["pending"]]
        out = pn.post("/v1/streams/observations", {"time_unit": "ns", "observations": batch})
        for item, r in zip(batch, out["results"]):
            if r["status"] != 200:
                raise SystemExit(r["error"])
            next(s for s in live.values() if s["id"] == item["stream_id"])["sequence"] = item["sequence"]
            closed += sum(ev["kind"] == "segmented" for ev in r["result"]["events"])
    print(f"live: {closed} segments closed across {len(live)} instruments")
    for s in live.values():
        pn.delete(f"/v1/streams/{s['id']}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "trades.csv")
