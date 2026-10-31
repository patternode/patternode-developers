---
title: Resilience
sidebar_position: 3
description: Jurisdictions and regions, failover, recovery objectives, degraded modes, change control, resilience testing and exit.
---

# Resilience

## Jurisdictions

Your data stays in the jurisdiction you choose. A jurisdiction is two cloud regions inside it, far enough apart that one event does not take both.

| Jurisdiction | Endpoint | Regions |
|---|---|---|
| Australia and New Zealand | `anz.api.patternode.com` | Two, in Australia and New Zealand |
| European Union | `eu.api.patternode.com` | Two, in the EU |
| United States | `us.api.patternode.com` | Two, on the east coast and in the centre |
| Any | `api.patternode.com` | Routes to your account's home jurisdiction |

Patternode MUST NOT store, process or replicate your series, segments, checkpoints or backups outside your jurisdiction. Support staff outside it MAY see metadata (request ids, counts, error codes), never series.

## How it stays up

| Plan | Within a region | Across regions |
|---|---|---|
| Production | Three zones; losing one zone is invisible to you | Backups in the second region; restored within 4 hours |
| Mission Critical, Dedicated | Three zones, as Production | Active-active: both regions serve your account all the time, each stream has a home region, and its checkpoint is replicated to the other within 1 second |

Your traffic runs in a cell: a slice of the service with its own capacity, so another account's surge cannot use yours. Dedicated cells serve one account.

## What you see in a failover

| Event | REST | gRPC stream | Webhooks and subscriptions |
|---|---|---|---|
| A zone fails | Nothing | Nothing, or a reconnect | Nothing |
| A region fails (Mission Critical, Dedicated) | Requests to the jurisdiction endpoint move to the other region within 60 seconds; requests in flight may fail with 503 and are safe to retry with their `Idempotency-Key` | The stream gets `GOAWAY` or resets; reconnect, and resume from the `last_sequence` the server reports. Nothing acknowledged is lost | Deliveries pause and resume from the other region; nothing is lost, duplicates are possible |
| A region is degraded but up | Patternode MAY drain it; you see the same as a failover, without errors | | |

You MUST make your client follow these: retry with backoff and the same idempotency key, reconnect streams and resume by sequence, and deduplicate events by id. The example clients do.

## Degraded modes

If a dependency fails, the service sheds what it can and keeps what matters most, in this order:

1. Appends to open streams, and their acknowledgements.
2. Event delivery to subscriptions and webhooks.
3. Finished series answered inline.
4. Jobs. Queued jobs wait; none is lost.
5. Reports and account changes.

## Recovery objectives

| | Production | Mission Critical, Dedicated |
|---|---|---|
| Recovery point, acknowledged appends, zone loss | 0 | 0 |
| Recovery point, acknowledged appends, region loss | 5 minutes | 1 second |
| Recovery time, region loss | 4 hours | 60 seconds |
| Recovery time, loss of a jurisdiction's both regions | Best effort | 24 hours, from backups in the same jurisdiction |

## Change control

| | Production | Mission Critical, Dedicated |
|---|---|---|
| Releases | Progressive: a cell at a time, watched, rolled back automatically on regression | The same, and never during your blackout periods |
| Blackout periods | None | You set them: for example the trading hours of your venues, or a storm or emergency declared by your operator. Patternode MUST NOT release to your cells inside them, except to fix a Severity 1 |
| Notice of change to the platform | Changelog | 5 business days, by email, for anything beyond a fix |
| Engine versions | Fixed per profile version ([Determinism](realtime.md#determinism)) | The same |

## Testing

Patternode MUST, every quarter, fail a region of each Mission Critical jurisdiction in production and publish the result to Mission Critical and Dedicated customers. Dedicated customers MAY take part, and MAY run their own resilience tests against their cells with 10 business days' notice.

## Exit

You can leave at any time with everything that is yours:

- Segments are already in your store; nothing of a finished series stays at Patternode.
- `GET /v1/streams` and `GET /v1/streams/{id}` export every open stream's right edge, so a stream can be rebuilt from your bars elsewhere.
- Usage and audit logs export as files.
- Mission Critical and Dedicated customers get an exit plan in the order form, and Dedicated customers a tested one, with transition support for 6 months.
