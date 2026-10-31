"""Your segment store: keep what Patternode returns, query it, and carry forming series forward.

Patternode keeps none of your series. Everything about a series lives here, on your side:
its segments at every level, and for a forming series its edge (the sealed token Patternode
needs to carry on). This module is the reference for that store. It keeps one JSON file per
series under a directory, written atomically; swap the two private methods for your own
database or object store and keep the rest.

    from patternode_client import Patternode
    from segment_store import SegmentStore

    store = SegmentStore("store/exampleco")                 # one directory per client: the prefix
    pn = Patternode()
    store.extend(pn, "exu/7f3a/1b02/export-kw", new_bars)   # edge + new bars -> new results, stored
    store.right_edge("exu/7f3a/1b02/export-kw")             # the open segment at each level
    store.edge("exu/7f3a/1b02/export-kw")                   # what Patternode needs next time
    store.cut("exu/7f3a/1b02/export-kw", start, end, width_px=600)   # what a chart should draw

Standard library only. Times are whatever unit you send (epoch milliseconds by default).
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Edge:
    token: str               # sealed by Patternode; store it and send it back unchanged
    last_close_time: int     # the next bars must open after this
    profile_version: str     # pinned for the life of the series
    version: int             # this store's write counter, for one writer at a time


class StaleWrite(Exception):
    """Another writer extended the series first. Re-read the edge and retry."""


class SegmentStore:
    def __init__(self, root: str | os.PathLike):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    # The one workflow: edge + new bars -> new results ---------------------------------

    def extend(self, pn, series: str, bars: list, profile: str = "standard") -> dict:
        """Send the stored edge with the new bars, then store what comes back.

        Safe to retry: the same edge with the same bars always gives the same answer. Two
        writers on one series cannot both win: the second gets StaleWrite.
        """
        edge = self.edge(series)
        body = {"series": series, "bars": bars}
        if edge:
            body["edge"] = edge.token
            body["profile"] = edge.profile_version
        else:
            body["profile"] = profile
        result = pn.post("/v1/segmentations/extend", body)
        self.apply_extension(series, result, expected_version=edge.version if edge else 0)
        return result

    # Writing ----------------------------------------------------------------------------

    def apply_segmentation(self, series: str, result: dict) -> None:
        """Store a finished series' answer: every segment, and its edge if it was asked for."""
        doc = {"series": series, "version": self._read(series).get("version", 0) + 1,
               "profile_version": result["profile_version"],
               "segments": {s["id"]: s for s in result["segments"]}}
        if result.get("edge"):
            doc["edge"] = result["edge"]
            doc["edge_last_close_time"] = result["edge_last_close_time"]
        self._write(series, doc)

    def apply_extension(self, series: str, result: dict, expected_version: int | None = None) -> None:
        """Store an extension: closed segments are final, the right edge replaces the old one,
        and the new edge replaces the old edge, all in one write."""
        doc = self._read(series)
        if expected_version is not None and doc.get("version", 0) != expected_version:
            raise StaleWrite(series)
        segments = {k: v for k, v in doc.get("segments", {}).items() if not v["provisional"]}
        for s in result["closed"] + result["right_edge"]:
            segments[s["id"]] = s
        self._write(series, {"series": series, "version": doc.get("version", 0) + 1,
                             "profile_version": result["profile_version"], "segments": segments,
                             "edge": result["edge"], "edge_last_close_time": result["edge_last_close_time"]})

    # Reading ----------------------------------------------------------------------------

    def edge(self, series: str) -> Edge | None:
        doc = self._read(series)
        if not doc.get("edge"):
            return None
        return Edge(doc["edge"], doc["edge_last_close_time"], doc["profile_version"], doc["version"])

    def right_edge(self, series: str) -> list[dict]:
        """The open segment at each level, bottom up. Provisional: they may still grow."""
        return sorted((s for s in self._segments(series) if s["provisional"]), key=lambda s: s["height"])

    def levels(self, series: str) -> list[int]:
        return sorted({s["height"] for s in self._segments(series)})

    def segments(self, series: str, level: int | None = None, start=None, end=None,
                 final_only: bool = False) -> list[dict]:
        """Segments by level and time window, in time order. A segment is in the window if it overlaps it."""
        out = []
        for s in self._segments(series):
            if level is not None and s["height"] != level:
                continue
            if final_only and s["provisional"]:
                continue
            if start is not None and _t(s["close_time"]) < _t(start):
                continue
            if end is not None and _t(s["open_time"]) > _t(end):
                continue
            out.append(s)
        return sorted(out, key=lambda s: (s["height"], _t(s["open_time"])))

    def cut(self, series: str, start, end, width_px: int, min_px: float = 6.0) -> list[dict]:
        """What a chart of width_px pixels over [start, end] should draw: the finest level whose
        segments are, at the median, at least min_px wide. Zoom in and finer levels take over."""
        span = max(_t(end) - _t(start), 1)
        for level in self.levels(series):
            segs = self.segments(series, level, start, end)
            if not segs:
                continue
            widths = sorted((_t(s["close_time"]) - _t(s["open_time"])) / span * width_px for s in segs)
            if widths[len(widths) // 2] >= min_px:
                return segs
        top = self.levels(series)
        return self.segments(series, top[-1], start, end) if top else []

    def trend(self, series: str, levels=(1, 2, 3), steady: float = 0.001) -> dict[int, str]:
        """Rising, falling or steady at each timescale: the open segment at each level."""
        out = {}
        for s in self.right_edge(series):
            if s["height"] in levels:
                change = (s["close"] - s["open"]) / abs(s["open"]) if s["open"] else 0.0
                out[s["height"]] = "steady" if abs(change) < steady else "rising" if change > 0 else "falling"
        return out

    def delete(self, series: str) -> None:
        self._path(series).unlink(missing_ok=True)

    # Storage: replace these two with your database or object store -----------------------

    def _read(self, series: str) -> dict:
        path = self._path(series)
        return json.loads(path.read_text()) if path.exists() else {}

    def _write(self, series: str, doc: dict) -> None:
        path = self._path(series)
        fd, tmp = tempfile.mkstemp(dir=self.root, suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump(doc, f)
        os.replace(tmp, path)  # atomic: segments and edge change together, or not at all

    def _path(self, series: str) -> Path:
        return self.root / (series.replace("/", "__") + ".json")

    def _segments(self, series: str) -> list[dict]:
        return list(self._read(series).get("segments", {}).values())


def _t(v) -> int:
    return int(v)  # us and ns times arrive as strings
