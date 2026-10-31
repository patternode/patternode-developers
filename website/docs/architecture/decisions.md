---
title: Decisions you make
sidebar_position: 7
description: The architecture decisions a partner makes when integrating, with the options, the recommended default and when to choose otherwise.
---

# Decisions you make

For solution architects. Each decision has a default that suits most integrations; choose otherwise only for the reason given. Record your choices in your integration brief ([playbook, stage 0](../playbooks/delve-onboarding.md#stage-0-choose-the-grade-and-plan)).

| # | Decision | Options | Default | Choose otherwise when |
|---|---|---|---|---|
| D1 | Plan | Evaluation, Production, Mission Critical, Dedicated | Production | Real-time operations or live trading depend on it (Mission Critical), or regulation needs single tenancy or audit rights (Dedicated) |
| D2 | Jurisdiction | Australia and New Zealand, EU, US | Where your clients' data must stay | Never by latency alone: residency first |
| D3 | Integration styles | Finished, forming, backfill, events | Backfill once, then forming, plus events | Reports that redraw daily need only finished series |
| D4 | Extension transport | REST, batched REST, gRPC | REST | Many series at once (batched REST), or sustained high rates with tight tail latency (gRPC, Mission Critical) |
| D5 | Event channel | Webhook, event bus, polling | Webhook | No inbound endpoint allowed (event bus on Mission Critical, or polling jobs) |
| D6 | Authentication | API keys, OAuth with `private_key_jwt`, mutual TLS, workload identity | API keys | Policy forbids long-lived secrets (OAuth or workload identity), or requires client certificates (mutual TLS) |
| D7 | Connectivity | Internet, private connectivity, dedicated interconnect | Internet with TLS | Traffic must stay off the internet (private connectivity, Mission Critical) |
| D8 | Bar width | Seconds to a day | What your chart's finest view needs to read | Fewer, wider bars cut cost and rate; narrower ones show more at the finest level |
| D9 | Profile version | Unpinned, pinned | Pinned in production | Never unpinned where results must reproduce (audits, backtests, models) |
| D10 | Segment and edge storage | Object store, time-series database, relational database | One record per series holding segments and edge, by client prefix, with a version for one writer | You query segments across series (a database) |
| D11 | Your own resilience | One region, two regions | One region on Production; two on Mission Critical | Your own service level is higher than one region gives |
| D12 | Series naming | Hash of client and asset, with a salt | `hash(client)/hash(asset)/measure` | Even the kind of measure is sensitive: drop the suffix |

[Detailed flows](flows.md) shows how each choice behaves at run time; [Plans](../service/plans.md) shows what each plan provides.
