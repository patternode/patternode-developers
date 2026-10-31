"""Finance: trades into Delve, with nanosecond times, live and in backtest.

    PATTERNODE_API_KEY=pnk_live_... python examples/industries/finance/trades_to_delve.py

Reads trades (symbol, time_ns, price, size) as a market data feed or a tick store gives them.
For each instrument it:

1. Builds one-second bars from trades, open and close the first and last trade, high and low
   the extremes. A second with no trade is a gap, not a flat bar.
2. Keeps nanosecond times end to end (time_unit "ns", sent as strings in JSON).
3. Backtests: segments the whole day as a finished series with a pinned profile version, and
   checks a second run gives the same segments, bit for bit.
4. Goes live from where the backtest ended: the finished series returns its edge, and as
   each second closes one request extends every instrument from its stored edge. Patternode
   keeps nothing; the edges live in your store. At full scale use the gRPC transport
   (Mission Critical): the same operation on one connection.

The instruments and trades are invented.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "python"))

from patternode_client import Patternode  # noqa: E402
from segment_store import SegmentStore  # noqa: E402

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


def main(path: Path = HERE / "trades.csv", store_root: Path = Path("out")) -> None:
    trades = defaultdict(list)
    with path.open() as f:
        for row in csv.DictReader(f):
            trades[row["symbol"]].append((int(row["time_ns"]), float(row["price"])))
    pn = Patternode()
    store = SegmentStore(store_root / "fund")

    live = {}
    for symbol, ts in trades.items():
        bars = bars_from_trades(ts)
        history, tail = bars[:-20], bars[-20:]
        name = f"eq/{symbol.lower()}/1s"
        body = {"series": name, "profile": PROFILE, "time_unit": "ns", "bars": history, "return_edge": True}
        a = pn.post("/v1/segmentations", body)
        b = pn.post("/v1/segmentations", body)
        same = a["segments"] == b["segments"] and a["edge"] == b["edge"]
        print(f"{symbol}: {len(ts)} trades -> {a['bars']} bars -> {len(a['segments'])} segments, "
              f"{a['profile_version']}, reproducible: {same}")
        if not same:
            raise SystemExit("two runs of one profile version differed")
        store.apply_segmentation(name, a)
        live[name] = tail

    closed = 0
    for i in range(20):                               # each second closes
        names = list(live)
        edges = [store.edge(n) for n in names]
        items = [{"series": n, "profile": e.profile_version, "edge": e.token, "bars": [live[n][i]]}
                 for n, e in zip(names, edges)]
        out = pn.post("/v1/segmentations/extend/batch", {"time_unit": "ns", "items": items})
        for n, e, r in zip(names, edges, out["results"]):
            if r["status"] != 200:
                raise SystemExit(r["error"])
            store.apply_extension(n, r["result"], expected_version=e.version)
            closed += len(r["result"]["closed"])
    print(f"live: {closed} segments closed across {len(live)} instruments; edges kept in your store")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "trades.csv")
