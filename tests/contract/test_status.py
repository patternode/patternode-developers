"""The status page's API (specs/status.yaml), as tests. No key.

    python -m unittest discover -s tests/contract -v                       # against the mock
    PATTERNODE_STATUS_URL=https://status.patternode.com python -m unittest discover -s tests/contract -v

Against a deployment of the API (PATTERNODE_BASE_URL) these tests run only when
PATTERNODE_STATUS_URL is set too, since the status page is served apart from the API.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REMOTE = bool(os.environ.get("PATTERNODE_BASE_URL")) and os.environ.get("PATTERNODE_CONTRACT_MOCK") != "1"
INDICATORS = ("none", "minor", "major", "critical", "maintenance")
STATUSES = ("operational", "degraded_performance", "partial_outage", "major_outage", "under_maintenance",
            "not_in_service")
INCIDENT_STATUSES = ("investigating", "identified", "monitoring", "resolved", "scheduled", "in_progress",
                     "verifying", "completed")
FILES = ("status.json", "summary.json", "components.json", "incidents.json", "incidents/unresolved.json",
         "scheduled-maintenances.json")
STATUS_URL = os.environ.get("PATTERNODE_STATUS_URL", "").rstrip("/")
_srv = None


def setUpModule():
    global STATUS_URL, _srv
    if STATUS_URL or REMOTE:
        return
    sys.path.insert(0, str(ROOT / "mock"))
    import mock_patternode
    os.environ["PATTERNODE_MOCK_QUIET"] = "1"
    _srv = mock_patternode.serve(0)
    threading.Thread(target=_srv.serve_forever, daemon=True).start()
    STATUS_URL = f"http://127.0.0.1:{_srv.server_address[1]}"


def tearDownModule():
    if _srv:
        _srv.shutdown()


def fetch(name: str) -> tuple[int, dict]:
    req = urllib.request.Request(f"{STATUS_URL}/api/v2/{name}")   # no key, on purpose
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {}


@unittest.skipUnless(STATUS_URL or not REMOTE, "set PATTERNODE_STATUS_URL to test a deployed status page")
class Status(unittest.TestCase):
    def test_every_file_answers_without_a_key(self):
        for name in FILES:
            status, body = fetch(name)
            self.assertEqual(status, 200, name)
            self.assertTrue(body["page"]["updated_at"], name)

    def test_the_indicator_is_one_of_the_five(self):
        self.assertIn(fetch("status.json")[1]["status"]["indicator"], INDICATORS)

    def test_components_have_stable_ids_known_statuses_and_whole_groups(self):
        comps = fetch("components.json")[1]["components"]
        ids = {c["id"] for c in comps}
        self.assertEqual(len(ids), len(comps), "ids are unique")
        for c in comps:
            self.assertIn(c["status"], STATUSES, c["id"])
            self.assertTrue(c["group_id"] is None or c["group_id"] in ids, c["id"])
            if c["group"]:
                self.assertTrue(set(c["components"]) <= ids, c["id"])

    def test_delve_is_listed(self):
        self.assertIn("delve", {c["id"] for c in fetch("components.json")[1]["components"]})

    def test_a_component_not_in_service_counts_for_nothing(self):
        comps = fetch("components.json")[1]["components"]
        for c in comps:
            if c["status"] == "not_in_service":
                self.assertNotIn("uptime", c, c["id"])
        if all(c["status"] in ("operational", "not_in_service") for c in comps):
            self.assertEqual(fetch("status.json")[1]["status"]["indicator"], "none")

    def test_unresolved_incidents_are_not_resolved(self):
        for i in fetch("incidents/unresolved.json")[1]["incidents"]:
            self.assertIn(i["status"], INCIDENT_STATUSES)
            self.assertNotIn(i["status"], ("resolved", "completed"))
            self.assertTrue(i["shortlink"].startswith(("https://", STATUS_URL)))

    def test_uptime_has_at_most_90_days(self):
        comp = next(c for c in fetch("components.json")[1]["components"] if not c["group"])
        status, body = fetch(f"uptime/{comp['id']}.json")
        self.assertEqual(status, 200)
        self.assertLessEqual(len(body["days"]), 90)
        self.assertEqual(fetch("uptime/no-such-component.json")[0], 404)


if __name__ == "__main__":
    unittest.main()
