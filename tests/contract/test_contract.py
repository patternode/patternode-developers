"""The contract, as tests. Every implementation of the Patternode API must pass them.

    python -m unittest discover -s tests/contract -v                     # against the mock, started here
    PATTERNODE_BASE_URL=https://staging.api.patternode.com \\
    PATTERNODE_API_KEY=pnk_live_... python -m unittest discover -s tests/contract -v   # against a deployment

They test behaviour the contract promises (shapes, errors, determinism, that extending in
pieces equals segmenting the whole, that the edge is sealed), never the values of segments,
which only the real engine decides. Tests that need an admin key or your own storage run
only against the mock, or when PATTERNODE_ADMIN_KEY and PATTERNODE_BUCKET_URL are set.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "examples" / "python"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from patternode_client import Patternode, PatternodeError  # noqa: E402
from schema import errors, load  # noqa: E402

BARS = json.loads((ROOT / "examples" / "data" / "export-kw.json").read_text())
SEGMENT = load("segment-box.schema.json")
ERROR = load("error.schema.json")
REMOTE = bool(os.environ.get("PATTERNODE_BASE_URL")) and os.environ.get("PATTERNODE_CONTRACT_MOCK") != "1"


def setUpModule():
    global BASE, LIVE, TEST, ADMIN, BUCKET, _srv
    if REMOTE:
        BASE = os.environ["PATTERNODE_BASE_URL"].rstrip("/")
        LIVE = os.environ["PATTERNODE_API_KEY"]
        TEST = os.environ.get("PATTERNODE_TEST_KEY")
        ADMIN = os.environ.get("PATTERNODE_ADMIN_KEY")
        BUCKET = os.environ.get("PATTERNODE_BUCKET_URL")
        _srv = None
    else:
        sys.path.insert(0, str(ROOT / "mock"))
        import mock_patternode
        os.environ["PATTERNODE_MOCK_QUIET"] = "1"
        _srv = mock_patternode.serve(0)
        threading.Thread(target=_srv.serve_forever, daemon=True).start()
        BASE = f"http://127.0.0.1:{_srv.server_address[1]}"
        LIVE, TEST, ADMIN = "pnk_live_" + "B" * 36, "pnk_test_" + "A" * 36, "pnk_admin_" + "C" * 36
        BUCKET = BASE + "/_bucket"


def tearDownModule():
    if _srv:
        _srv.shutdown()


def raw(method: str, path: str, body: bytes | None, headers: dict) -> tuple[int, dict]:
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        text = e.read()
        try:
            return e.code, json.loads(text or b"{}")
        except json.JSONDecodeError:
            return e.code, {}


class Contract(unittest.TestCase):
    def setUp(self):
        self.pn = Patternode(LIVE, BASE, max_retries=2)
        self.series = f"contract/{self.id().rsplit('.', 1)[-1]}/{time.time_ns()}"

    def assertSchema(self, value, schema):
        self.assertEqual(errors(value, schema), [])

    def assertCode(self, call, status: int, code: str):
        with self.assertRaises(PatternodeError) as e:
            call()
        self.assertEqual((e.exception.status, e.exception.code), (status, code))

    # The door -------------------------------------------------------------------------

    def test_whoami(self):
        me = self.pn.get("/v1/whoami")
        self.assertEqual(me["object"], "key")
        self.assertIn(me["kind"], ("live", "test", "admin"))

    def test_no_key_is_401(self):
        status, body = raw("GET", "/v1/whoami", None, {})
        self.assertEqual(status, 401)

    def test_a_write_needs_the_body_hash(self):
        body = json.dumps({"demo": "walk"}).encode()
        status, _ = raw("POST", "/v1/segmentations", body,
                        {"authorization": f"Bearer {LIVE}", "content-type": "application/json"})
        self.assertEqual(status, 400)
        status, _ = raw("POST", "/v1/segmentations", body,
                        {"authorization": f"Bearer {LIVE}", "content-type": "application/json",
                         "x-amz-content-sha256": hashlib.sha256(b"other").hexdigest()})
        self.assertEqual(status, 403)

    @unittest.skipUnless(REMOTE is False or os.environ.get("PATTERNODE_TEST_KEY"), "needs a test key")
    def test_a_test_key_runs_only_demonstrations(self):
        pn = Patternode(TEST, BASE)
        self.assertEqual(pn.post("/v1/segmentations", {"demo": "walk"})["object"], "segmentation")
        self.assertCode(lambda: pn.post("/v1/segmentations", {"series": self.series, "bars": BARS[:4]}),
                        403, "test_key_demo_only")

    def test_errors_have_the_error_shape(self):
        with self.assertRaises(PatternodeError) as e:
            self.pn.post("/v1/segmentations", {"series": self.series, "bars": [BARS[1], BARS[0]]})
        self.assertEqual(e.exception.code, "invalid_series")
        self.assertEqual(e.exception.problems[0]["problem"], "times_not_increasing")
        self.assertEqual(e.exception.problems[0]["index"], 1)

    def test_an_idempotency_key_reused_with_another_body_is_422(self):
        self.pn.post("/v1/segmentations", {"series": self.series, "bars": BARS[:8]}, idempotency_key=self.series)
        self.assertCode(lambda: self.pn.post("/v1/segmentations", {"series": self.series, "bars": BARS[:9]},
                                             idempotency_key=self.series), 422, "idempotency_conflict")

    # Finished series ------------------------------------------------------------------

    def test_a_finished_series_returns_a_tree_of_segment_boxes(self):
        r = self.pn.post("/v1/segmentations", {"series": self.series, "profile": "standard", "bars": BARS})
        self.assertEqual(r["object"], "segmentation")
        self.assertRegex(r["profile_version"], r"^standard@\d{4}-\d{2}$")
        ids = {s["id"] for s in r["segments"]}
        self.assertEqual(len(ids), len(r["segments"]), "ids are unique")
        for s in r["segments"]:
            self.assertSchema(s, SEGMENT)
            self.assertTrue(s["parent"] is None or s["parent"] in ids, f"{s['id']} has a parent in the tree")
        provisional = [s["height"] for s in r["segments"] if s["provisional"]]
        self.assertEqual(sorted(provisional), sorted(set(provisional)), "one open segment per level")
        self.assertEqual(r["depth"], max(s["height"] for s in r["segments"]))

    def test_the_same_bars_and_version_give_the_same_segments(self):
        body = {"series": self.series, "profile": "standard@2026-11", "bars": BARS}
        self.assertEqual(self.pn.post("/v1/segmentations", body)["segments"],
                         self.pn.post("/v1/segmentations", body)["segments"])

    def test_nanosecond_times_come_back_as_strings_untouched(self):
        t = 1730246400000000000
        bars = [[str(t + i * 10**9), str(t + i * 10**9 + 999_999_999), 1, 2, 1, 2] for i in range(12)]
        r = self.pn.post("/v1/segmentations", {"series": self.series, "time_unit": "ns", "bars": bars})
        opens = {s["open_time"] for s in r["segments"]}
        self.assertIn(str(t), opens)
        self.assertTrue(all(isinstance(s["open_time"], str) for s in r["segments"]))

    # Forming series: the edge ---------------------------------------------------------

    def extend(self, bars, edge=None, series=None, **extra):
        body = {"series": series or self.series, "profile": "standard@2026-11", "bars": bars, **extra}
        if edge:
            body["edge"] = edge
        return self.pn.post("/v1/segmentations/extend", body)

    def test_extending_in_pieces_equals_segmenting_the_whole(self):
        whole = {s["id"]: s for s in self.pn.post("/v1/segmentations", {
            "series": self.series, "profile": "standard@2026-11", "bars": BARS})["segments"]}
        for size in (1, 5, 17):
            edge, final, last = None, {}, None
            for i in range(0, len(BARS), size):
                last = self.extend(BARS[i:i + size], edge)
                self.assertEqual(last["object"], "extension")
                for s in last["closed"]:
                    self.assertFalse(s["provisional"])
                    self.assertSchema(s, SEGMENT)
                final.update({s["id"]: s for s in last["closed"]})
                edge = last["edge"]
            self.assertEqual({**final, **{s["id"]: s for s in last["right_edge"]}}, whole, f"pieces of {size}")

    def test_a_finished_series_can_carry_on_from_its_edge(self):
        head = self.pn.post("/v1/segmentations", {"series": self.series, "profile": "standard@2026-11",
                                                  "bars": BARS[:30], "return_edge": True})
        self.assertTrue(head["edge"].startswith("pne1."))
        tail = self.extend(BARS[30:], head["edge"])
        whole = self.pn.post("/v1/segmentations", {"series": self.series, "profile": "standard@2026-11", "bars": BARS})
        closed_ids = {s["id"] for s in head["segments"] if not s["provisional"]} | {s["id"] for s in tail["closed"]}
        right_ids = {s["id"] for s in tail["right_edge"]}
        self.assertEqual(closed_ids | right_ids, {s["id"] for s in whole["segments"]})

    def test_a_retry_with_the_same_edge_gives_the_same_answer(self):
        first = self.extend(BARS[:10])
        a = self.extend(BARS[10:12], first["edge"])
        b = self.extend(BARS[10:12], first["edge"])
        self.assertEqual((a["closed"], a["right_edge"], a["edge"]), (b["closed"], b["right_edge"], b["edge"]))

    def test_a_bar_before_the_edge_is_out_of_order(self):
        first = self.extend(BARS[:10])
        self.assertEqual(first["edge_last_close_time"], BARS[9][1])
        self.assertCode(lambda: self.extend(BARS[5:6], first["edge"]), 409, "out_of_order")

    def test_an_edge_belongs_to_one_series(self):
        first = self.extend(BARS[:10])
        self.assertCode(lambda: self.extend(BARS[10:11], first["edge"], series=self.series + "/other"),
                        409, "edge_mismatch")

    def test_a_changed_edge_is_refused(self):
        edge = self.extend(BARS[:10])["edge"]
        head, tail = edge[:-6], edge[-6:]
        tampered = head + ("A" if tail[0] != "A" else "B") + tail[1:]
        self.assertCode(lambda: self.extend(BARS[10:11], tampered), 400, "edge_invalid")

    def test_a_batch_answers_each_item(self):
        a = self.extend(BARS[:10])
        r = self.pn.post("/v1/segmentations/extend/batch", {"items": [
            {"series": self.series, "edge": a["edge"], "bars": BARS[10:11]},
            {"series": self.series, "edge": a["edge"], "bars": BARS[2:3]}]})
        self.assertEqual([x["status"] for x in r["results"]], [200, 409])
        self.assertSchema(r["results"][1]["error"], ERROR)

    # Jobs: your storage in, your storage out --------------------------------------------

    @unittest.skipUnless(not REMOTE or os.environ.get("PATTERNODE_BUCKET_URL"), "needs storage links")
    def test_a_job_reads_your_file_and_writes_your_result(self):
        key = self.series.replace("/", "_")
        urllib.request.urlopen(urllib.request.Request(f"{BUCKET}/in/{key}.jsonl", method="PUT",
                                                      data="\n".join(json.dumps(b) for b in BARS).encode())).read()
        job = self.pn.post("/v1/segmentations/jobs", {
            "series": self.series, "kind": "bars", "format": "jsonl", "profile": "standard@2026-11",
            "source_url": f"{BUCKET}/in/{key}.jsonl", "result_url": f"{BUCKET}/out/{key}.json"})
        self.assertIn(job["status"], ("queued", "running"))
        for _ in range(120):
            job = self.pn.get(f"/v1/segmentations/jobs/{job['id']}")
            if job["status"] in ("succeeded", "failed"):
                break
            time.sleep(0.5)
        self.assertEqual(job["status"], "succeeded")
        self.assertTrue(job["result_written"])
        self.assertNotIn("result_url", job, "the job record holds no link to a result Patternode keeps")
        result = json.loads(urllib.request.urlopen(f"{BUCKET}/out/{key}.json").read())
        whole = self.pn.post("/v1/segmentations", {"series": self.series, "profile": "standard@2026-11", "bars": BARS})
        self.assertEqual(result["segments"], whole["segments"])

    # Keys ------------------------------------------------------------------------------

    @unittest.skipUnless(not REMOTE or os.environ.get("PATTERNODE_ADMIN_KEY"), "needs an admin key")
    def test_an_admin_key_makes_keys_and_runs_nothing(self):
        admin = Patternode(ADMIN, BASE)
        k = admin.post("/v1/keys", {"kind": "live", "name": "contract", "scopes": "read-only", "expires_in_days": 1})
        self.assertRegex(k["key"], r"^pnk_live_[0-9A-Za-z]{36}$")
        self.assertCode(lambda: admin.post("/v1/segmentations", {"demo": "walk"}), 403, "missing_scope")
        admin.delete(f"/v1/keys/{k['id']}")


if __name__ == "__main__":
    unittest.main()
