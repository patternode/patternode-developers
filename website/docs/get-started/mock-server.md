---
title: The mock server
sidebar_position: 4
description: A local stand-in for the Patternode API, for development, tests and CI. Fake segments, real shapes and real checks.
---

# The mock server

`mock/mock_patternode.py` is a stand-in for the Patternode API: one file, Python 3.10 or newer, standard library only.

```bash
python mock/mock_patternode.py                      # http://127.0.0.1:4010
PATTERNODE_MOCK_PORT=5000 python mock/mock_patternode.py
```

| It does as production does | It does differently |
|---|---|
| Refuses a key of the wrong shape (401), a write without `x-amz-content-sha256` (400) or with the wrong hash (403) | Accepts any key of the right shape |
| Refuses a test key on your own series (403 `test_key_demo_only`) | Never bills; reports a nominal `usage` |
| Checks bars: order, high and low, values above zero, with `problems` listing each bad bar | Its segments are fake: every four children make a parent |
| Refuses a bar before the edge (409), an edge from another series (409) and a changed edge (400) | Its edge is signed but readable; the service's is also encrypted |
| Keeps nothing of your series; refuses an `Idempotency-Key` reused with another body (422) | Does not rate limit; keeps keys and jobs in memory only |
| Runs jobs from links to your storage, and signs job webhooks to Standard Webhooks | Serves a stand-in for your storage at `/_bucket/`; reads CSV and JSON Lines only; signs only when `PATTERNODE_MOCK_WEBHOOK_SECRET` is set |

Use it to test your code's handling of the contract, never its handling of real segments: the shapes are right, the values mean nothing.

## In your CI

```yaml
- run: python mock/mock_patternode.py &
- run: sleep 1 && your-test-command
  env:
    PATTERNODE_BASE_URL: http://127.0.0.1:4010
    PATTERNODE_API_KEY: pnk_live_BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
```

The mock is fake, so the key in this snippet is fake too, and safe to commit. A real key never is.
