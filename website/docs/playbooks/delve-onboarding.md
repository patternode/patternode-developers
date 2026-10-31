---
title: Delve onboarding playbook
sidebar_label: Delve onboarding
sidebar_position: 1
description: From choosing a plan to production traffic at utility-operations or trading grade, in eleven stages with a gate at each.
---

# Delve onboarding playbook

The supported route from first contact to Delve running in production in your environment, at the grade your use needs. Eleven stages, each ending in a gate: a check that proves the stage is done. Stages marked "agent" can be run by a coding agent working from this site; the rest need a person.

The playbook is the same for every grade. What changes with the grade is the plan you choose in stage 0 and how hard stages 3, 8 and 9 bite. For a reporting product on the Production plan, stage 8 is an afternoon. For a control room or a live trading desk on Mission Critical, it is the stage that matters most.

| Stage | What | Who | Gate |
|---|---|---|---|
| 0 | [Choose the grade and plan](#stage-0-choose-the-grade-and-plan) | You | Plan, jurisdiction, transports and contacts chosen |
| 1 | [Order and receive your onboarding pack](#stage-1-order-and-receive-your-onboarding-pack) | Patternode, then you | Test key answers |
| 2 | [Build against the mock](#stage-2-build-against-the-mock) | You, agent | Your tests pass against the mock |
| 3 | [Design for the contract](#stage-3-design-for-the-contract) | You, agent | Capacity, latency and resilience design written down |
| 4 | [Stand up your infrastructure](#stage-4-stand-up-your-infrastructure) | You, agent | Infrastructure applied in each region you run in |
| 5 | [Take control of your credentials](#stage-5-take-control-of-your-credentials) | A named contact | Delivered admin key deleted; live credentials in your secret store |
| 6 | [First live call](#stage-6-first-live-call) | You, agent | A real series segmented and stored |
| 7 | [Wire the patterns you need](#stage-7-wire-the-patterns-you-need) | You, agent | Every flow you need runs end to end in staging |
| 8 | [Prove it](#stage-8-prove-it) | You, with Patternode | Load test and failover rehearsal passed |
| 9 | [Get ready to operate](#stage-9-get-ready-to-operate) | You | Monitoring, runbooks, blackout periods and exit plan in place |
| 10 | [Go live](#stage-10-go-live) | You, with Patternode | Production checklist complete; hypercare running |

## Stage 0: choose the grade and plan

Decide, and write down:

1. The grade. What happens to your users if Delve is unavailable for an hour? Delayed analysis is Production. A control room losing a view it operates from, or a desk unable to trade a signal, is Mission Critical. Read [Plans](../service/plans.md).
2. The jurisdiction, where your data must stay: Australia and New Zealand, the EU or the US ([Resilience](../service/resilience.md#jurisdictions)).
3. The transports. REST serves every plan and is enough for most; add gRPC for sustained high rates or tight tail latency, and your event bus for events ([Real-time](../service/realtime.md#transports)).
4. Your own service level, and the share of it you give to Patternode. If your product promises 99.95% and depends on Patternode in series, Patternode must be better than that: choose Mission Critical.
5. Two technical contacts, by name and work email. They receive the admin key and are the only people Patternode acts for on credentials. Two, so a credential can be rotated when one is away.
6. Your blackout periods (Mission Critical and Dedicated): your venues' trading hours, or the conditions under which your operator declares an emergency.
7. Your series naming scheme ([Naming series](../concepts/data-boundary.md#naming-series)).
8. Your industry's starting point: [Utilities](../industries/utilities.mdx) or [Finance](../industries/finance.mdx).

Gate: a one-page integration brief with the answers to 1 to 8.

## Stage 1: order and receive your onboarding pack

The order form names the plan, the jurisdiction, the transports, the technical contacts, the blackout periods and any agreed numbers. Patternode then creates your accounts (one for staging, one for production, on the same plan) and sends the onboarding pack to both technical contacts. [Getting your API keys](../get-started/api-keys.md) describes each item and how it reaches you:

| Item | How it reaches you |
|---|---|
| Account ids, plan, jurisdiction endpoint, tier quotas, profiles and their versions | The welcome email |
| A test key per account | The welcome email |
| An admin key per account | A one-time link to the first contact, expiring in 72 hours; its passphrase read out on the kick-off call |
| Private connectivity details (Mission Critical, Dedicated) | The welcome email: the service name to connect your endpoint to |

Gate:

```bash
PATTERNODE_API_KEY=pnk_test_... PATTERNODE_BASE_URL=https://us.api.patternode.com ./examples/curl/quickstart.sh
```

prints your staging account id and a demonstration segmentation, using your jurisdiction's endpoint.

## Stage 2: build against the mock

```bash
python mock/mock_patternode.py
```

The mock checks what the service checks at the door (key shape, body hash, scopes, time order, the edge's seal, idempotency) and answers in the real shapes, with fake segments ([The mock server](../get-started/mock-server.md)). Copy the client you need from `examples/`, or generate one from `specs/openapi.yaml` (REST) or `specs/proto/` (gRPC), and write your tests against the mock as `examples/python/tests/test_examples.py` does.

Gate: your tests pass against the mock, including:

- A bad series: expect `invalid_series` with `problems`.
- A retried write with the same `Idempotency-Key`: expect the first answer.
- A retry with the same edge and bars: expect the same answer. A bar before the edge, an edge from another series, a changed edge: expect `out_of_order`, `edge_mismatch`, `edge_invalid`.
- Your contract tests: run `tests/contract` from this repository against the mock, then against your staging account.
- A 429 and a 503: expect your client to wait for `retry-after` and succeed.
- A forged webhook: expect your receiver to answer 400.

## Stage 3: design for the contract

Write a short design, and check it against the contract.

### Capacity

| Input | Your figure |
|---|---|
| Series (assets times measures, or instruments times bar widths) | |
| Bars a second, at peak (series divided by bar width, times the peak factor) | |
| Forming series at peak | |
| History to backfill (bars), and how fast | |

Peak, not average. A storm can make every feeder report at once, and a market open makes every instrument trade at once. Compare the peak with your plan's figures ([Plans](../service/plans.md)). If it is over them, tell Patternode now: capacity is added within 10 business days.

### Latency budget

Start from what your user sees and work back. A control room tile that must update within 2 seconds of a reading, or a signal that must reach a strategy within 50 milliseconds of a bar closing, divides into your collection, your network to Patternode, Patternode's p99 ([Service levels](../service/service-levels.md)) and your own processing and drawing. Place your callers in the same cloud region as your jurisdiction's endpoint, or connect privately, so the network share is small and steady.

### Resilience

Your client MUST:

- Retry 429, 5xx and network errors with backoff, honouring `retry-after`, resending the request unchanged.
- Store each forming series' closed segments, right edge and edge in one write, with one writer per series ([Your segment store](../guides/segment-store.mdx)).
- Reconnect gRPC streams on `GOAWAY` or reset, and resend what was not answered.
- Deduplicate events by `id`.
- Use the jurisdiction endpoint, never a regional address, so a regional failover is invisible.

On Mission Critical, run your own callers in two regions as well. Patternode surviving a region does not help you if your ingest workload does not.

Gate: the design is written down, and your peak is inside your plan or Patternode has confirmed the extra capacity.

## Stage 4: stand up your infrastructure

| Building block | Why | AWS recipe |
|---|---|---|
| Key vault | Credentials never sit in code, images or CI logs | Secrets Manager, KMS |
| Shard store | You keep the segments, beside your own data, under your client's prefix | S3, versioned, encrypted |
| Event receiver | Job and account events arrive asynchronously; verify, deduplicate, queue | Lambda Function URL, DynamoDB, SQS |
| Ingest workload role | The only thing that reads the live credential | IAM policy |
| Private endpoint (Mission Critical, Dedicated) | Traffic to Patternode never crosses the internet | An interface VPC endpoint to the service name in your pack |

```bash
cd terraform/aws/delve-partner
terraform init
terraform apply -var-file=staging.tfvars
```

On Mission Critical, apply it in each region your callers run in. See [Your side](../architecture/partner-side.md) for other stacks.

Gate: `terraform output webhook_url` prints an HTTPS URL in each region.

## Stage 5: take control of your credentials

A named contact does this, by hand, from a trusted machine, for staging and then for production.

1. Open the one-time link and enter the passphrase from the kick-off call. Put the admin key in your password manager.
2. Make your own admin key, and delete the delivered one with it:

   ```bash
   export PATTERNODE_API_KEY=pnk_admin_...delivered...
   python examples/python/keys.py create-admin --name ops-admin        # printed once
   export PATTERNODE_API_KEY=pnk_admin_...yours...
   python examples/python/keys.py delete <id of the delivered key>
   ```

3. Create a live key for each workload, with the narrowest scopes and an expiry, straight into the secret store:

   ```bash
   python examples/python/keys.py create-live --name ingest --scopes full --expires-in-days 90 \
     | aws secretsmanager put-secret-value --secret-id "$(terraform output -raw live_key_secret_arn)" --secret-string file:///dev/stdin
   ```

   On Mission Critical and Dedicated you may instead register a client for OAuth with `private_key_jwt`, so your workloads hold no long-lived secret at all ([Security](../service/security.md#authentication)).

4. Issue the webhook secret, store it, and point Patternode at your receiver:

   ```bash
   python examples/python/keys.py webhook-secret \
     | aws secretsmanager put-secret-value --secret-id "$(terraform output -raw webhook_secret_arn)" --secret-string file:///dev/stdin
   python examples/python/keys.py set-webhook "$(terraform output -raw webhook_url)"
   ```

5. Add the key pattern `\bpnk_(live|test|admin)_[0-9A-Za-z]{36}\b` to your secret scanning.

Gate: `python examples/python/keys.py list` shows no active key you did not create, and the delivered admin key shows `deleted`.

## Stage 6: first live call

From your ingest workload in staging, with the live key read from the secret store:

```bash
python examples/python/finished_series.py examples/data/export-kw.json
```

then the same with one of your own series, built into bars by your own code ([Shards and bars](../concepts/shards.md)). Pin the profile version you will run in production (`standard@2026-11`), so staging and production agree bit for bit ([Determinism](../service/realtime.md#determinism)).

Gate: the segments of one real series are in your shard store, and `GET /v1/usage_report` shows the run.

## Stage 7: wire the patterns you need

| Need | Pattern |
|---|---|
| History, galleries, reports | [Finished series](../guides/finished-series.mdx) |
| Live tiles; act as a segment closes | [Forming series](../guides/forming-series.mdx), batched or on gRPC at volume |
| Years of history, or a backtest | [Backfill](../guides/backfill.mdx), in Parquet or Arrow at volume |
| Hear when something happens | [Webhooks](../guides/webhooks.mdx), or your event bus |

Gate: each flow runs end to end in staging, including events received, verified and deduplicated, and a restart of your ingest workload that carries every forming series on from its stored edge without a gap.

## Stage 8: prove it

Run these against your staging account, which is on the same plan as production. Tell Patternode the window two business days ahead so the test is not mistaken for an incident.

| Test | How | Pass |
|---|---|---|
| Load | Your peak from stage 3, for an hour, then twice your peak for 10 minutes | Your latency budget holds at peak; at twice peak, 429s with `retry-after` and no errors your client does not absorb |
| Soak | Your normal rate for 24 hours | No growth in latency, memory or open connections on your side; usage report matches your counts |
| Failover rehearsal (Mission Critical, Dedicated) | Patternode drains the region serving your staging account during the window | Your users see nothing beyond your budget; no series left behind its edge; no lost or unhandled events |
| Credential rotation | Rotate the live key and the webhook secret under load | No failed request, no rejected delivery |
| Backfill at scale | Your largest backfill, in the format you will use | Inside your planned time; usage as estimated |

Gate: every test passed, with the results written down.

## Stage 9: get ready to operate

| Area | In place |
|---|---|
| Monitoring | Your own indicators per transport: success rate, p99 latency, 429 rate, out-of-order and edge errors, event lag, dead-letter depth. Alerts on each, routed to your on-call |
| Patternode's view | `status.patternode.com`'s feed or the `status.*` events routed to your on-call; your alerts ask the status API before paging; `GET /v1/service_levels` in your monthly review |
| Tracing | W3C `traceparent` sent on every request, so `server-timing` shows Patternode's share |
| Runbooks | For: 429 storm, 5xx burst, failover, credential leak, webhook secret rotation, dead-letter redrive, catching a series up after a long outage |
| Support | Technical contacts able to open Severity 1 by phone; your plan's numbers in the runbooks |
| Blackout periods | Registered with Patternode (Mission Critical, Dedicated) |
| Exit | Your exit plan: segments and edges are yours already; who is told |

Gate: a person on call can find each runbook, and a dry run of the credential-leak runbook has been done.

## Stage 10: go live

Work through the [production checklist](../go-live/production-checklist.md), switch production traffic on in steps (a tenth of your series, then half, then all, a day apart), and tell Patternode the date. On Mission Critical and Dedicated, Patternode runs two weeks of hypercare: a named engineer watching your account, and a daily check-in if you want one.

Gate: every line of the checklist is ticked, all production traffic is on, and hypercare has ended without an open Severity 1 or 2.

## After go-live

| Every | Do |
|---|---|
| Day | Watch your alerts; read the dead-letter queue |
| Month | Compare `GET /v1/service_levels` and `GET /v1/usage_report` with your own figures; claim credits within 30 days if they are owed |
| Quarter | Read Patternode's failover test results (Mission Critical, Dedicated); repeat your own failover rehearsal; review capacity against plan |
| 90 days, or a person leaving | Rotate live keys and the webhook secret ([Rotating](../get-started/api-keys.md#rotating)) |
| Release | Read the [changelog](../resources/changelog.md). Preview routes can change with 30 days' notice; pinned profile versions never change |
