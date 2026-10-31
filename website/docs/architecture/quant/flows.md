---
title: Flows for a fund
sidebar_label: Flows
sidebar_position: 5
description: Sequence diagrams for a fund's engineers. Backtest, going live from the backtest's edge, the intraday loop, and recovering an extender.
---

# Flows for a fund

## Backtest, then go live from where it ended

```mermaid
sequenceDiagram
  autonumber
  participant R as Research platform
  participant B as Your storage
  participant P as Patternode
  participant M as Model registry
  participant L as Live platform
  R->>B: Parquet per instrument; presign GET and PUT
  R->>P: POST /v1/segmentations/jobs {profile: standard@2026-11, return_edge: true, links}
  P->>B: GET the file, PUT the result (segments and the edge at its end)
  P-->>R: segmentation.job.succeeded
  R->>B: read results; build features; backtest
  R->>M: model, window, profile version
  Note over L: at the session start
  L->>P: POST /v1/segmentations {today so far, profile, return_edge: true}
  P-->>L: segments and an edge per instrument
  L->>L: edges into memory and the durable store
```

## The intraday loop

```mermaid
sequenceDiagram
  autonumber
  participant F as Bar builder
  participant X as Extender
  participant E as Edge store
  participant P as Patternode (gRPC Extend)
  participant S as Signal engine
  loop each bar close, every instrument
    F->>X: closed bars
    X->>P: ExtendRequest {correlation_id, series, edge, bars} per instrument
    P-->>X: ExtendResponse {closed, right_edge, edge}
    X->>E: new edge, version n+1 (if still n)
    X->>S: closed segments and right edge
  end
```

## Recovering an extender

```mermaid
sequenceDiagram
  autonumber
  participant X as New extender
  participant E as Edge store
  participant P as Patternode
  X->>E: read edges for its instruments
  alt an edge is present
    X->>P: extend from it with the next bars
  else an edge is missing
    X->>P: POST /v1/segmentations {session so far, return_edge: true}
    P-->>X: an edge
    X->>E: store it
  end
```

The general flows, with every error and what to do, are in [Detailed flows](../flows.md).
