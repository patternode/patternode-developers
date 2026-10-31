"""Pattern 3, a backfill: a job reads your file from your storage and writes the result back to it.

    PATTERNODE_API_KEY=pnk_live_... python examples/python/bulk_job.py examples/data/export-kw.json

Patternode keeps nothing: give it a link to read the file from and a link to write the result
to, both presigned in your own storage. With S3, for example:

    s3 = boto3.client("s3")
    source_url = s3.generate_presigned_url("get_object", Params={"Bucket": b, "Key": "in/x.parquet"}, ExpiresIn=3600)
    result_url = s3.generate_presigned_url("put_object", Params={"Bucket": b, "Key": "out/x.json"}, ExpiresIn=3600)

Against the mock, its stand-in for your storage at /_bucket/ plays that part.
"""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

from patternode_client import Patternode


def main(path: str) -> None:
    bars = json.loads(Path(path).read_text())
    pn = Patternode()
    bucket = os.environ.get("PATTERNODE_BASE_URL", "http://127.0.0.1:4010").rstrip("/") + "/_bucket"
    data = "\n".join(json.dumps(b) for b in bars).encode()            # JSON Lines, one bar a line
    urllib.request.urlopen(urllib.request.Request(f"{bucket}/in/export-kw.jsonl", data=data, method="PUT")).read()

    job = pn.post("/v1/segmentations/jobs", {
        "series": "exu/demo/backfill/ac-power", "profile": "standard@2026-11", "kind": "bars", "format": "jsonl",
        "source_url": f"{bucket}/in/export-kw.jsonl", "result_url": f"{bucket}/out/export-kw.json",
        "return_edge": True})                                          # to carry on as a forming series
    print(f"job {job['id']} {job['status']}")
    # In production, let segmentation.job.succeeded reach your webhook instead of polling.
    while job["status"] in ("queued", "running"):
        time.sleep(0.5)
        job = pn.get(f"/v1/segmentations/jobs/{job['id']}")
    if job["status"] == "failed":
        raise SystemExit(f"failed, not charged: {job['error']}")
    result = json.loads(urllib.request.urlopen(f"{bucket}/out/export-kw.json").read())   # from your storage
    print(f"succeeded: {len(result['segments'])} segments, edge returned: {'edge' in result}, "
          f"{job['usage']['samples_billed']} samples billed")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "examples/data/export-kw.json")
