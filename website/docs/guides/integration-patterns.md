---
title: Integration patterns
sidebar_position: 1
description: The four ways a partner system works with Delve, and how to choose.
---

# Integration patterns

| Pattern | Use when | Calls | Status |
|---|---|---|---|
| [Finished series](finished-series.mdx) | You have a window of history and want every level to draw from | `POST /v1/segmentations` | Available |
| [Forming series](forming-series.mdx) | Bars arrive live and you want each segment as it closes | `POST /v1/streams`, `/observations` | Preview |
| [Backfill](backfill.mdx) | Years of history, or bodies over 5 MB | `POST /v1/uploads`, `/v1/segmentations/jobs` | Available |
| [Webhooks](webhooks.mdx) | You run jobs, or want account events | Your endpoint | Available |

Most integrations use three: a backfill once per series, a forming stream from then on, and webhooks for the jobs. A reporting product that redraws daily can use finished series alone.

```mermaid
flowchart TB
  start([A new series]) --> big{More than 5 MB of history?}
  big -- yes --> bf[Backfill: upload and job] --> wh[Webhook: job succeeded] --> store[(Store segments)]
  big -- no --> fin[Finished series: one call] --> store
  store --> live{Bars arrive live?}
  live -- yes --> fs[Forming series: one append per bar] --> store
  live -- no --> redraw[Redraw on a schedule: finished series again]
```

All four use the same key, client, body hash and error handling ([Requests, errors and limits](../concepts/requests.md)).
