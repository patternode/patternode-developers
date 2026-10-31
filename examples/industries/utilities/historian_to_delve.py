"""Utilities: a historian export into Delve, every tag, the way a monitoring product would.

    PATTERNODE_API_KEY=pnk_live_... python examples/industries/utilities/historian_to_delve.py

Reads an export of compressed historian points (tag, time, value, quality), as PI, eDNA,
Canary or a SCADA historian produce them. For each tag it:

1. Drops points whose quality is not GOOD (your historian's codes may differ).
2. Builds bars from the points the historian kept, as kept. It never interpolates onto a
   grid: a compressed archive's points already mark where the signal changed.
3. Names the series opaquely, from the site and the tag, with a salt only you hold.
4. Sends the last three days as a finished series, and stores the segments under the
   client's prefix.
5. Opens a forming stream per tag and appends new bars as they close, many tags a request.

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


def main(path: Path = HERE / "historian-export.csv") -> None:
    pn = Patternode()
    store = Path("out") / opaque(CLIENT)            # the client's prefix in your store
    store.mkdir(parents=True, exist_ok=True)
    streams = {}
    for tag, points in read_export(path).items():
        site, measure = tag.split(".", 1)
        name = f"{opaque(CLIENT, site)}/{opaque(measure)}"
        bars = bars_from_samples(points, BAR_MS, min_samples=2)
        history, live = bars[:-8], bars[-8:]      # pretend the last two hours are still arriving
        seg = pn.post("/v1/segmentations", {"series": name, "profile": PROFILE, "bars": history})
        (store / f"{name.replace('/', '_')}.json").write_text(json.dumps(seg["segments"]))
        print(f"{tag}: {len(points)} kept points -> {seg['bars']} bars -> {len(seg['segments'])} segments "
              f"({seg['profile_version']})")
        opened = pn.post("/v1/streams", {"series": name, "profile": PROFILE, "bar": live[0]})
        streams[tag] = {"id": opened["stream_id"], "sequence": 1, "pending": live[1:]}

    # As each 15 minutes closes, one request carries the new bar of every tag.
    while any(s["pending"] for s in streams.values()):
        batch, tags = [], []
        for tag, s in streams.items():
            if s["pending"]:
                batch.append({"stream_id": s["id"], "sequence": s["sequence"] + 1, "bar": s["pending"].pop(0)})
                tags.append(tag)
        results = pn.post("/v1/streams/observations", {"observations": batch})["results"]
        for tag, item, r in zip(tags, batch, results):
            if r["status"] != 200:
                raise SystemExit(f"{tag}: {r['error']['error']['details']['error_code']}")
            streams[tag]["sequence"] = item["sequence"]
            for ev in r["result"]["events"]:
                if ev["kind"] == "segmented":
                    print(f"{tag}: level {ev['level'] + 1} segment closed at {ev['node']['close_time']}")
    for s in streams.values():
        pn.delete(f"/v1/streams/{s['id']}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "historian-export.csv")
