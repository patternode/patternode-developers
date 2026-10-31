---
title: Production checklist
sidebar_position: 1
description: Every line to tick before production traffic, grouped by area, with what each plan needs.
---

# Production checklist

PC = Production. MC = Mission Critical and Dedicated. A line marked for PC applies to MC as well.

## Credentials

| | Check | Plan |
|---|---|---|
| ☐ | The delivered admin keys are deleted; your own are in a password manager held by both technical contacts | PC |
| ☐ | Each workload and environment has its own live key (or OAuth client), narrowest scopes, expiry at most 90 days | PC |
| ☐ | Keys are read from a secret store at start; none is in code, images, CI logs or tickets | PC |
| ☐ | Secret scanning has the key pattern | PC |
| ☐ | An IP allow list on each production key, or private connectivity only | MC |
| ☐ | OAuth with `private_key_jwt` or mutual TLS, if your policy needs no long-lived secret | MC |

## Client

| | Check | Plan |
|---|---|---|
| ☐ | Every write sends `x-amz-content-sha256` and every POST an `Idempotency-Key`, the same on each retry | PC |
| ☐ | Retries: 429, 5xx and network errors, backoff with jitter, `retry-after` honoured; other 4xx never retried unchanged | PC |
| ☐ | Error handling branches on `error_code`, and tolerates unknown codes, fields and event types | PC |
| ☐ | Sequences assigned per stream and the last acknowledged one persisted; resume after restart tested | PC |
| ☐ | The jurisdiction endpoint is used, never a regional address | PC |
| ☐ | `traceparent` sent; `server-timing` recorded | PC |
| ☐ | Profile versions pinned where results must reproduce | PC |
| ☐ | gRPC streams and subscriptions reconnect on `GOAWAY` or reset and resume by sequence or event id | MC |
| ☐ | Callers run in two regions | MC |

## Events

| | Check | Plan |
|---|---|---|
| ☐ | Signatures verified on the raw body; stale timestamps rejected; `id` deduplicated | PC |
| ☐ | 2xx returned within 10 seconds; work done from a queue with a dead-letter queue | PC |
| ☐ | Webhook secret rotation tested with both secrets live | PC |
| ☐ | Subscription consumers acknowledge and resume; `lag` messages alert | MC |

## Data

| | Check | Plan |
|---|---|---|
| ☐ | Series names are opaque; the mapping is in your store only | PC |
| ☐ | Segments stored by client prefix; deleting a client deletes its prefix | PC |
| ☐ | Jurisdiction matches where your data must stay | PC |
| ☐ | Customer-managed encryption key configured, if your policy needs one | MC |

## Capacity and proof

| | Check | Plan |
|---|---|---|
| ☐ | Peak bars a second, open streams and backfill volume within the plan, or extra capacity confirmed | PC |
| ☐ | Load and soak tests passed (playbook stage 8) | PC |
| ☐ | Failover rehearsal passed | MC |

## Operations

| | Check | Plan |
|---|---|---|
| ☐ | Alerts on success rate, p99, 429 rate, sequence gaps, event lag and dead-letter depth, routed to on-call | PC |
| ☐ | On-call subscribed to `status.patternode.com` | PC |
| ☐ | Runbooks written and found by on-call (playbook stage 9) | PC |
| ☐ | Technical contacts can open Severity 1 by phone | MC |
| ☐ | Blackout periods registered | MC |
| ☐ | Exit plan written | MC |
