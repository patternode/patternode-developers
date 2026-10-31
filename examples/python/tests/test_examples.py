"""Every example runs against the mock. Run from the repo root:

    python -m unittest discover -s examples/python/tests -v
"""

import base64
import json
import os
import subprocess
import tempfile
import sys
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "examples" / "python"))
sys.path.insert(0, str(ROOT / "mock"))

import mock_patternode  # noqa: E402
from bars import bars_from_samples  # noqa: E402
from patternode_client import Patternode, PatternodeError  # noqa: E402
from webhook_receiver import InvalidSignature, verify  # noqa: E402

TEST_KEY = "pnk_test_" + "A" * 36
LIVE_KEY = "pnk_live_" + "B" * 36
ADMIN_KEY = "pnk_admin_" + "C" * 36
SECRET = "whsec_" + base64.b64encode(b"k" * 32).decode()


class WithMock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["PATTERNODE_MOCK_QUIET"] = "1"
        cls.srv = mock_patternode.serve(0)
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def run_example(self, name: str, key: str, args=None) -> str:
        env = {**os.environ, "PATTERNODE_API_KEY": key, "PATTERNODE_BASE_URL": self.base}
        script = ROOT / "examples" / name if "/" in name else ROOT / "examples" / "python" / name
        args = args if args is not None else [str(ROOT / "examples" / "data" / "export-kw.json")]
        with tempfile.TemporaryDirectory() as cwd:
            out = subprocess.run([sys.executable, str(script), *args], cwd=cwd, env=env,
                                 capture_output=True, text=True, timeout=120)
        self.assertEqual(out.returncode, 0, out.stderr)
        return out.stdout


class Examples(WithMock):
    def test_first_call_with_a_test_key(self):
        self.assertIn("segments", self.run_example("first_call.py", TEST_KEY))

    def test_finished_series(self):
        self.assertIn("chart draws", self.run_example("finished_series.py", LIVE_KEY))

    def test_forming_series(self):
        out = self.run_example("forming_series.py", LIVE_KEY)
        self.assertIn("closed h1@", out)
        self.assertIn("edge", out)

    def test_bulk_job(self):
        self.assertIn("succeeded:", self.run_example("bulk_job.py", LIVE_KEY))

    def test_utilities_historian(self):
        self.assertIn("segment closed", self.run_example("industries/utilities/historian_to_delve.py", LIVE_KEY, []))

    def test_finance_trades(self):
        self.assertIn("reproducible: True", self.run_example("industries/finance/trades_to_delve.py", LIVE_KEY, []))


class Store(WithMock):
    """The local segment store: the edge goes back with the next bars, and nothing is lost."""

    def test_the_store_carries_a_series_forward_from_its_edge(self):
        from segment_store import SegmentStore, StaleWrite
        pn = Patternode(LIVE_KEY, self.base)
        bars = json.loads((ROOT / "examples" / "data" / "export-kw.json").read_text())
        with tempfile.TemporaryDirectory() as d:
            store = SegmentStore(d)
            for b in bars:
                store.extend(pn, "s", [b], profile="standard@2026-11")
            whole = pn.post("/v1/segmentations", {"series": "s", "profile": "standard@2026-11", "bars": bars})
            self.assertEqual({x["id"] for x in store.segments("s")}, {x["id"] for x in whole["segments"]})
            edge = store.edge("s")
            self.assertEqual(edge.last_close_time, bars[-1][1])
            self.assertEqual([x["height"] for x in store.right_edge("s")], sorted({x["height"] for x in store.right_edge("s")}))
            self.assertLess(len(store.cut("s", bars[0][0], bars[-1][1], 30)),
                            len(store.cut("s", bars[0][0], bars[-1][1], 5000)))
            self.assertEqual(set(store.trend("s").values()) <= {"rising", "falling", "steady"}, True)
            with self.assertRaises(StaleWrite):  # a second writer with an old version loses
                store.apply_extension("s", pn.post("/v1/segmentations/extend", {
                    "series": "s", "edge": edge.token, "bars": [[bars[-1][1] + 1, bars[-1][1] + 9, 1, 2, 1, 2]]}),
                    expected_version=edge.version - 1)


class Webhooks(unittest.TestCase):
    def test_genuine_delivery_verifies(self):
        body = json.dumps({"type": "segmentation.job.succeeded", "data": {}}).encode()
        ts = int(time.time())
        sig = mock_patternode.sign(SECRET, "msg_1", ts, body)
        h = {"webhook-id": "msg_1", "webhook-timestamp": str(ts), "webhook-signature": "v1,stale " + sig}
        self.assertEqual(verify(SECRET, h, body)["type"], "segmentation.job.succeeded")

    def test_tampered_or_stale_delivery_fails(self):
        body, ts = b'{"type":"x"}', int(time.time())
        sig = mock_patternode.sign(SECRET, "msg_1", ts, body)
        with self.assertRaises(InvalidSignature):
            verify(SECRET, {"webhook-id": "msg_1", "webhook-timestamp": str(ts), "webhook-signature": sig},
                   b'{"type":"y"}')
        with self.assertRaises(InvalidSignature):
            verify(SECRET, {"webhook-id": "msg_1", "webhook-timestamp": str(ts - 600), "webhook-signature": sig}, body)


class Bars(unittest.TestCase):
    def test_gaps_and_flat_intervals_are_not_sent(self):
        samples = [(0, 5.0), (1000, 6.0), (2000, 5.5),          # a bar
                   (60_000, 4.0), (61_000, 4.0), (62_000, 4.0),  # flat: dropped
                   (300_000, 7.0)]                               # too few: dropped
        self.assertEqual(bars_from_samples(samples, 60_000), [[0, 2000, 5.0, 6.0, 5.0, 5.5]])

    def test_values_at_zero_need_an_offset(self):
        with self.assertRaises(ValueError):
            bars_from_samples([(0, -1.0), (1, 0.0), (2, 1.0)], 60_000)
        self.assertEqual(bars_from_samples([(0, -1.0), (1, 0.0), (2, 1.0)], 60_000, offset=10)[0][4], 9.0)


if __name__ == "__main__":
    unittest.main()
