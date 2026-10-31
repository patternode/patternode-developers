---
title: Service levels
sidebar_position: 2
description: The service level objectives, how each is measured, the error budget and service credits.
---

# Service levels

## Objectives

| Indicator | Production | Mission Critical | Dedicated | Measured |
|---|---|---|---|---|
| Availability | 99.9% | 99.99% | 99.99% (99.995% by agreement) | Valid requests answered without a 5xx or a timeout, over all minutes of the calendar month, per jurisdiction |
| Extension latency, REST | p99 50 ms | p50 10 ms, p99 40 ms | By agreement | From the last byte received at Patternode's edge to the first byte of the answer |
| Extension latency, gRPC | | p50 2 ms, p99 10 ms, p99.9 25 ms | p99 5 ms, by agreement | From a request received to its answer on the stream, at the edge |
| Finished series, inline | p99 2 s for up to 100,000 bars | p99 1 s for up to 100,000 bars | By agreement | Edge to edge |
| Job start | p99 60 s | p99 15 s | p99 15 s | From 202 to `running` |
| Job throughput | 10 million bars a minute per account | 50 million | Sized together | Bars processed across running jobs |
| Event freshness, webhook | p99 30 s | p99 5 s | p99 5 s | From the event to the first delivery attempt |
| Event delivery | At least once, retried for 24 hours | At least once, retried for 72 hours | As Mission Critical | |
| Your series' data held | None: every answer is complete, and edges are yours | None | None | |

Latency is measured at the edge so that it excludes the network between you and Patternode, which is yours to choose: put your caller in the same cloud region as your jurisdiction's endpoint, or use private connectivity.

## What counts as unavailable

A minute is unavailable when more than 1% of valid requests in it fail with a 5xx, time out (30 seconds for REST, 5 seconds for a gRPC answer), or a gRPC connection is reset without a `GOAWAY`. These do not count: 4xx answers, including 429 within your plan's throughput; scheduled maintenance announced as the plan requires (none on Mission Critical and Dedicated, which are maintained without downtime); failures caused by your network or your cloud provider's network outside Patternode's edge; and preview or planned routes.

## Your view of the indicators

- `GET /v1/service_levels` returns your account's indicators for the current and the last 12 months, per jurisdiction, as Patternode measures them.
- Every response carries `request-id` and, when you send W3C `traceparent`, continues your trace, so your own monitoring sees Patternode's share of each request's time in `server-timing`.
- `GET /v1/status` returns this month's availability so far, with the components that serve you and any incident touching them.
- The status page, `status.patternode.com`, shows every component, incidents and maintenance, with an Atom and RSS feed, a status API with no key, and `status.*` events on your webhook endpoint ([Service status](status.mdx)).

## Error budget and change

Each month's error budget is what the availability objective allows: 43 minutes at 99.9%, 4 minutes 19 seconds at 99.99%. When a jurisdiction has spent its budget, Patternode MUST stop releasing to it anything but fixes until the budget recovers.

## Service credits

| Monthly availability | Production | Mission Critical, Dedicated |
|---|---|---|
| Below the objective | 10% of the month's fees | 10% |
| Below 99.0% (Production) or 99.9% (Mission Critical) | 25% | 25% |
| Below 95.0% (Production) or 99.0% (Mission Critical) | 50% | 50% |

Credits are claimed within 30 days of the month's end, by a technical contact, with the request ids or times affected. The order form may agree others.
