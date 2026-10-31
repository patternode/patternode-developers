---
title: Operations and compliance
sidebar_position: 4
description: Placement, capacity, blackout periods, resilience, support and the regulatory terms a fund needs, in one place.
---

# Operations and compliance

## Placement and plan

| Platform | Plan | Placement |
|---|---|---|
| Research | Production | Any region of your jurisdiction; jobs need only links to your storage |
| Live | Mission Critical | Your live platform in the jurisdiction's cloud region, two regions if your own availability needs it; private connectivity |
| Live at full scale, or under critical third-party oversight | Dedicated | As Mission Critical, with cells for you alone and your change board |

## Capacity

Size for the open and the close, when every instrument closes a bar at once: instruments × bars a second at that moment. Compare with your plan's bars a second ([Plans](../../service/plans.md)); tell Patternode 10 business days ahead to go beyond it. Research jobs are bounded by concurrent jobs, not by rate.

## Blackout periods

Register your venues' trading hours (and any other window, such as an index rebalance) as blackout periods. Patternode releases nothing to your cells inside them except a Severity 1 fix, and runs its quarterly regional failover tests outside them.

## Resilience

Patternode holds none of your state, so its failures cannot lose your data, and either region answers any call. Your platform's resilience is yours: edges in a durable store, extenders that restart from it, and callers in two regions if you need them. See [Deployment and resilience](../deployment.md).

## Regulation

| Regime | What Patternode gives you |
|---|---|
| DORA (EU) | Article 30 terms in the order form: service levels, locations, access, audit, exit; incident notification on its timelines; resilience test results; subprocessor list |
| UK operational resilience and outsourcing | The same terms; recovery objectives you can use for impact tolerances |
| MiFID II RTS 25, SEC Rule 613 | Your nanosecond times kept exactly; Patternode's own clocks within 100 microseconds of UTC |
| Model risk (SR 11-7, PRA SS1/23) | Determinism per version; version documentation under NDA ([Reproducibility](reproducibility.md)) |
| Confidentiality of strategies | Patternode sees only bars under names you choose, and keeps none of them |

## Support

Mission Critical and Dedicated: 24x7, Severity 1 answered in 15 minutes by phone, a shared channel, and post-incident reports within 5 business days ([Support](../../service/support.md)).

Next: [Flows](flows.md).
