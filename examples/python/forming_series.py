"""Pattern 2, a forming series: send the edge with each new bar, store what comes back. Preview.

    PATTERNODE_API_KEY=pnk_live_... python examples/python/forming_series.py examples/data/export-kw.json

Patternode keeps nothing between calls. Each answer carries the series' edge, a sealed token;
SegmentStore keeps it with the segments and sends it back with the next bars. A retry with
the same edge and bars gives the same answer, so a timeout is safe to retry.
"""

import json
import sys
import tempfile
from pathlib import Path

from patternode_client import Patternode, PatternodeError
from segment_store import SegmentStore


def main(path: str) -> None:
    bars = json.loads(Path(path).read_text())
    pn = Patternode()
    store = SegmentStore(Path(tempfile.mkdtemp()) / "example-utility")   # in production: your store, per client
    series = "exu/demo/forming/ac-power"
    for bar in bars:                                                       # as each bar closes
        try:
            r = store.extend(pn, series, [bar], profile="standard@2026-11")
        except PatternodeError as e:
            if e.code == "out_of_order":   # a late bar: nothing was applied, the edge is unchanged
                print(f"skipped a bar at {bar[0]}: out of order")
                continue
            raise
        for s in r["closed"]:              # final: redraw, notify
            print(f"bar {r['bars']}: level {s['height']} closed {s['id']} ({s['open']} -> {s['close']})")
    edge = store.edge(series)
    print(f"open at each level: {', '.join(s['id'] for s in store.right_edge(series))}")
    print(f"trend: {store.trend(series)}; edge {len(edge.token)} bytes, next bar after {edge.last_close_time}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "examples/data/export-kw.json")
