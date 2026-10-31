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
        self.assertIn("levels; stored", self.run_example("finished_series.py", LIVE_KEY))

    def test_forming_series(self):
        out = self.run_example("forming_series.py", LIVE_KEY)
        self.assertIn("closed h1@", out)

    def test_bulk_job(self):
        self.assertIn("succeeded:", self.run_example("bulk_job.py", LIVE_KEY))

    def test_utilities_historian(self):
        self.assertIn("segment closed", self.run_example("industries/utilities/historian_to_delve.py", LIVE_KEY, []))

    def test_finance_trades(self):
        self.assertIn("reproducible: True", self.run_example("industries/finance/trades_to_delve.py", LIVE_KEY, []))


class Contract(WithMock):
    def test_test_key_cannot_run_real_data(self):
        pn = Patternode(TEST_KEY, self.base)
        with self.assertRaises(PatternodeError) as e:
            pn.post("/v1/segmentations", {"series": "x", "bars": [[1, 2, 1, 1, 1, 1], [3, 4, 1, 1, 1, 1]]})
        self.assertEqual(e.exception.code, "test_key_demo_only")

    def test_bad_series_lists_problems(self):
        pn = Patternode(LIVE_KEY, self.base)
        with self.assertRaises(PatternodeError) as e:
            pn.post("/v1/segmentations", {"series": "x", "bars": [[5, 6, 1, 1, 1, 1], [3, 4, 1, 1, 1, 1]]})
        self.assertEqual(e.exception.code, "invalid_series")
        self.assertEqual(e.exception.problems[0]["problem"], "times_not_increasing")

    def test_out_of_order_leaves_stream_unchanged(self):
        pn = Patternode(LIVE_KEY, self.base)
        s = pn.post("/v1/streams", {"series": "x", "bar": [10, 20, 1, 2, 1, 2]})
        with self.assertRaises(PatternodeError) as e:
            pn.post(f"/v1/streams/{s['stream_id']}/observations", {"sequence": 2, "bar": [5, 8, 1, 2, 1, 2]})
        self.assertEqual(e.exception.code, "out_of_order")
        self.assertEqual(pn.get(f"/v1/streams/{s['stream_id']}")["bars"], 1)

    def test_sequence_makes_appends_exactly_once(self):
        pn = Patternode(LIVE_KEY, self.base)
        s = pn.post("/v1/streams", {"series": "x", "bar": [10, 20, 1, 2, 1, 2]})
        path = f"/v1/streams/{s['stream_id']}/observations"
        first = pn.post(path, {"sequence": 2, "bar": [30, 40, 1, 2, 1, 2]})
        again = pn.post(path, {"sequence": 2, "bar": [30, 40, 1, 2, 1, 2]})
        self.assertEqual(first, again)
        with self.assertRaises(PatternodeError) as e:
            pn.post(path, {"sequence": 4, "bar": [50, 60, 1, 2, 1, 2]})
        self.assertEqual((e.exception.code, e.exception.status), ("sequence_gap", 409))
        self.assertEqual(pn.get(f"/v1/streams/{s['stream_id']}")["last_sequence"], 2)

    def test_batch_appends_answer_each_item(self):
        pn = Patternode(LIVE_KEY, self.base)
        a = pn.post("/v1/streams", {"series": "a", "bar": [10, 20, 1, 2, 1, 2]})["stream_id"]
        b = pn.post("/v1/streams", {"series": "b", "bar": [10, 20, 1, 2, 1, 2]})["stream_id"]
        r = pn.post("/v1/streams/observations", {"observations": [
            {"stream_id": a, "sequence": 2, "bar": [30, 40, 1, 2, 1, 2]},
            {"stream_id": b, "sequence": 5, "bar": [30, 40, 1, 2, 1, 2]}]})
        self.assertEqual([x["status"] for x in r["results"]], [200, 409])

    def test_nanosecond_times_round_trip_as_strings(self):
        pn = Patternode(LIVE_KEY, self.base)
        t = 1730246400000000000
        bars = [[str(t + i * 10**9), str(t + i * 10**9 + 999_999_999), 1, 2, 1, 2] for i in range(8)]
        r = pn.post("/v1/segmentations", {"series": "ns", "time_unit": "ns", "bars": bars})
        self.assertEqual(r["segments"][0]["open_time"], str(t))
        self.assertTrue(r["profile_version"].startswith("standard@"))

    def test_idempotent_retry_returns_the_first_answer(self):
        pn = Patternode(LIVE_KEY, self.base)
        a = pn.post("/v1/segmentations", {"demo": "walk"}, idempotency_key="same")
        b = pn.post("/v1/segmentations", {"demo": "walk"}, idempotency_key="same")
        self.assertEqual(a["id"], b["id"])

    def test_admin_key_rotates_itself_out(self):
        pn = Patternode(ADMIN_KEY, self.base)
        new = pn.post("/v1/keys", {"kind": "admin", "name": "ops"})
        self.assertRegex(new["key"], r"^pnk_admin_[0-9A-Za-z]{36}$")
        live = Patternode(new["key"], self.base).post("/v1/keys", {"kind": "live", "scopes": "full"})
        self.assertTrue(live["key"].startswith("pnk_live_"))


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
