---
title: Requests, errors and limits
sidebar_position: 5
description: Authentication, the body hash on writes, idempotency, the error shape, rate limits and retries.
---

# Requests, errors and limits

## Authentication

Send the key as `Authorization: Bearer <key>`, with one space after `Bearer`, or as `x-api-key: <key>`. A request to `/v1/` whose key has the wrong prefix or length is refused before anything runs (401 `missing_api_key`).

## Writes carry the body's SHA-256

Every `POST`, `PUT` and `PATCH` to `/v1/` sends the SHA-256 of the exact body bytes, lowercase hex, in `x-amz-content-sha256`. With no body, send the hash of the empty string, `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Hash the bytes you send, not a re-serialisation of them.

| Without it | With the wrong hash |
|---|---|
| 400 `missing_content_sha256`, from the edge | 403, from the edge, not in the API's error shape |

## Idempotency

Send `Idempotency-Key` on every `POST`, a fresh UUID per operation and the same one on every retry of it. For 24 hours Patternode keeps the key and a hash of the request, never its data: a repeat is not billed twice, and the same key with a different body is 422 `idempotency_conflict`. Segmentations are recomputed on a repeat, and give the same answer, because they are deterministic.

## Every response

`request-id` is on every response. Quote it to support.

## Errors

```json
{ "type": "error",
  "error": { "type": "invalid_request_error", "message": "...",
             "details": { "error_code": "invalid_series", "problems": [{ "index": 3, "problem": "times_not_increasing" }] } },
  "request_id": "req_..." }
```

Branch on `error.details.error_code`; the message is for people and may change.

| Status | `error.type` | `error_code` | Do |
|---|---|---|---|
| 400 | `invalid_request_error` | `invalid_series` (with `problems`), `body_too_large`, `missing_content_sha256` | Fix the request. For `body_too_large`, run a job from your storage |
| 401 | `authentication_error` | `missing_api_key`, `invalid_api_key`, `key_disabled`, `key_expired` | Check the secret store; rotate |
| 402 | `billing_error` | `credit_balance_too_low` | Add credit, or turn on auto-reload |
| 403 | `permission_error` | `missing_scope`, `test_key_demo_only`, `terms_not_accepted` | Use the right key |
| 404 | `not_found_error` | `not_found` | |
| 400 | `invalid_request_error` | `edge_invalid` | The edge was changed or is not Patternode's: use the one you stored |
| 409 | `conflict_error` | `out_of_order`, `edge_mismatch` | A bar before the edge's last close, or an edge from another series or profile version. Nothing was applied |
| 422 | `invalid_request_error` | `idempotency_conflict` | A new operation needs a new key |
| 429 | `rate_limit_error` | `rate_limited`, `enforced_spend_limit_reached`, `customer_spend_limit_reached` | Wait for `retry-after`. Spend limits do not clear by waiting: raise the limit |
| 503 | `overloaded_error` | `service_capacity` | Wait for `retry-after` |
| 5xx | `api_error` | `internal` | Retry with backoff |

## Rate limits

Each response carries `ratelimit-policy` and `ratelimit` (IETF RateLimit headers), so your client can slow down before it is refused. Limits are per account and per key: requests a minute, samples a minute and concurrent jobs, set by your plan. Your onboarding pack gives your tier's numbers.

## Retries

Retry 429, 503 and other 5xx, and network errors, with exponential backoff and jitter, honouring `retry-after`, and with the same `Idempotency-Key`. Never retry other 4xx unchanged. The example clients do this.
