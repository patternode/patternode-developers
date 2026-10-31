"""A mock of the Patternode API, for development and CI. Python 3.10+, standard library only.

    python mock/mock_patternode.py            # http://localhost:4010
    PATTERNODE_MOCK_PORT=5000 python mock/mock_patternode.py

It checks what the real service checks at the door (the key's shape, the body hash on
writes, scopes, time order) and answers in the real shapes. The segments are FAKE: every
four children make a parent. Never draw conclusions from them; they exist so your code can
be tested against the contract in specs/openapi.yaml.

Any key of the right shape is accepted. A pnk_test_ key may run only {"demo": ...}, as in
production. Webhooks for jobs are signed with PATTERNODE_MOCK_WEBHOOK_SECRET when it is set.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

KEY = re.compile(r"^pnk_(live|test|admin)_[0-9A-Za-z]{36}$")
FAN = 4  # FAKE: children per parent
EMPTY_SHA = hashlib.sha256(b"").hexdigest()
PRESETS = {
    "full": ["segment:run", "segment:read", "series:write", "stream:write", "stream:read"],
    "read-only": ["segment:read", "stream:read"],
    "stream-only": ["stream:write", "stream:read"],
    "admin": ["usage:read", "keys:manage", "billing:manage"],
}
DEMO = {
    "walk": [[1730246400000 + i * 3_600_000, 1730246400000 + (i + 1) * 3_600_000 - 1,
              100 + i, 102 + i, 99 + i, 101 + i] for i in range(32)],
    "sensor": [[1730246400000 + i * 900_000, 1730246400000 + (i + 1) * 900_000 - 1,
                50 + (i % 8), 53 + (i % 8), 49 + (i % 8), 51 + (i % 8)] for i in range(64)],
}

STATE = {"streams": {}, "uploads": {}, "jobs": {}, "keys": {}, "idem": {},
         "account": {"webhook_url": None, "spend_limit_usd": None}}
LOCK = threading.Lock()


def new_id(prefix: str) -> str:
    return prefix + secrets.token_hex(6)


def iso(t: float | None = None) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t if t is not None else time.time()))


class ApiError(Exception):
    def __init__(self, status: int, etype: str, code: str, message: str, problems=None):
        self.status, self.etype, self.code, self.message, self.problems = status, etype, code, message, problems

    def body(self) -> dict:
        details = {"error_code": self.code}
        if getattr(self, "expected_sequence", None):
            details["expected_sequence"] = self.expected_sequence
        if self.problems:
            details["problems"] = self.problems
        return {"type": "error", "error": {"type": self.etype, "message": self.message, "details": details},
                "request_id": new_id("req_")}


def invalid(message: str, code: str = "invalid_series", problems=None) -> ApiError:
    return ApiError(400, "invalid_request_error", code, message, problems)


# Series ------------------------------------------------------------------------------

def check_bars(bars) -> list[list[float]]:
    if not isinstance(bars, list) or len(bars) < 1:
        raise invalid("`bars` must be a non-empty list.")
    problems = []
    for i, b in enumerate(bars):
        if not (isinstance(b, list) and len(b) == 6 and all(isinstance(v, (int, float)) for v in b)):
            problems.append({"index": i, "problem": "not_a_bar"})
            continue
        ot, ct, o, h, lo, c = b
        if ct < ot:
            problems.append({"index": i, "problem": "closes_before_open"})
        if h < lo or not (lo <= o <= h and lo <= c <= h):
            problems.append({"index": i, "problem": "outside_high_low"})
        if min(o, h, lo, c) <= 0:
            problems.append({"index": i, "problem": "value_not_above_zero"})
        if i and isinstance(bars[i - 1], list) and len(bars[i - 1]) == 6 and ot <= bars[i - 1][1]:
            problems.append({"index": i, "problem": "times_not_increasing"})
    if problems:
        raise invalid(f"{len(problems)} bar(s) cannot be used.", problems=problems[:50])
    return bars


def bars_from_samples(samples) -> list[list[float]]:
    """FAKE: the real service has its own rule. Here every four samples make a bar."""
    if not isinstance(samples, list) or len(samples) < 2:
        raise invalid("`samples` must hold at least two [time, value] pairs.")
    out = []
    for i in range(0, len(samples), FAN):
        chunk = samples[i:i + FAN]
        vals = [v for _, v in chunk]
        out.append([chunk[0][0], chunk[-1][0], vals[0], max(vals), min(vals), vals[-1]])
    return check_bars(out)


def box(height: int, order: int, children: list[dict], parent: str | None, provisional: bool) -> dict:
    hi = max(children, key=lambda c: c["high"])
    lo = min(children, key=lambda c: c["low"])
    return {"id": f"h{height}@{int(children[0]['open_time'])}", "parent": parent, "height": height,
            "order": order, "bars": sum(c["bars"] for c in children),
            "open_time": children[0]["open_time"], "open": children[0]["open"],
            "high_time": hi["high_time"], "high": hi["high"], "low_time": lo["low_time"], "low": lo["low"],
            "close_time": children[-1]["close_time"], "close": children[-1]["close"], "provisional": provisional}


def fake_tree(bars: list[list[float]]) -> list[dict]:
    """FAKE segments: groups of FAN children at each level until one segment remains."""
    level = [{"id": f"h0@{int(b[0])}", "bars": 1, "open_time": b[0], "close_time": b[1], "open": b[2],
              "high": b[3], "low": b[4], "close": b[5], "high_time": (b[0] + b[1]) // 2,
              "low_time": (b[0] + b[1]) // 2} for b in bars]
    levels, height = [], 0
    while len(level) > 1 or height == 0:
        height += 1
        groups = [level[i:i + FAN] for i in range(0, len(level), FAN)]
        level = [box(height, n, g, None, provisional=(n == len(groups) - 1)) for n, g in enumerate(groups)]
        levels.append((level, groups))
        if len(level) == 1:
            break
    out = []
    for h in range(len(levels) - 1, -1, -1):  # parents first
        boxes, _ = levels[h]
        if h + 1 < len(levels):
            parents, pgroups = levels[h + 1]
            for p, g in zip(parents, pgroups):
                for child in g:
                    child["parent"] = p["id"]
        out.extend(boxes)
    order = {b["id"]: b for b in out}
    return sorted(order.values(), key=lambda b: (-b["height"], b["open_time"]))


def right_edge(segments: list[dict]) -> list[dict]:
    return sorted([s for s in segments if s["provisional"]], key=lambda s: s["height"])


PROFILE_VERSION = "2026-11"


def profile_version(profile: str | None) -> str:
    profile = profile or "standard"
    if not re.fullmatch(r"[a-z][a-z0-9-]*(@[0-9]{4}-[0-9]{2})?", profile):
        raise invalid("`profile` is a name, optionally @YYYY-MM.", "invalid_request")
    return profile if "@" in profile else f"{profile}@{PROFILE_VERSION}"


def to_ms(values: list, unit: str) -> list:
    """Bars or samples in the request's time_unit, as integers. us and ns come as strings in JSON."""
    if unit not in ("ms", "us", "ns"):
        raise invalid("`time_unit` is ms, us or ns.", "invalid_request")
    out = []
    for row in values or []:
        if not isinstance(row, list):
            out.append(row)
            continue
        n = 2 if len(row) == 6 else 1
        times = []
        for t in row[:n]:
            if unit == "ms" and isinstance(t, (int, float)):
                times.append(t)
            elif unit != "ms" and isinstance(t, str) and t.isdigit():
                times.append(int(t))
            else:
                raise invalid(f"times in {unit} are {'integers' if unit == 'ms' else 'strings of digits'}.")
        out.append(times + row[n:])
    return out


def times_out(obj, unit: str):
    """Times back in the caller's unit: strings for us and ns."""
    if unit == "ms":
        return obj
    if isinstance(obj, list):
        return [times_out(o, unit) for o in obj]
    if isinstance(obj, dict):
        return {k: (str(int(v)) if k.endswith("_time") and isinstance(v, (int, float)) else times_out(v, unit))
                for k, v in obj.items()}
    return obj


def segmentation(series: str, profile: str, bars: list) -> dict:
    segs = fake_tree(bars)
    samples = len(bars)
    return {"object": "segmentation", "id": new_id("seg_"), "series": series, "profile_version": profile_version(profile),
            "bars": len(bars), "depth": max(s["height"] for s in segs), "segments": segs,
            "usage": {"samples_billed": max(samples, 10_000), "cost_usd": round(max(samples, 10_000) * 2e-6, 6)},
            "mock": "FAKE segments: four children per parent"}


def append_seq(stream: dict, sequence, bar: list) -> dict:
    """Apply a bar by sequence: a repeat returns the first answer, a gap is refused."""
    if not isinstance(sequence, int) or sequence < 1:
        raise invalid("`sequence` is an integer from 1.", "invalid_request")
    if sequence in stream["answers"]:
        return stream["answers"][sequence]
    expected = len(stream["bars"]) + 1
    if sequence != expected:
        e = ApiError(409, "conflict_error", "sequence_gap", f"Expected sequence {expected}.")
        e.expected_sequence = expected
        raise e
    out = append(stream, bar)
    out["sequence"] = sequence
    stream["answers"][sequence] = out
    if len(stream["answers"]) > 1000:  # the mock keeps the last thousand answers
        stream["answers"].pop(min(stream["answers"]))
    return out


def append(stream: dict, bar: list) -> dict:
    if not (isinstance(bar, list) and len(bar) == 6):
        raise invalid("`bar` is [open_time, close_time, open, high, low, close].")
    before = {s["height"]: s for s in right_edge(fake_tree(stream["bars"]))} if stream["bars"] else {}
    if stream["bars"] and bar[0] <= stream["bars"][-1][1]:
        raise ApiError(409, "conflict_error", "out_of_order",
                       "The bar opens before the stream's last bar closed. The stream is unchanged.")
    check_bars(stream["bars"][-1:] + [bar] if stream["bars"] else [bar])
    stream["bars"].append(bar)
    after = right_edge(fake_tree(stream["bars"]))
    events, outcome = [], "started" if len(stream["bars"]) <= 2 else "extended"
    child = {"id": f"h0@{int(bar[0])}", "parent": after[0]["id"] if after else None, "height": 0, "order": 0,
             "bars": 1, "open_time": bar[0], "open": bar[2], "high_time": (bar[0] + bar[1]) // 2, "high": bar[3],
             "low_time": (bar[0] + bar[1]) // 2, "low": bar[4], "close_time": bar[1], "close": bar[5],
             "provisional": False}
    if len(stream["bars"]) > 2:
        for node in after:
            prev = before.get(node["height"])
            if prev and prev["id"] != node["id"]:
                events.append({"kind": "segmented", "level": node["height"] - 1,
                               "node": {**prev, "provisional": False}, "child": child})
                outcome = "segmented"
            else:
                events.append({"kind": "extended", "level": node["height"] - 1, "node": node, "child": child})
            child = node
    return {"object": "observation_result", "stream_id": stream["id"], "series": stream["series"],
            "profile_version": stream["profile_version"],
            "bars": len(stream["bars"]), "outcome": outcome, "events": events, "right_edge": after}


# Webhooks ----------------------------------------------------------------------------

def sign(secret: str, msg_id: str, ts: int, body: bytes) -> str:
    key = base64.b64decode(secret.removeprefix("whsec_"))
    mac = hmac.new(key, f"{msg_id}.{ts}.".encode() + body, hashlib.sha256).digest()
    return "v1," + base64.b64encode(mac).decode()


def deliver(url: str, event: dict, msg_id: str) -> None:
    secret = os.environ.get("PATTERNODE_MOCK_WEBHOOK_SECRET")
    if not secret:
        return
    body = json.dumps(event, separators=(",", ":")).encode()
    ts = int(time.time())
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "content-type": "application/json", "webhook-id": msg_id, "webhook-timestamp": str(ts),
        "webhook-signature": sign(secret, msg_id, ts, body), "user-agent": "patternode-webhooks/1 (mock)"})
    try:
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as e:  # the mock does not retry
        print(f"webhook to {url} failed: {e!r}")


# HTTP --------------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "patternode-mock/1"

    def log_message(self, fmt, *args):
        if os.environ.get("PATTERNODE_MOCK_QUIET") != "1":
            super().log_message(fmt, *args)

    def _send(self, status: int, body: dict | None, headers: dict | None = None):
        raw = b"" if body is None else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("request-id", (body or {}).get("request_id") or new_id("req_"))
        self.send_header("ratelimit-policy", '"default";q=300;w=60')
        self.send_header("ratelimit", '"default";r=299;t=60')
        self.send_header("server-timing", 'app;dur=1')
        if self.headers.get("traceparent"):
            self.send_header("traceparent", self.headers["traceparent"])
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _identity(self) -> dict:
        auth = self.headers.get("authorization", "")
        key = auth[7:] if auth.startswith("Bearer ") else self.headers.get("x-api-key", "")
        if not KEY.match(key):
            raise ApiError(401, "authentication_error", "missing_api_key" if not key else "invalid_api_key",
                           "Send a key as `Authorization: Bearer pnk_...`.")
        kind = key.split("_")[1]
        scopes = PRESETS["admin"] if kind == "admin" else PRESETS["full"]
        return {"key": key, "kind": kind, "scopes": scopes}

    def _body(self) -> dict:
        raw = self.rfile.read(int(self.headers.get("content-length") or 0))
        sha = self.headers.get("x-amz-content-sha256")
        if not sha:
            raise ApiError(400, "invalid_request_error", "missing_content_sha256",
                           "Writes must send the body's SHA-256 in x-amz-content-sha256.")
        if sha != hashlib.sha256(raw).hexdigest():
            raise ApiError(403, "permission_error", "invalid_content_sha256", "The body hash does not match.")
        self._raw = raw
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise invalid("The body is not JSON.", "invalid_request")

    def _need(self, ident: dict, scope: str):
        if scope not in ident["scopes"]:
            raise ApiError(403, "permission_error", "missing_scope", f"This key lacks `{scope}`.")

    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")

    def do_PATCH(self):
        self._route("PATCH")

    def do_DELETE(self):
        self._route("DELETE")

    def _route(self, method: str):
        path = urlparse(self.path).path.rstrip("/")
        try:
            if method == "POST" and path.startswith("/_upload/"):
                return self._upload_file(path.split("/")[-1])
            if method == "GET" and path.startswith("/_results/"):  # a signed link in production: no key
                job = STATE["jobs"].get(path.split("/")[-1])
                if not job or "result" not in job:
                    raise ApiError(404, "not_found_error", "not_found", "No result.")
                return self._send(200, job["result"])
            ident = self._identity()
            body = self._body() if method in ("POST", "PATCH") else {}
            idem = self.headers.get("idempotency-key")
            if idem and method == "POST":
                with LOCK:
                    seen = STATE["idem"].get(idem)
                if seen:
                    if seen[0] != hashlib.sha256(self._raw).hexdigest():
                        raise ApiError(422, "invalid_request_error", "idempotency_conflict",
                                       "This Idempotency-Key was used with a different body.")
                    return self._send(*seen[1:])
            status, out, headers = self._dispatch(method, path, ident, body)
            if idem and method == "POST":
                with LOCK:
                    STATE["idem"][idem] = (hashlib.sha256(self._raw).hexdigest(), status, out, headers)
            self._send(status, out, headers)
        except ApiError as e:
            self._send(e.status, e.body(), {"retry-after": "1"} if e.status == 429 else None)

    def _dispatch(self, m: str, p: str, ident: dict, body: dict):
        if m == "GET" and p == "/v1/whoami":
            return 200, {"object": "key", "id": "key_mock", "kind": ident["kind"], "name": "mock",
                         "scopes": ident["scopes"], "account": "acct_mock", "tier": "evaluation",
                         "expires_at": None}, None
        if m == "POST" and p == "/v1/segmentations":
            self._need(ident, "segment:run")
            if "demo" in body:
                if body["demo"] not in DEMO:
                    raise invalid("Demonstration series are: walk, sensor.", "invalid_request")
                out = segmentation(f"demo/{body['demo']}", "standard", DEMO[body["demo"]])
                out["usage"] = {"samples_billed": 0, "cost_usd": 0.0}
                return 200, out, None
            if ident["kind"] == "test":
                raise ApiError(403, "permission_error", "test_key_demo_only",
                               'Test keys run only on demonstration series. Send {"demo": "walk"}.')
            series = self._series(body)
            unit = body.get("time_unit", "ms")
            bars = check_bars(to_ms(body["bars"], unit)) if "bars" in body \
                else bars_from_samples(to_ms(body.get("samples"), unit))
            out = segmentation(series, body.get("profile", "standard"), bars)
            out["time_unit"] = unit
            return 200, times_out(out, unit), None
        if m == "POST" and p == "/v1/uploads":
            self._need(ident, "series:write")
            if body.get("format") not in ("csv", "jsonl"):
                raise invalid("`format` must be csv or jsonl.", "invalid_request")
            uid = new_id("upl_")
            host = self.headers.get("host", "localhost:4010")
            with LOCK:
                STATE["uploads"][uid] = {"format": body["format"], "data": None}
            return 201, {"object": "upload", "id": uid, "url": f"http://{host}/_upload/{uid}",
                         "fields": {"key": uid}, "max_bytes": body.get("size_bytes", 100_000_000),
                         "expires_at": iso(time.time() + 3600)}, None
        if m == "POST" and p == "/v1/segmentations/jobs":
            self._need(ident, "segment:run")
            return self._job(ident, body)
        if m == "GET" and (mm := re.fullmatch(r"/v1/segmentations/jobs/(job_\w+)", p)):
            self._need(ident, "segment:read")
            job = STATE["jobs"].get(mm.group(1))
            if not job:
                raise ApiError(404, "not_found_error", "not_found", "No such job.")
            return 200, {k: v for k, v in job.items() if k != "result"}, None
        if m == "POST" and p == "/v1/streams":
            self._need(ident, "stream:write")
            if ident["kind"] == "test":
                raise ApiError(403, "permission_error", "test_key_demo_only", "Test keys cannot open streams.")
            unit = body.get("time_unit", "ms")
            stream = {"id": new_id("str_"), "series": self._series(body), "unit": unit,
                      "profile_version": profile_version(body.get("profile")),
                      "bars": [], "answers": {}, "created_at": iso()}
            out = append_seq(stream, 1, to_ms([body.get("bar")], unit)[0])
            with LOCK:
                STATE["streams"][stream["id"]] = stream
            return 201, times_out(out, unit), None
        if m == "POST" and p == "/v1/streams/observations":
            self._need(ident, "stream:write")
            items = body.get("observations")
            if not isinstance(items, list) or not 0 < len(items) <= 1000:
                raise invalid("`observations` holds 1 to 1000 items.", "invalid_request")
            results = []
            for item in items:
                try:
                    stream = STATE["streams"].get(item.get("stream_id"))
                    if not stream:
                        raise ApiError(404, "not_found_error", "not_found", "No such stream.")
                    with LOCK:
                        r = append_seq(stream, item.get("sequence"),
                                       to_ms([item.get("bar")], body.get("time_unit", stream["unit"]))[0])
                    results.append({"status": 200, "result": times_out(r, stream["unit"])})
                except ApiError as e:
                    results.append({"status": e.status, "error": e.body()})
            return 200, {"object": "observation_batch_result", "results": results}, None
        if m == "GET" and p == "/v1/streams":
            self._need(ident, "stream:read")
            return 200, {"object": "list", "has_more": False,
                         "data": [self._stream_view(st) for st in STATE["streams"].values()]}, None
        if mm := re.fullmatch(r"/v1/streams/(str_\w+)(/observations)?", p):
            stream = STATE["streams"].get(mm.group(1))
            if not stream:
                raise ApiError(404, "not_found_error", "not_found", "No such stream.")
            if m == "POST" and mm.group(2):
                self._need(ident, "stream:write")
                unit = body.get("time_unit", stream["unit"])
                with LOCK:
                    out = append_seq(stream, body.get("sequence"), to_ms([body.get("bar")], unit)[0])
                return 200, times_out(out, stream["unit"]), None
            if m == "GET" and not mm.group(2):
                return 200, self._stream_view(stream), None
            if m == "DELETE" and not mm.group(2):
                with LOCK:
                    del STATE["streams"][stream["id"]]
                return 204, None, None
        if p == "/v1/keys" and m == "POST":
            self._need(ident, "keys:manage")
            kind = body.get("kind", "live")
            alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
            secret = f"pnk_{kind}_" + "".join(secrets.choice(alphabet) for _ in range(36))
            scopes = body.get("scopes", "admin" if kind == "admin" else "full")
            rec = {"object": "api_key", "id": new_id("key_"), "kind": kind, "name": body.get("name"),
                   "status": "active", "scopes": PRESETS.get(scopes, scopes) if isinstance(scopes, str) else scopes,
                   "hint": "..." + secret[-4:], "created_at": iso(), "expires_at": None, "last_used_at": None}
            with LOCK:
                STATE["keys"][rec["id"]] = rec
            return 201, {**rec, "key": secret, "note": "This is the only time the key is shown. Store it now."}, None
        if p == "/v1/keys" and m == "GET":
            self._need(ident, "keys:manage")
            return 200, {"object": "list", "data": list(STATE["keys"].values())}, None
        if mm := re.fullmatch(r"/v1/keys/(key_\w+)(/disable|/enable)?", p):
            self._need(ident, "keys:manage")
            rec = STATE["keys"].get(mm.group(1))
            if not rec:
                raise ApiError(404, "not_found_error", "not_found", "No such key.")
            rec["status"] = {"/disable": "disabled", "/enable": "active", None: "deleted"}[mm.group(2)]
            return 200, rec, None
        if p == "/v1/account":
            if m == "PATCH":
                self._need(ident, "keys:manage")
                STATE["account"].update({k: body[k] for k in ("webhook_url", "spend_limit_usd") if k in body})
            return 200, {"object": "account", "id": "acct_mock", "tier": "evaluation", "balance_usd": 20.0,
                         "terms_accepted_at": iso(0), **STATE["account"]}, None
        if m == "POST" and p == "/v1/account/webhook_secret":
            self._need(ident, "keys:manage")
            return 201, {"object": "webhook_secret", "secret": "whsec_" + base64.b64encode(os.urandom(32)).decode(),
                         "note": "The mock does not sign with this; set PATTERNODE_MOCK_WEBHOOK_SECRET."}, None
        raise ApiError(404, "not_found_error", "not_found", f"No route {m} {p} in the mock.")

    def _stream_view(self, st: dict) -> dict:
        last = st["bars"][-1][1] if st["bars"] else None
        scale = {"ms": 1, "us": 1_000, "ns": 1_000_000}[st["unit"]]
        return times_out({"object": "stream", "id": st["id"], "series": st["series"],
                          "profile_version": st["profile_version"], "last_sequence": len(st["bars"]),
                          "bars": len(st["bars"]), "right_edge": right_edge(fake_tree(st["bars"])),
                          "created_at": st["created_at"],
                          "last_bar_at": iso(last / scale / 1000) if last is not None else None}, st["unit"])

    def _series(self, body: dict) -> str:
        s = body.get("series")
        if not isinstance(s, str) or not 0 < len(s) <= 200:
            raise invalid("`series` is required, at most 200 characters.", "invalid_request")
        return s

    def _upload_file(self, uid: str):
        raw = self.rfile.read(int(self.headers.get("content-length") or 0))
        if uid not in STATE["uploads"]:
            return self._send(404, None)
        STATE["uploads"][uid]["data"] = raw
        self._send(204, None)

    def _job(self, ident: dict, body: dict):
        up = STATE["uploads"].get(body.get("upload_id"))
        if not up or up["data"] is None:
            raise invalid("No such upload, or nothing was uploaded to it.", "invalid_request")
        series = self._series(body)
        job = {"object": "segmentation_job", "id": new_id("job_"), "status": "running", "series": series,
               "created_at": iso(), "finished_at": None, "result_url": None, "usage": None, "error": None}
        host = self.headers.get("host", "localhost:4010")
        STATE["jobs"][job["id"]] = job
        webhook = body.get("webhook_url") or STATE["account"]["webhook_url"]

        def run():
            try:
                text = up["data"].decode()
                if b"\r\n\r\n" in up["data"]:  # a multipart form: take the file part
                    text = text.split("\r\n\r\n", 2)[-1].rsplit("\r\n--", 1)[0]
                rows = [json.loads(line) for line in text.splitlines() if line.strip()] if up["format"] == "jsonl" \
                    else [[float(x) for x in line.split(",")] for line in text.splitlines()[1:] if line.strip()]
                bars = check_bars(rows) if body.get("kind") == "bars" else bars_from_samples(rows)
                job["result"] = segmentation(series, body.get("profile", "standard"), bars)
                job.update(status="succeeded", result_url=f"http://{host}/_results/{job['id']}",
                           usage=job["result"]["usage"])
            except ApiError as e:
                job.update(status="failed", error=e.body()["error"])
            job["finished_at"] = iso()
            if webhook:
                event = {"type": f"segmentation.job.{job['status']}", "created_at": iso(),
                         "data": {k: v for k, v in job.items() if k != "result"}}
                deliver(webhook, event, f"msg_{job['id']}")

        threading.Timer(0.2, run).start()
        return 202, job, {"location": f"/v1/segmentations/jobs/{job['id']}"}


def serve(port: int | None = None) -> ThreadingHTTPServer:
    port = port if port is not None else int(os.environ.get("PATTERNODE_MOCK_PORT", "4010"))
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    srv = serve()
    print(f"Patternode mock on http://127.0.0.1:{srv.server_address[1]} (FAKE segments)")
    srv.serve_forever()
