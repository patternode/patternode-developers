"""A mock of the Patternode API, for development and CI. Python 3.10+, standard library only.

    python mock/mock_patternode.py            # http://localhost:4010
    PATTERNODE_MOCK_PORT=5000 python mock/mock_patternode.py

It checks what the real service checks at the door (the key's shape, the body hash on
writes, scopes, time order, the edge's seal) and answers in the real shapes. The segments
are FAKE: every four children make a parent. Never draw conclusions from them; they exist
so your code can be tested against the contract in specs/openapi.yaml.

Like the service, the mock keeps none of your series. A forming series travels as its edge:
the mock's edge is signed but readable, where the service's is also encrypted. Jobs read
from and write to links you give; for tests, the mock serves a stand-in for your storage at
/_bucket/<path> (GET and PUT, no key). It also serves the status page's files (specs/status.yaml)
at /api/v2/, with no key, and the account's view at GET /v1/status.

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
PROFILE_VERSION = "2026-11"
SEAL_KEY = b"patternode-mock-edge-key"  # the mock's own; the service's is per account and secret
PRESETS = {
    "full": ["segment:run", "segment:read"],
    "read-only": ["segment:read"],
    "admin": ["usage:read", "keys:manage", "billing:manage"],
}
DEMO = {
    "walk": [[1730246400000 + i * 3_600_000, 1730246400000 + (i + 1) * 3_600_000 - 1,
              100 + i, 102 + i, 99 + i, 101 + i] for i in range(32)],
    "sensor": [[1730246400000 + i * 900_000, 1730246400000 + (i + 1) * 900_000 - 1,
                50 + (i % 8), 53 + (i % 8), 49 + (i % 8), 51 + (i % 8)] for i in range(64)],
}

# Account metadata only: jobs (status and usage), keys, idempotency hashes, settings.
# Never a series, an edge or a result. _bucket stands in for the partner's own storage.
STATE = {"jobs": {}, "keys": {}, "idem": {}, "bucket": {},
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
        if self.problems:
            details["problems"] = self.problems
        return {"type": "error", "error": {"type": self.etype, "message": self.message, "details": details},
                "request_id": new_id("req_")}


def invalid(message: str, code: str = "invalid_series", problems=None) -> ApiError:
    return ApiError(400, "invalid_request_error", code, message, problems)


# Series ------------------------------------------------------------------------------

def check_bars(bars, after: float | None = None) -> list[list[float]]:
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
    if after is not None and bars[0][0] <= after:
        raise ApiError(409, "conflict_error", "out_of_order",
                       "The first bar opens before the edge's last bar closed. Nothing was applied.")
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


def leaf(b: list) -> dict:
    mid = (b[0] + b[1]) // 2
    return {"id": f"h0@{int(b[0])}", "bars": 1, "open_time": b[0], "open": b[2], "high_time": mid, "high": b[3],
            "low_time": mid, "low": b[4], "close_time": b[1], "close": b[5]}


def summarise(height: int, order: int, children: list[dict], parent: str | None, provisional: bool) -> dict:
    hi = max(children, key=lambda c: c["high"])
    lo = min(children, key=lambda c: c["low"])
    return {"id": f"h{height}@{int(children[0]['open_time'])}", "parent": parent, "height": height,
            "order": order, "bars": sum(c["bars"] for c in children),
            "open_time": children[0]["open_time"], "open": children[0]["open"],
            "high_time": hi["high_time"], "high": hi["high"], "low_time": lo["low_time"], "low": lo["low"],
            "close_time": children[-1]["close_time"], "close": children[-1]["close"], "provisional": provisional}


LEAF_KEYS = ("id", "bars", "open_time", "open", "high_time", "high", "low_time", "low", "close_time", "close")


class Tree:
    """FAKE incremental segmentation. Its whole state is the open group at each level, which
    is what the edge carries; extending bar by bar equals segmenting all bars at once."""

    def __init__(self, state: dict | None = None):
        state = state or {}
        self.levels: list[list[dict]] = state.get("levels", [])   # open children, per level from 1
        self.orders: list[int] = state.get("orders", [])          # order of the open node, per level
        self.bars: int = state.get("bars", 0)
        self.last_close = state.get("last_close")

    def state(self) -> dict:
        return {"levels": self.levels, "orders": self.orders, "bars": self.bars, "last_close": self.last_close}

    def _push(self, h: int, child: dict, closed: list[dict]) -> None:
        """Offer a child to level h (1-based); close the open node when it is full."""
        while len(self.levels) < h:
            self.levels.append([])
            self.orders.append(0)
        group = self.levels[h - 1]
        if len(group) == FAN:
            node = summarise(h, self.orders[h - 1], group, None, False)
            self.levels[h - 1] = [child]
            self.orders[h - 1] += 1
            self._push(h + 1, {k: node[k] for k in LEAF_KEYS}, closed)
            node["parent"] = f"h{h + 1}@{int(self.levels[h][0]['open_time'])}"  # the group it joined
            closed.append(node)
        else:
            group.append(child)

    def extend(self, bars: list) -> list[dict]:
        closed: list[dict] = []
        for b in bars:
            self._push(1, leaf(b), closed)
            self.bars += 1
            self.last_close = b[1]
        return closed

    def right_edge(self) -> list[dict]:
        edge = []
        for h, group in enumerate(self.levels, start=1):
            if not group:
                continue
            parent = f"h{h + 1}@{int(self.levels[h][0]['open_time'])}" if h < len(self.levels) and self.levels[h] else None
            edge.append(summarise(h, self.orders[h - 1], group, parent, True))
        return edge


def profile_version(profile: str | None) -> str:
    profile = profile or "standard"
    if not re.fullmatch(r"[a-z][a-z0-9-]*(@[0-9]{4}-[0-9]{2})?", profile):
        raise invalid("`profile` is a name, optionally @YYYY-MM.", "invalid_request")
    return profile if "@" in profile else f"{profile}@{PROFILE_VERSION}"


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def seal(account: str, series: str, version: str, tree: Tree) -> str:
    payload = b64(json.dumps({"v": 1, "a": account, "s": series, "p": version, "t": tree.state()},
                             separators=(",", ":")).encode())
    mac = b64(hmac.new(SEAL_KEY, f"pne1.{payload}.mock".encode(), hashlib.sha256).digest())
    return f"pne1.{payload}.mock.{mac}"


def unseal(edge: str, account: str, series: str, version: str | None) -> tuple[Tree, str]:
    try:
        prefix, payload, kid, mac = edge.split(".")
        good = hmac.compare_digest(mac, b64(hmac.new(SEAL_KEY, f"pne1.{payload}.{kid}".encode(),
                                                     hashlib.sha256).digest()))
        data = json.loads(unb64(payload)) if good and prefix == "pne1" else None
    except Exception:
        data = None
    if not data:
        raise invalid("The edge is not one Patternode sealed, or it was changed.", "edge_invalid")
    if data["a"] != account or data["s"] != series or (version and data["p"] != version):
        raise ApiError(409, "conflict_error", "edge_mismatch",
                       "This edge belongs to another account, series or profile version. Nothing was applied.")
    return Tree(data["t"]), data["p"]


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
        return {k: (str(int(v)) if (k.endswith("_time") or k == "edge_last_close_time") and isinstance(v, (int, float))
                    else times_out(v, unit)) for k, v in obj.items()}
    return obj


def usage(n: int) -> dict:
    billed = max(n, 10_000)
    return {"samples_billed": billed, "cost_usd": round(billed * 2e-6, 6)}


def segmentation(account: str, series: str, profile: str | None, bars: list, return_edge: bool, raw: bytes) -> dict:
    version = profile_version(profile)
    tree = Tree()
    closed = tree.extend(bars)
    segments = sorted(closed + tree.right_edge(), key=lambda s: (-s["height"], s["open_time"]))
    out = {"object": "segmentation", "id": "seg_" + hashlib.sha256(raw).hexdigest()[:12], "series": series,
           "profile_version": version, "bars": len(bars), "depth": max(s["height"] for s in segments),
           "segments": segments, "usage": usage(len(bars)), "mock": "FAKE segments: four children per parent"}
    if return_edge:
        out["edge"] = seal(account, series, version, tree)
        out["edge_last_close_time"] = tree.last_close
    return out


def extension(account: str, item: dict, unit_default: str = "ms") -> dict:
    series = item.get("series")
    if not isinstance(series, str) or not 0 < len(series) <= 200:
        raise invalid("`series` is required, at most 200 characters.", "invalid_request")
    unit = item.get("time_unit", unit_default)
    bars = to_ms(item.get("bars"), unit)
    if item.get("edge"):
        tree, version = unseal(item["edge"], account, series, profile_version(item["profile"]) if item.get("profile") else None)
        check_bars(bars, after=tree.last_close)
        started = False
    else:
        version, tree, started = profile_version(item.get("profile")), Tree(), True
        check_bars(bars)
    closed = tree.extend(bars)
    out = {"object": "extension", "series": series, "profile_version": version, "time_unit": unit, "bars": tree.bars,
           "outcome": "started" if started else ("segmented" if closed else "extended"),
           "closed": sorted(closed, key=lambda s: (s["height"], s["open_time"])), "right_edge": tree.right_edge(),
           "edge": seal(account, series, version, tree), "edge_last_close_time": tree.last_close,
           "usage": usage(len(bars))}
    return times_out(out, unit)


# Webhooks ----------------------------------------------------------------------------

# The status page (specs/status.yaml): the same files status.patternode.com serves, with no key.
# Delve is listed but not in service; the sites are up. Invented history, the shapes are real.

STATUS_COMPONENTS = [
    ("delve", "Delve API", None, "not_in_service", "Segmentation, forming series, jobs, keys and account"),
    ("delve-segmentation", "Segmentation", "delve", "not_in_service", "POST /v1/segmentations"),
    ("delve-extend", "Forming series", "delve", "not_in_service", "POST /v1/segmentations/extend"),
    ("delve-jobs", "Jobs", "delve", "not_in_service", "POST /v1/segmentations/jobs"),
    ("delve-account", "Keys and account", "delve", "not_in_service", "/v1/keys, /v1/account"),
    ("webhooks", "Webhooks", None, "not_in_service", "Event delivery to your endpoint"),
    ("developer-portal", "Developer portal", None, "operational", "developers.patternode.com"),
    ("website", "Website", None, "operational", "patternode.com"),
]
ACCOUNT_COMPONENTS = ("delve-segmentation", "delve-extend", "delve-jobs", "delve-account", "webhooks")


def status_page() -> dict:
    return {"id": "patternode", "name": "Patternode", "url": "https://status.patternode.com",
            "time_zone": "Etc/UTC", "updated_at": iso()}


def status_components() -> list[dict]:
    out = []
    for i, (cid, name, group, state, desc) in enumerate(STATUS_COMPONENTS):
        c = {"id": cid, "name": name, "status": state, "description": desc, "group": any(x[2] == cid for x in STATUS_COMPONENTS),
             "group_id": group, "position": i + 1, "only_show_if_degraded": False,
             "created_at": "2026-11-01T00:00:00Z", "updated_at": iso()}
        if c["group"]:
            c["components"] = [x[0] for x in STATUS_COMPONENTS if x[2] == cid]
        if state != "not_in_service":
            c["uptime"] = {"day": 100.0, "week": 100.0, "quarter": 99.98}
        out.append(c)
    return out


def status_file(name: str):
    """The body of /api/v2/<name>, or None for no such file."""
    page, components = status_page(), status_components()
    indicator = {"indicator": "none", "description": "All systems operational"}
    if name == "status.json":
        return {"page": page, "status": indicator}
    if name == "summary.json":
        return {"page": page, "status": indicator, "components": components, "incidents": [],
                "scheduled_maintenances": []}
    if name == "components.json":
        return {"page": page, "components": components}
    if name in ("incidents.json", "incidents/unresolved.json"):
        return {"page": page, "incidents": []}
    if name == "scheduled-maintenances.json":
        return {"page": page, "scheduled_maintenances": []}
    m = re.fullmatch(r"uptime/([a-z0-9-]+)\.json", name)
    if m and any(c["id"] == m.group(1) for c in components):
        live = next(c for c in components if c["id"] == m.group(1))["status"] != "not_in_service"
        day = 86400
        return {"component": m.group(1),
                "days": [{"date": time.strftime("%Y-%m-%d", time.gmtime(time.time() - (89 - i) * day)),
                          "availability": 100.0 if live else None, "checks": 288 if live else 0,
                          **({"latency_ms": {"p50": 41.0, "p95": 88.0}} if live else {})} for i in range(90)]}
    return None


def account_status(account: str) -> dict:
    states = {c["id"]: c for c in status_components()}
    return {"object": "account_status", "account": account, "plan": "evaluation", "jurisdiction": "anz",
            "indicator": "none",
            "components": [{"id": i, "name": states[i]["name"], "status": states[i]["status"]} for i in ACCOUNT_COMPONENTS],
            "incidents": [], "scheduled_maintenances": [], "availability": None,
            "page_url": "https://status.patternode.com", "checked_at": iso()}


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

    def _send(self, status: int, body: dict | None, headers: dict | None = None, raw: bytes | None = None):
        raw = raw if raw is not None else (b"" if body is None else json.dumps(body).encode())
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("request-id", (body or {}).get("request_id") or new_id("req_"))
        self.send_header("ratelimit-policy", '"default";q=300;w=60')
        self.send_header("ratelimit", '"default";r=299;t=60')
        self.send_header("server-timing", "app;dur=1")
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
        return {"key": key, "kind": kind, "scopes": PRESETS["admin"] if kind == "admin" else PRESETS["full"],
                "account": "acct_mock"}

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

    def _live(self, ident: dict):
        if ident["kind"] == "test":
            raise ApiError(403, "permission_error", "test_key_demo_only",
                           'Test keys run only on demonstration series. Send {"demo": "walk"}.')

    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")

    def do_PUT(self):
        self._route("PUT")

    def do_PATCH(self):
        self._route("PATCH")

    def do_DELETE(self):
        self._route("DELETE")

    def _route(self, method: str):
        path = urlparse(self.path).path.rstrip("/")
        try:
            if path.startswith("/_bucket/"):  # a stand-in for the partner's own storage, no key
                return self._bucket(method, path[len("/_bucket/"):])
            if path.startswith("/api/v2/"):   # the status page's files, no key, read only
                body = status_file(path[len("/api/v2/"):]) if method == "GET" else None
                if body is None:
                    return self._send(404, None, {"content-type": "text/html"}, raw=b"<h1>Not found</h1>")
                return self._send(200, body, {"cache-control": "public, max-age=300", "access-control-allow-origin": "*"})
            ident = self._identity()
            body = self._body() if method in ("POST", "PATCH") else {}
            idem = self.headers.get("idempotency-key")
            if idem and method == "POST":
                digest = hashlib.sha256(self._raw).hexdigest()
                with LOCK:
                    seen = STATE["idem"].setdefault(idem, digest)
                if seen != digest:
                    raise ApiError(422, "invalid_request_error", "idempotency_conflict",
                                   "This Idempotency-Key was used with a different body.")
            status, out, headers = self._dispatch(method, path, ident, body)
            self._send(status, out, headers)
        except ApiError as e:
            self._send(e.status, e.body(), {"retry-after": "1"} if e.status == 429 else None)

    def _dispatch(self, m: str, p: str, ident: dict, body: dict):
        acct = ident["account"]
        if m == "GET" and p == "/v1/status":
            return 200, account_status(acct), None
        if m == "GET" and p == "/v1/whoami":
            return 200, {"object": "key", "id": "key_mock", "kind": ident["kind"], "name": "mock",
                         "scopes": ident["scopes"], "account": acct, "tier": "evaluation", "expires_at": None}, None
        if m == "POST" and p == "/v1/segmentations":
            self._need(ident, "segment:run")
            if "demo" in body:
                if body["demo"] not in DEMO:
                    raise invalid("Demonstration series are: walk, sensor.", "invalid_request")
                out = segmentation(acct, f"demo/{body['demo']}", "standard", DEMO[body["demo"]], False, self._raw)
                out["usage"] = {"samples_billed": 0, "cost_usd": 0.0}
                return 200, out, None
            self._live(ident)
            series = self._series(body)
            unit = body.get("time_unit", "ms")
            bars = check_bars(to_ms(body["bars"], unit)) if "bars" in body \
                else bars_from_samples(to_ms(body.get("samples"), unit))
            out = segmentation(acct, series, body.get("profile"), bars, bool(body.get("return_edge")), self._raw)
            out["time_unit"] = unit
            return 200, times_out(out, unit), None
        if m == "POST" and p == "/v1/segmentations/extend":
            self._need(ident, "segment:run")
            self._live(ident)
            return 200, extension(acct, body), None
        if m == "POST" and p == "/v1/segmentations/extend/batch":
            self._need(ident, "segment:run")
            self._live(ident)
            items = body.get("items")
            if not isinstance(items, list) or not 0 < len(items) <= 1000:
                raise invalid("`items` holds 1 to 1000 extensions.", "invalid_request")
            results = []
            for item in items:
                try:
                    results.append({"status": 200, "result": extension(acct, item, body.get("time_unit", "ms"))})
                except ApiError as e:
                    results.append({"status": e.status, "error": e.body()})
            return 200, {"object": "extension_batch", "results": results}, None
        if m == "POST" and p == "/v1/segmentations/jobs":
            self._need(ident, "segment:run")
            self._live(ident)
            return self._job(ident, body)
        if m == "GET" and (mm := re.fullmatch(r"/v1/segmentations/jobs/(job_\w+)", p)):
            self._need(ident, "segment:read")
            job = STATE["jobs"].get(mm.group(1))
            if not job:
                raise ApiError(404, "not_found_error", "not_found", "No such job.")
            return 200, job, None
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
            return 200, {"object": "account", "id": acct, "tier": "evaluation", "balance_usd": 20.0,
                         "terms_accepted_at": iso(0), **STATE["account"]}, None
        if m == "POST" and p == "/v1/account/webhook_secret":
            self._need(ident, "keys:manage")
            return 201, {"object": "webhook_secret", "secret": "whsec_" + base64.b64encode(os.urandom(32)).decode(),
                         "note": "The mock does not sign with this; set PATTERNODE_MOCK_WEBHOOK_SECRET."}, None
        raise ApiError(404, "not_found_error", "not_found", f"No route {m} {p} in the mock.")

    def _series(self, body: dict) -> str:
        s = body.get("series")
        if not isinstance(s, str) or not 0 < len(s) <= 200:
            raise invalid("`series` is required, at most 200 characters.", "invalid_request")
        return s

    def _bucket(self, method: str, key: str):
        if method == "PUT":
            data = self.rfile.read(int(self.headers.get("content-length") or 0))
            with LOCK:
                STATE["bucket"][key] = data
            return self._send(200, None, raw=b"")
        if method == "GET" and key in STATE["bucket"]:
            return self._send(200, None, raw=STATE["bucket"][key])
        return self._send(404, None, raw=b"")

    def _job(self, ident: dict, body: dict):
        series = self._series(body)
        for f in ("source_url", "result_url"):
            if not isinstance(body.get(f), str) or not body[f].startswith(("https://", "http://127.0.0.1", "http://localhost")):
                raise invalid(f"`{f}` must be an https link to your storage.", "invalid_request")
        if body.get("format") not in ("csv", "jsonl", "parquet", "arrow"):
            raise invalid("`format` is csv, jsonl, parquet or arrow.", "invalid_request")
        if body["format"] in ("parquet", "arrow"):
            raise invalid("The mock reads csv and jsonl only; the service reads all four.", "invalid_request")
        job = {"object": "segmentation_job", "id": new_id("job_"), "status": "running", "series": series,
               "created_at": iso(), "finished_at": None, "result_written": False, "usage": None, "error": None}
        STATE["jobs"][job["id"]] = job
        webhook = body.get("webhook_url") or STATE["account"]["webhook_url"]
        acct = ident["account"]

        def run():
            try:
                text = urllib.request.urlopen(body["source_url"], timeout=60).read().decode()
                rows = [json.loads(line) for line in text.splitlines() if line.strip()] if body["format"] == "jsonl" \
                    else [[float(x) for x in line.split(",")] for line in text.splitlines()[1:] if line.strip()]
                bars = check_bars(rows) if body.get("kind") == "bars" else bars_from_samples(rows)
                result = segmentation(acct, series, body.get("profile"), bars, bool(body.get("return_edge")),
                                      json.dumps(body, sort_keys=True).encode())
                req = urllib.request.Request(body["result_url"], data=json.dumps(result).encode(), method="PUT",
                                             headers={"content-type": "application/json"})
                urllib.request.urlopen(req, timeout=60).read()
                job.update(status="succeeded", result_written=True, usage=result["usage"])
            except ApiError as e:
                job.update(status="failed", error=e.body()["error"])
            except Exception as e:
                job.update(status="failed", error={"type": "api_error", "message": f"The job failed: {e}. It was not charged.",
                                                   "details": {"error_code": "internal"}})
            job["finished_at"] = iso()
            if webhook:
                event = {"id": "evt_" + job["id"][4:], "type": f"segmentation.job.{job['status']}",
                         "created_at": iso(), "data": dict(job)}
                deliver(webhook, event, f"msg_{job['id']}")

        threading.Timer(0.2, run).start()
        return 202, job, {"location": f"/v1/segmentations/jobs/{job['id']}"}


def serve(port: int | None = None) -> ThreadingHTTPServer:
    port = port if port is not None else int(os.environ.get("PATTERNODE_MOCK_PORT", "4010"))
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    srv = serve()
    print(f"Patternode mock on http://127.0.0.1:{srv.server_address[1]} (FAKE segments; keeps no series)")
    srv.serve_forever()
