---
title: Real-time
sidebar_position: 4
description: Nothing kept between calls, transports, batching, ordering, exactly-once effect, backpressure, time precision and determinism.
---

# Real-time

## Nothing is kept

Patternode keeps none of your series between calls: no copies, no checkpoints, no results. Every answer is complete in itself, and a forming series' state travels with you as its sealed edge ([Forming series](../guides/forming-series.mdx)). So any region can answer any call, a failover loses nothing, and there is no session to reconnect.

## Transports

Every transport carries the same operations with the same semantics. REST works on every plan; the others are faster ways to do the same thing.

| Transport | For | Plans | Contract |
|---|---|---|---|
| REST, JSON over HTTPS | Everything; the reference | All | `specs/openapi.yaml` |
| Batched REST extensions | Many series, one request: up to 1,000 items, each with its own edge | All | `POST /v1/segmentations/extend/batch` |
| gRPC bidirectional stream | Sustained high-rate extensions with low tail latency; one connection carries many series | Mission Critical, Dedicated | `specs/proto/patternode/delve/v1/delve.proto` |
| Webhooks | Job and account events to an HTTPS endpoint | Production and above | `specs/asyncapi.yaml` |
| Event buses: Amazon EventBridge, Kafka | The same events into your own bus, as CloudEvents 1.0 | Mission Critical, Dedicated | `specs/asyncapi.yaml` |
| Bulk files: CSV, JSON Lines, Apache Parquet, Apache Arrow IPC | Backfills and backtests, read from and written to your storage | All | `POST /v1/segmentations/jobs` |

HTTP/2 is used for REST and gRPC; keep connections open and reuse them.

## Ordering

- A series' order is in its edge. The next bars must open after `edge_last_close_time`; an earlier bar is refused with 409 `out_of_order`, and nothing is applied.
- One writer per series. Two writers extending from the same edge would fork it; keep the first write with a version check in your store.
- Across series there is no order.

## Exactly-once effect, without server state

The same edge with the same bars always gives the same answer, so a retry can never apply a bar twice: resend exactly what you sent. Store the closed segments, the right edge and the new edge in one write, and your store moves forward exactly once per answer. Other writes (keys, account settings) are applied once by `Idempotency-Key`; for 24 hours Patternode keeps the key and a hash of the request, never its data, so a retry is not billed twice. Events are delivered at least once; each has a stable `id`.

## Backpressure

| Signal | Means | Do |
|---|---|---|
| `ratelimit` header falling | You are approaching the plan's rate | Smooth your sending |
| 429 with `retry-after` | Over the rate | Wait, then resend unchanged |
| gRPC flow control and `RESOURCE_EXHAUSTED` with retry info | The same, on a stream | The client library waits |

## Time

Times are integers since the Unix epoch, UTC, in the unit you choose per request with `time_unit`: `ms` (the default), `us` or `ns`. In JSON, `us` and `ns` times are sent and returned as strings, because JSON numbers lose precision past 2^53; on gRPC and in Parquet and Arrow they are 64-bit integers. Segments are returned in the unit you sent. Patternode does not move your times: there is no rounding, clock adjustment or time zone.

Patternode's own timestamps (`created_at`, event times, audit logs) come from clocks synchronised to UTC within 100 microseconds, and carry microseconds.

## Determinism

The same bars with the same profile version give the same segments, bit for bit, on every transport, in every region, at any time. A profile is named with its version, `standard@2026-11`; a bare `standard` means the version current when you called (or, with an edge, the version sealed in it), and the answer names the version used. A profile version is never changed; new behaviour is a new version, announced in the changelog, and old versions are served for at least 24 months. Pin the version for backtests and audits.
