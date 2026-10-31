"""Pattern 2, a forming series: send each bar as it closes, and act on what it did. Preview.

    PATTERNODE_API_KEY=pnk_live_... python examples/python/forming_series.py examples/data/export-kw.json

Keep the stream_id and the last sequence with the series in your own store. Each bar carries
its sequence: a repeat (a retry) returns the first answer and applies nothing, and a gap is
refused with 409 sequence_gap naming the sequence to send. Either way the stream is unchanged.
"""

import json
import sys
from pathlib import Path

from patternode_client import Patternode, PatternodeError


def main(path: str) -> None:
    bars = json.loads(Path(path).read_text())
    pn = Patternode()
    first = pn.post("/v1/streams", {"series": "exu/demo/forming/ac-power", "bar": bars[0]})
    stream_id = first["stream_id"]
    print(f"opened {stream_id}")
    sequence = 1  # the opening bar
    for bar in bars[1:]:
        try:
            r = pn.post(f"/v1/streams/{stream_id}/observations", {"sequence": sequence + 1, "bar": bar})
        except PatternodeError as e:
            if e.code == "out_of_order":  # a late bar: nothing was applied, so its sequence is free
                print(f"skipped a bar at {bar[0]}: out of order")
                continue
            raise
        sequence = r["sequence"]
        closed = [ev for ev in r["events"] if ev["kind"] == "segmented"]
        for ev in closed:  # a segment is final: store it, redraw, notify
            print(f"bar {r['bars']}: level {ev['level'] + 1} closed {ev['node']['id']} "
                  f"({ev['node']['open']} -> {ev['node']['close']})")
    edge = pn.get(f"/v1/streams/{stream_id}")["right_edge"]
    print("open at each level:", ", ".join(s["id"] for s in edge))
    pn.delete(f"/v1/streams/{stream_id}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "examples/data/export-kw.json")
