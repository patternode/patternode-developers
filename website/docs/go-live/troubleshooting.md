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
| 409 `edge_mismatch` | The edge sent belongs to another series or profile version | Read the edge for this series from your store; keep one writer per series |
| 400 `edge_invalid` | The edge was changed, truncated or re-encoded on its way through your store | Store it as an opaque string, exactly as received |
| 409 `out_of_order` | A late bar, or an edge older than the bars (a second writer moved on) | Drop the bar, or read the latest edge; nothing was applied |
| A failed job with `storage_unreachable` | Patternode could not read `source_url` or write `result_url`: the link expired, its signature does not cover a GET or PUT, or the bucket refused it. The job was not charged | Sign the links for at least an hour, the GET for the file and the PUT for the result, and run the job again |
| 429 `rate_limited` that does not clear | Sustained traffic over your plan | Smooth to the rate in `ratelimit-policy`, or ask for capacity |
| 429 `enforced_spend_limit_reached` | The plan's monthly cap | Waiting does not clear it: move up a plan |
| Webhooks rejected after a rotation | The receiver holds only the new secret | Keep the previous one too, until the next rotation |
| Duplicate events | Normal: delivery is at least once | Deduplicate by `id` |
| Segments differ between staging and production | Different profile versions | Pin the version on both |
| p99 above the service level from your side, but `server-timing` is small | The network between you and the edge | Move callers to the jurisdiction's region, or connect privately |

Still stuck: open a case with the `request-id`, the time in UTC, the jurisdiction and the transport ([Support](../service/support.md)).
