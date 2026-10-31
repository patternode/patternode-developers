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

Patternode keeps none of your series, segments or edges at all. It MUST NOT process them outside your jurisdiction. Support staff outside it MAY see metadata (request ids, counts, error codes), never series.

## How it stays up

Patternode keeps no series state, so every region and every instance can answer every call. Resilience is a matter of capacity and routing, not of moving state.

| Plan | Within a region | Across regions |
|---|---|---|
| Production | Three zones; losing one zone is invisible to you | A second region of the jurisdiction takes the traffic within 4 hours |
| Mission Critical, Dedicated | Three zones, as Production | Active-active: both regions serve your account all the time |

Your traffic runs in a cell: a slice of the service with its own capacity, so another account's surge cannot use yours. Dedicated cells serve one account.

## What you see in a failover

| Event | REST | gRPC stream | Webhooks and event buses |
|---|---|---|---|
| A zone fails | Nothing | Nothing, or a reconnect | Nothing |
| A region fails (Mission Critical, Dedicated) | Requests move to the other region within 60 seconds; requests in flight may fail with 503 and are safe to resend unchanged | The connection gets `GOAWAY` or resets; reconnect and resend the requests not answered | Deliveries pause and resume from the other region; duplicates are possible |
| A region is degraded but up | Patternode MAY drain it; you see the same as a failover, without errors | | |

You MUST make your client follow these: resend unanswered requests unchanged, with backoff; reconnect gRPC streams; deduplicate events by id. Because your edges are in your store, nothing about your series is lost in any failure of Patternode's. The example clients do this.

## Degraded modes

If a dependency fails, the service sheds what it can and keeps what matters most, in this order:

1. Extensions of forming series.
2. Finished series answered inline.
3. Event delivery.
4. Jobs. Queued jobs wait; none is lost.
5. Reports and account changes.

## Recovery objectives

| | Production | Mission Critical, Dedicated |
|---|---|---|
| Your series' data lost in any Patternode failure | None: Patternode holds none | None |
| Recovery time, region loss | 4 hours | 60 seconds |
| Recovery time, loss of a jurisdiction's both regions | Best effort | 24 hours |
| Account data (keys, settings, usage), recovery point | 5 minutes | 1 second |

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

- Your segments and edges are already in your store; Patternode holds nothing of your series.
- Usage and audit logs export as files.
- Mission Critical and Dedicated customers get an exit plan in the order form, and Dedicated customers a tested one, with transition support for 6 months.
