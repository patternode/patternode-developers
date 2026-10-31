---
title: Plans
sidebar_position: 1
description: Evaluation, Production, Mission Critical and Dedicated, and what each guarantees.
---

# Plans

One functional contract, four plans. Every plan runs the same API: the same routes, fields, errors, events and semantics, on REST. A plan changes only how much you can send, the service levels Patternode commits to, and which faster transports are switched on for you. So code written against the Evaluation plan runs unchanged on Dedicated, and moving up a plan is a change to your order form, not to your code.

## Open for orders

| Plan | State |
|---|---|
| Evaluation | Open |
| Production | Open |
| Mission Critical | By arrangement: ask, and Patternode confirms the jurisdiction and a start date |
| Dedicated | By arrangement: sized and scheduled together |

A plan's service levels start on the date its order form names. Until a jurisdiction is open for a plan, that plan is not sold there.

## What each plan provides

| | Evaluation | Production | Mission Critical | Dedicated |
|---|---|---|---|---|
| For | Building and testing | Products where an outage is an inconvenience | Real-time operations and live trading | The largest utilities and funds; regulated outsourcing |
| Monthly availability | None | 99.9% | 99.99% | 99.99%, or 99.995% by agreement |
| Deployment | Shared | Shared, multi-zone, one region | Shared cells, active-active across two regions of your jurisdiction | Single-tenant cells, active-active across two regions, in your jurisdiction |
| Transports | REST | REST, webhooks | REST, gRPC, webhooks, event buses | As Mission Critical |
| Throughput (bars a second, sustained, per account) | 100 | 5,000 | 100,000 | 1,000,000 or more, sized together |
| Append latency, p99, at the edge | None | 50 ms (REST) | 10 ms (gRPC), 40 ms (REST) | 5 ms (gRPC), by agreement |
| Your series' data held by Patternode | None | None | None | None |
| Recovery time (regional loss) | None | 4 hours | 60 seconds | 60 seconds |
| Private connectivity | No | No | AWS PrivateLink, Azure Private Link, Google Private Service Connect | As Mission Critical, plus dedicated interconnect |
| Customer-managed encryption keys | No | No | Yes | Yes |
| Change windows | None | Announced 5 days ahead | Agreed blackout periods (market hours, storm declarations) | Agreed blackout periods, with your change board |
| Support | Community | Business hours; Severity 1 in 4 hours | 24x7; Severity 1 in 15 minutes | 24x7; named engineers; Severity 1 in 15 minutes |
| Service credits | No | Yes | Yes | Yes, as agreed |
| Exit assistance | No | Data export | Data export, exit plan | Data export, tested exit plan, transition support |

The throughput figures are what the plan is provisioned for, without asking. Patternode enforces them with the quotas every response reports in `ratelimit-policy` and `ratelimit`, so you can see your headroom before you reach it. Above them, tell Patternode 10 business days ahead and the capacity is added; the service does not refuse traffic within twice the figure while that happens, it slows it with `429` and `retry-after`.

## Which plan for which grade

| Grade | Plan | Why |
|---|---|---|
| A monitoring product for utilities, used by engineers in office hours | Production | Outages delay analysis, not operations |
| A control room tool used in real-time operations | Mission Critical | Recovery in a minute, private connectivity, blackout periods during storms |
| A transmission operator, a large water utility, or anything inside a regulated outsourcing regime | Dedicated | Single tenancy, your change board, a tested exit plan |
| A research team running backtests | Production, with jobs | Throughput, not tail latency |
| A live trading desk | Mission Critical | gRPC, 10 ms p99, no change during market hours |
| A fund at full scale, or one whose regulator treats Patternode as a critical third party | Dedicated | Sized throughput, 5 ms p99, exit plan, your audit rights |
