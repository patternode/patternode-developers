---
title: The service contract
sidebar_position: 0
description: What Patternode provides and what it needs from you, specified for real-time utility operations and high-volume quantitative trading.
---

# The service contract

This section specifies the Patternode service: the plans, the service levels, how it stays up, how real-time traffic moves, how it is secured, and how it is supported. It is written for the hardest users the service is built for:

| Grade | Typical user | What it demands |
|---|---|---|
| Utility operations | A control room or monitoring product on SCADA, historian and meter data for a grid, a water network or a generation fleet | Always on through storms and failovers; every bar accounted for; data kept in its jurisdiction; operational technology boundaries respected; audit trails for regulators |
| Quantitative trading | A fund or trading desk segmenting tick and bar data across thousands of instruments, live and in backtest | Low and predictable tail latency; very high throughput; nanosecond timestamps; deterministic, reproducible results; no change during market hours |

## How to read it

The key words MUST, MUST NOT, SHOULD and MAY are used as in RFC 2119 and RFC 8174. "Patternode MUST" is a commitment by Patternode; "you MUST" is a condition of the commitment.

The numbers on these pages are the service's specification. They bind when your order form names your plan: the order form, and the service level agreement it incorporates, is the contract, and these pages are its technical schedule. Where an order form agrees different numbers (a Dedicated plan, for example), the order form wins.

## The pages

| Page | Specifies |
|---|---|
| [Plans](plans.md) | The four plans, what each guarantees, and which grade each serves |
| [Service levels](service-levels.md) | Availability, latency, throughput, durability, freshness and how each is measured; credits |
| [Resilience](resilience.md) | Jurisdictions and regions, failover, recovery objectives, degradation, change control, testing, exit |
| [Real-time](realtime.md) | Transports (REST, gRPC streams, WebSocket subscriptions, event buses), ordering, exactly-once effect, backpressure, time precision, determinism |
| [Security](security.md) | Authentication, private connectivity, encryption, keys you manage, audit |
| [Compliance](compliance.md) | Assurance reports, and how the service maps to the rules utilities and funds work under |
| [Support](support.md) | Severities, response times, incident communication, status |
| [Shared responsibility](shared-responsibility.md) | What is yours, what is Patternode's |
