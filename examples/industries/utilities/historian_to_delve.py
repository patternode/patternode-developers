"""Utilities: a historian export into Delve, every tag, the way a monitoring product would.

    PATTERNODE_API_KEY=pnk_live_... python examples/industries/utilities/historian_to_delve.py

Reads an export of compressed historian points (tag, time, value, quality), as PI, eDNA,
Canary or a SCADA historian produce them. For each tag it:

1. Drops points whose quality is not GOOD (your historian's codes may differ).
2. Builds bars from the points the historian kept, as kept. It never interpolates onto a
   grid: a compressed archive's points already mark where the signal changed.
3. Names the series opaquely, from the site and the tag, with a salt only you hold.
4. Sends the history as a finished series, asking for its edge, and keeps both in the
   segment store under the client's prefix. Patternode keeps nothing.
5. As each interval closes, extends every tag in one request: each item carries that tag's
   stored edge and its new bar, and each answer's new edge goes back in the store.

The data is invented: a zone substation transformer's top-oil temperature and load.
"""

import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "python"))

from bars import bars_from_samples  # noqa: E402
from patternode_client import Patternode  # noqa: E402
from segment_store import SegmentStore  # noqa: E402

CLIENT = "example-utility"           # your client, never sent
SALT = "per-environment-secret"       # from your secret store in production
BAR_MS = 15 * 60 * 1000               # 15-minute bars: a substation's view in hours to weeks
PROFILE = "standard@2026-11"          # pinned, so an audit can reproduce every segment


def opaque(*parts: str) -> str:
    return "/".join(hashlib.sha256((SALT + p).encode()).hexdigest()[:12] for p in parts)


def read_export(path: Path) -> dict[str, list[tuple[int, float]]]:
    points = defaultdict(list)
    with path.open() as f:
        for row in csv.DictReader(f):
            if row["quality"] == "GOOD":
                points[row["tag"]].append((int(row["time_ms"]), float(row["value"])))
    return points


def main(path: Path = HERE / "historian-export.csv", store_root: Path = Path("out")) -> None:
    pn = Patternode()
    store = SegmentStore(store_root / opaque(CLIENT))   # the client's prefix in your store
    pending = {}
    for tag, points in read_export(path).items():
        site, measure = tag.split(".", 1)
        name = f"{opaque(CLIENT, site)}/{opaque(measure)}"
        bars = bars_from_samples(points, BAR_MS, min_samples=2)
        history, live = bars[:-8], bars[-8:]      # pretend the last two hours are still arriving
        seg = pn.post("/v1/segmentations", {"series": name, "profile": PROFILE, "bars": history, "return_edge": True})
        store.apply_segmentation(name, seg)
        print(f"{tag}: {len(points)} kept points -> {seg['bars']} bars -> {len(seg['segments'])} segments "
              f"({seg['profile_version']})")
        pending[tag] = (name, live)

    # As each 15 minutes closes, one request extends every tag from its stored edge.
    for i in range(8):
        items, tags = [], []
        for tag, (name, live) in pending.items():
            edge = store.edge(name)
            items.append({"series": name, "profile": edge.profile_version, "edge": edge.token, "bars": [live[i]]})
            tags.append((tag, name, edge.version))
        results = pn.post("/v1/segmentations/extend/batch", {"items": items})["results"]
        for (tag, name, version), r in zip(tags, results):
            if r["status"] != 200:
                raise SystemExit(f"{tag}: {r['error']['error']['details']['error_code']}")
            store.apply_extension(name, r["result"], expected_version=version)
            for s in r["result"]["closed"]:
                print(f"{tag}: level {s['height']} segment closed at {s['close_time']}")
    for tag, (name, _) in pending.items():
        print(f"{tag}: trend {store.trend(name)}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "historian-export.csv")
