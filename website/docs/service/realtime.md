---
title: Real-time
sidebar_position: 4
description: Transports, batching, ordering, exactly-once effect, backpressure, time precision and determinism.
---

# Real-time

## Transports

Every transport carries the same operations with the same semantics. REST works on every plan; the others are faster ways to do the same thing.

| Transport | For | Plans | Contract |
|---|---|---|---|
| REST, JSON over HTTPS | Everything; the reference | All | `specs/openapi.yaml` |
| Batched REST appends | Many series, one request: up to 1,000 bars across any number of streams | All | `POST /v1/streams/observations` |
| gRPC bidirectional stream | Sustained high-rate appends with low tail latency; one connection carries many series | Mission Critical, Dedicated | `specs/proto/patternode/delve/v1/delve.proto` |
| WebSocket subscription | Events pushed as they happen, to a backend that holds a connection | Mission Critical, Dedicated | `specs/asyncapi.yaml`, channel `subscription` |
| Webhooks | Events to an HTTPS endpoint | Production and above | `specs/asyncapi.yaml`, channel `webhook` |
| Event buses: Amazon EventBridge, Kafka | Events into your own bus, without running a receiver | Mission Critical, Dedicated | The same events, as CloudEvents 1.0 |
| Bulk files: CSV, JSON Lines, Apache Parquet, Apache Arrow IPC | Backfills and backtests | All | `POST /v1/uploads` |

HTTP/2 is used for REST and gRPC; keep connections open and reuse them.

## Ordering and sequence

- Each stream has one sequence. Every append carries `sequence`, an integer you assign, starting at 1 and increasing by 1. The answer carries it back.
- Patternode applies a stream's bars in sequence order. A bar whose sequence is already applied is answered with the original answer and applied nothing (its effect is exactly once). A bar that skips a sequence is refused with 409 `sequence_gap`, naming `expected_sequence`; resend from there.
- Across streams there is no order. Events of one stream arrive in sequence order on a subscription; on webhooks and buses, order by `sequence`.

## Exactly-once effect

Appends are applied exactly once by stream and sequence. Other writes are applied exactly once by `Idempotency-Key` within 24 hours. Events are delivered at least once; each has a stable `id` and the stream's `sequence`, so you deduplicate.

## Backpressure

| Signal | Means | Do |
|---|---|---|
| `ratelimit` header falling | You are approaching the plan's rate | Smooth your sending |
| 429 with `retry-after` | Over the rate | Wait, then resend with the same sequence or key |
| gRPC flow control and `RESOURCE_EXHAUSTED` with retry info | The same, on a stream | The client library waits |
| Subscription `lag` message | Your consumer is behind; the server is buffering for you, up to 7 days | Catch up, or resume later from a sequence |

## Time

Times are integers since the Unix epoch, UTC, in the unit you choose per request with `time_unit`: `ms` (the default), `us` or `ns`. In JSON, `us` and `ns` times are sent and returned as strings, because JSON numbers lose precision past 2^53; on gRPC and in Parquet and Arrow they are 64-bit integers. Segments are returned in the unit you sent. Patternode does not move your times: there is no rounding, clock adjustment or time zone.

Patternode's own timestamps (`created_at`, event times, audit logs) come from clocks synchronised to UTC within 100 microseconds, and carry microseconds.

## Determinism

The same bars with the same profile version give the same segments, bit for bit, on every transport, in every region, at any time. A profile is named with its version, `standard@2026-11`; a bare `standard` means the version current when your stream opened, or for a finished series when you called, and the answer names the version used. A profile version is never changed; new behaviour is a new version, announced in the changelog, and old versions are served for at least 24 months. Pin the version for backtests and audits.
