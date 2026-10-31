"""Key management with an admin key: the commands the onboarding playbook runs in stage 4.

    export PATTERNODE_API_KEY=pnk_admin_...
    python examples/python/keys.py list
    python examples/python/keys.py create-admin --name ops-admin
    python examples/python/keys.py create-live --name ingest-prod --scopes full --expires-in-days 90
    python examples/python/keys.py disable key_...      # reversible
    python examples/python/keys.py delete key_...       # permanent; a key cannot delete itself
    python examples/python/keys.py webhook-secret       # prints {"current": ..., "previous": ...}
    python examples/python/keys.py set-webhook https://...

A created key or secret is printed once, to stdout and nothing else, so it can be piped
straight into a secret store. Everything else goes to stderr.
"""

import argparse
import json
import sys

from patternode_client import Patternode


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    for kind in ("admin", "live", "test"):
        c = sub.add_parser(f"create-{kind}")
        c.add_argument("--name", required=True)
        c.add_argument("--expires-in-days", type=int, choices=(1, 7, 30, 90))
        if kind != "admin":
            c.add_argument("--scopes", default="full", help="full, read-only, stream-only, or a comma list")
            c.add_argument("--monthly-usd", type=float)
    for verb in ("disable", "enable", "delete"):
        sub.add_parser(verb).add_argument("key_id")
    sub.add_parser("webhook-secret").add_argument("--previous", help="the secret it replaces, kept for the overlap")
    sub.add_parser("set-webhook").add_argument("url")
    a = p.parse_args(argv)
    pn = Patternode()

    if a.cmd == "list":
        for k in pn.get("/v1/keys")["data"]:
            print(f"{k['id']:<20} {k['kind']:<6} {k['status']:<9} {k.get('name') or '':<20} {k.get('hint', '')}",
                  file=sys.stderr)
    elif a.cmd.startswith("create-"):
        kind = a.cmd.split("-", 1)[1]
        body = {"kind": kind, "name": a.name}
        if a.expires_in_days:
            body["expires_in_days"] = a.expires_in_days
        if kind != "admin":
            body["scopes"] = a.scopes if a.scopes in ("full", "read-only", "stream-only") else a.scopes.split(",")
            if a.monthly_usd is not None:
                body["limits"] = {"monthly_usd": a.monthly_usd}
        k = pn.post("/v1/keys", body)
        print(f"created {k['id']} ({k['kind']}, {', '.join(k['scopes'])}); shown once, store it now", file=sys.stderr)
        print(k["key"])
    elif a.cmd in ("disable", "enable"):
        k = pn.post(f"/v1/keys/{a.key_id}/{a.cmd}")
        print(f"{k['id']} {k['status']}", file=sys.stderr)
    elif a.cmd == "delete":
        k = pn.delete(f"/v1/keys/{a.key_id}")
        print(f"{k['id']} {k['status']}", file=sys.stderr)
    elif a.cmd == "webhook-secret":
        s = pn.post("/v1/account/webhook_secret")
        print("new webhook secret; deliveries carry both signatures until the next rotation", file=sys.stderr)
        print(json.dumps({"current": s["secret"], "previous": a.previous}))
    elif a.cmd == "set-webhook":
        acct = pn.patch("/v1/account", {"webhook_url": a.url})
        print(f"webhook_url = {acct['webhook_url']}", file=sys.stderr)


if __name__ == "__main__":
    main()
