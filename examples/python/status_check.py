"""Before you alarm on Patternode, ask its status page. Standard library only.

A failed call (5xx, a timeout, overloaded_error) is either Patternode or your side: your
network, your proxy, a bad deploy of your own. The status page is served apart from the API,
so it answers when the API does not, and it says which.

    python examples/python/status_check.py                 # reads status.patternode.com
    PATTERNODE_STATUS_URL=http://localhost:4010 python examples/python/status_check.py
"""

from __future__ import annotations

import json
import os
import urllib.request

STATUS_URL = os.environ.get("PATTERNODE_STATUS_URL", "https://status.patternode.com").rstrip("/")


def status(url: str = STATUS_URL) -> dict:
    """The overall indicator: none, minor, major, critical or maintenance. No key."""
    with urllib.request.urlopen(f"{url}/api/v2/status.json", timeout=10) as r:
        return json.loads(r.read())["status"]


def open_incidents(url: str = STATUS_URL, components: set[str] | None = None) -> list[dict]:
    """Unresolved incidents, only those touching `components` (ids) if given."""
    with urllib.request.urlopen(f"{url}/api/v2/incidents/unresolved.json", timeout=10) as r:
        incidents = json.loads(r.read())["incidents"]
    if components is None:
        return incidents
    return [i for i in incidents if components & {c["id"] for c in i["components"]}]


def who_to_page(url: str = STATUS_URL, components: set[str] | None = None) -> str:
    """After your calls to Patternode fail: 'patternode' when it has an open incident on the
    components you use (watch it, do not page your own on-call), 'us' when it says all is well
    (look at your side first), 'unknown' when the status page cannot be reached either."""
    try:
        if open_incidents(url, components):
            return "patternode"
        return "patternode" if status(url)["indicator"] in ("major", "critical") else "us"
    except OSError:
        return "unknown"


if __name__ == "__main__":
    print(status()["description"], "|", who_to_page(components={"delve-segmentation", "delve-extend"}))
