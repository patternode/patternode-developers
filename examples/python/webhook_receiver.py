"""Pattern 4, the webhook receiver: verify, deduplicate, answer 2xx at once, then do the work.

    PATTERNODE_WEBHOOK_SECRET=whsec_... python examples/python/webhook_receiver.py    # :8787

Deliveries are signed to the Standard Webhooks specification. `verify` is the part to copy;
it is also what terraform/aws runs in its Lambda.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

TOLERANCE_S = 300


class InvalidSignature(Exception):
    pass


def verify(secret: str, headers: dict[str, str], body: bytes, now: float | None = None) -> dict:
    """Return the event if the delivery is genuine and fresh, else raise InvalidSignature.

    `headers` keys are lower case. During a secret rotation Patternode sends two signatures,
    space separated; either may match.
    """
    msg_id, ts, sigs = headers.get("webhook-id"), headers.get("webhook-timestamp"), headers.get("webhook-signature")
    if not (msg_id and ts and sigs):
        raise InvalidSignature("missing webhook headers")
    try:
        ts_int = int(ts)
    except ValueError:
        raise InvalidSignature("bad timestamp") from None
    if abs((now if now is not None else time.time()) - ts_int) > TOLERANCE_S:
        raise InvalidSignature("timestamp outside tolerance")
    key = base64.b64decode(secret.removeprefix("whsec_"))
    expected = base64.b64encode(hmac.new(key, f"{msg_id}.{ts}.".encode() + body, hashlib.sha256).digest()).decode()
    for sig in sigs.split(" "):
        version, _, value = sig.partition(",")
        if version == "v1" and hmac.compare_digest(value, expected):
            return json.loads(body)
    raise InvalidSignature("no signature matched")


SEEN: set[str] = set()  # in production: a table with a TTL, keyed on webhook-id


def handle(event: dict) -> None:
    """Your work, after the 2xx. Here it only prints."""
    data = event.get("data", {})
    if event["type"] == "segmentation.job.succeeded":
        print(f"job {data['id']} succeeded: fetch {data['result_url']}")
    elif event["type"] == "segmentation.job.failed":
        print(f"job {data['id']} failed, not charged: {data.get('error')}")
    else:
        print(f"ignored {event['type']}")  # unknown types are expected: new ones are added without notice


class Receiver(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("content-length") or 0))
        headers = {k.lower(): v for k, v in self.headers.items()}
        try:
            event = verify(os.environ["PATTERNODE_WEBHOOK_SECRET"], headers, body)
        except InvalidSignature as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(str(e).encode())
            return
        self.send_response(204)
        self.end_headers()
        if headers["webhook-id"] in SEEN:
            return
        SEEN.add(headers["webhook-id"])
        handle(event)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8787"))
    print(f"listening on :{port}")
    HTTPServer(("127.0.0.1", port), Receiver).serve_forever()
