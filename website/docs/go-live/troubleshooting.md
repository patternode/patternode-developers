---
title: Troubleshooting
sidebar_position: 2
description: Symptoms, causes and fixes for the problems integrations meet most.
---

# Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| 401 `missing_api_key` on every call | Key not sent, or `Bearer` with two spaces, or the key truncated | Send `Authorization: Bearer <key>` with one space; check the secret store value has no newline |
| 400 `missing_content_sha256` | A write without the hash | Hash the exact body bytes you send |
| 403 not in the error shape | The hash does not match the body | Hash after serialising, and send those bytes unchanged; check no middleware re-encodes the body |
| 403 `test_key_demo_only` | A test key on your own series | Use a live key |
| 403 `terms_not_accepted` | A new account | Accept the terms through the order form or the first credit purchase |
| 400 `invalid_series` | A bar out of order, high below low, a value at or below zero | Read `problems`: each names a bar and why. For values at zero, add an offset |
| 409 `sequence_gap` | A bar was lost between your queue and the call, or two writers share a stream | Resend from `expected_sequence`; keep one writer per stream |
| 409 `out_of_order` | A late bar | Drop it or rebuild the window as a finished series; nothing was applied |
| 429 `rate_limited` that does not clear | Sustained traffic over your plan | Smooth to the rate in `ratelimit-policy`, or ask for capacity |
| 429 `enforced_spend_limit_reached` | The plan's monthly cap | Waiting does not clear it: move up a plan |
| Webhooks rejected after a rotation | The receiver holds only the new secret | Keep the previous one too, until the next rotation |
| Duplicate events | Normal: delivery is at least once | Deduplicate by `id` |
| Segments differ between staging and production | Different profile versions | Pin the version on both |
| p99 above the service level from your side, but `server-timing` is small | The network between you and the edge | Move callers to the jurisdiction's region, or connect privately |

Still stuck: open a case with the `request-id`, the time in UTC, the jurisdiction and the transport ([Support](../service/support.md)).
