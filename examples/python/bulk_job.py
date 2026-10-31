"""Pattern 3, a backfill: upload a large file, run it as a job, take the result by webhook or poll.

    PATTERNODE_API_KEY=pnk_live_... python examples/python/bulk_job.py examples/data/export-kw.json
"""

import json
import sys
import time
import urllib.request
import uuid
from pathlib import Path

from patternode_client import Patternode


def upload(slot: dict, data: bytes, filename: str) -> None:
    """POST the file to the presigned form: its fields first, unchanged, then the file."""
    boundary = uuid.uuid4().hex
    parts = [f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
             for k, v in slot["fields"].items()]
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                 f"Content-Type: application/octet-stream\r\n\r\n".encode() + data + b"\r\n")
    body = b"".join(parts) + f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(slot["url"], data=body, method="POST",
                                 headers={"content-type": f"multipart/form-data; boundary={boundary}"})
    urllib.request.urlopen(req, timeout=300).read()


def main(path: str) -> None:
    bars = json.loads(Path(path).read_text())
    data = "\n".join(json.dumps(b) for b in bars).encode()  # JSON Lines, one bar a line
    pn = Patternode()
    slot = pn.post("/v1/uploads", {"format": "jsonl", "size_bytes": len(data)})
    upload(slot, data, "bars.jsonl")
    job = pn.post("/v1/segmentations/jobs",
                  {"upload_id": slot["id"], "kind": "bars", "series": "exu/demo/backfill/ac-power"})
    print(f"job {job['id']} {job['status']}")
    # In production, let segmentation.job.succeeded reach your webhook instead of polling.
    while job["status"] in ("queued", "running"):
        time.sleep(1)
        job = pn.get(f"/v1/segmentations/jobs/{job['id']}")
    if job["status"] == "failed":
        raise SystemExit(f"failed, not charged: {job['error']}")
    # result_url is a signed link, valid 24 hours: no key needed, so do not send one.
    with urllib.request.urlopen(job["result_url"], timeout=60) as r:
        result = json.loads(r.read())
    print(f"succeeded: {len(result['segments'])} segments, {job['usage']['samples_billed']} samples billed")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "examples/data/export-kw.json")
