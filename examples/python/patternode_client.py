"""A small client for the Patternode API. Python 3.10+, standard library only.

Copy it into your codebase, or use it as the reference for your own. It does the four
things every call needs: the key header, the body hash on writes, an idempotency key on
every POST, and retries that honour retry-after.

    from patternode_client import Patternode
    pn = Patternode()                      # reads PATTERNODE_API_KEY and PATTERNODE_BASE_URL
    print(pn.get("/v1/whoami"))
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
import urllib.error
import urllib.request
import uuid

DEFAULT_BASE_URL = "http://127.0.0.1:4010"  # the mock; set PATTERNODE_BASE_URL=https://api.patternode.com
RETRYABLE = {429, 500, 502, 503, 504}


class PatternodeError(Exception):
    """An error answer from the API. Branch on `code`, never on `message`."""

    def __init__(self, status: int, body: dict):
        err = (body or {}).get("error", {})
        self.status = status
        self.type = err.get("type", "api_error")
        self.code = err.get("details", {}).get("error_code", "unknown")
        self.problems = err.get("details", {}).get("problems", [])
        self.request_id = (body or {}).get("request_id")
        super().__init__(f"{status} {self.code}: {err.get('message', '')} (request {self.request_id})")


class Patternode:
    def __init__(self, api_key: str | None = None, base_url: str | None = None,
                 max_retries: int = 4, timeout: float = 60.0):
        self.api_key = api_key or os.environ.get("PATTERNODE_API_KEY")
        if not self.api_key:
            raise ValueError("Set PATTERNODE_API_KEY (from your secret store, never from source code).")
        self.base_url = (base_url or os.environ.get("PATTERNODE_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout

    # The verbs -------------------------------------------------------------------

    def get(self, path: str) -> dict:
        return self.request("GET", path)

    def post(self, path: str, body: dict | None = None, idempotency_key: str | None = None) -> dict:
        return self.request("POST", path, body, idempotency_key or str(uuid.uuid4()))

    def patch(self, path: str, body: dict) -> dict:
        return self.request("PATCH", path, body)

    def delete(self, path: str) -> dict:
        return self.request("DELETE", path)

    # The one place a request is made ---------------------------------------------

    def request(self, method: str, path: str, body: dict | None = None, idempotency_key: str | None = None) -> dict:
        raw = b"" if body is None else json.dumps(body, separators=(",", ":")).encode()
        headers = {"authorization": f"Bearer {self.api_key}", "accept": "application/json",
                   "user-agent": "patternode-example-python/1"}
        if method in ("POST", "PUT", "PATCH"):
            headers["content-type"] = "application/json"
            headers["x-amz-content-sha256"] = hashlib.sha256(raw).hexdigest()
        if idempotency_key:
            headers["idempotency-key"] = idempotency_key  # the same key on every retry
        for attempt in range(self.max_retries + 1):
            req = urllib.request.Request(self.base_url + path, data=raw if method != "GET" else None,
                                         method=method, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    text = resp.read()
                    return json.loads(text) if text else {}
            except urllib.error.HTTPError as e:
                text = e.read()
                try:
                    payload = json.loads(text) if text else {}
                except json.JSONDecodeError:
                    payload = {}
                if e.code in RETRYABLE and attempt < self.max_retries:
                    time.sleep(_wait(e.headers.get("retry-after"), attempt))
                    continue
                raise PatternodeError(e.code, payload) from None
            except (urllib.error.URLError, TimeoutError):
                if attempt < self.max_retries:
                    time.sleep(_wait(None, attempt))
                    continue
                raise
        raise RuntimeError("unreachable")


def _wait(retry_after: str | None, attempt: int) -> float:
    if retry_after:
        try:
            return min(float(retry_after), 60.0)
        except ValueError:
            pass
    return min(2 ** attempt, 30) * (0.5 + random.random() / 2)  # backoff with jitter
