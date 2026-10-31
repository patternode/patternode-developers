"""Pattern 1, a finished series: send it once, store the segments beside your own data.

    PATTERNODE_API_KEY=pnk_live_... python examples/python/finished_series.py examples/data/export-kw.json

The series name is opaque: a hash of your client and asset, never their names. Patternode
keeps nothing of the series after it answers; the segments live in your store.
"""

import hashlib
import json
import sys
from pathlib import Path

from patternode_client import Patternode
from segment_store import SegmentStore


def series_name(client_id: str, asset_id: str, measure: str, salt: str) -> str:
    """An opaque, stable name: the same asset always gets the same name, and no one can read it."""
    h = lambda s: hashlib.sha256((salt + s).encode()).hexdigest()[:12]  # noqa: E731
    return f"{h(client_id)}/{h(asset_id)}/{measure}"


def main(path: str) -> None:
    bars = json.loads(Path(path).read_text())
    name = series_name("example-utility", "inverter-07", "ac-power", salt="rotate-me-per-environment")
    pn = Patternode()
    seg = pn.post("/v1/segmentations", {"series": name, "profile": "standard@2026-11", "bars": bars,
                                        "return_edge": True})   # to carry on as a forming series later
    store = SegmentStore(Path("out") / "example-utility")         # your store, under your client's prefix
    store.apply_segmentation(name, seg)
    final = sum(not s["provisional"] for s in seg["segments"])
    print(f"{seg['series']}: {seg['bars']} bars -> {len(seg['segments'])} segments ({final} final), "
          f"{seg['depth']} levels; a 600 px chart draws {len(store.cut(name, bars[0][0], bars[-1][1], 600))}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "examples/data/export-kw.json")
