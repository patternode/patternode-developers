---
title: Reference architectures
sidebar_position: 5
description: Two worked reference architectures, for utility operations and for quantitative trading, showing where Patternode sits among the systems you already have.
---

# Reference architectures

For solution architects. Where Patternode sits among the systems your industry already runs. Both use the same API; the [industry pages](../industries/index.md) have the examples and data.

## Utility operations

[![Utility reference: operational zone with field devices, SCADA and historian; a one-way transfer to a historian mirror in the DMZ; the ingest workload in the enterprise zone calls Patternode ANZ over private connectivity; events return to a receiver in the enterprise zone](./img/utilities.svg)](./img/utilities.svg)

| Decision | Here |
|---|---|
| Where data is read | A historian mirror in the DMZ, fed one way from the operational zone. Nothing reads the operational zone directly |
| What is sent | Bars built from the points the historian kept, good quality only, every 15 minutes or as configured |
| Where Patternode sits | Outside every control zone and electronic security perimeter, reached outbound from the enterprise zone or your cloud |
| Plan and connectivity | Mission Critical for control room use, in your jurisdiction, with private connectivity and mutual TLS |
| Events | To a receiver in the enterprise zone; nothing flows back toward the operational zone |
| Operations | Storm and emergency declarations registered as blackout periods; capacity sized for the storm |

More: [Utilities](../industries/utilities.mdx).

## Quantitative trading

[![Trading reference: market data through a feed handler; the live path builds bars and extends each instrument from its stored edge over gRPC to Patternode in the same region, the answers feeding the signal engine; the research path runs jobs over Parquet in your storage for backtests; the same pinned profile version on both](./img/finance.svg)](./img/finance.svg)

| Decision | Here |
|---|---|
| Live path | One-second to one-minute bars, nanosecond times, each instrument extended from its stored edge over gRPC; the answers feed the signal engine directly |
| Research path | Jobs over Parquet in your storage, results written back to it; segments stored per profile version, with each series' edge to go live from |
| Reproducibility | The same pinned profile version on both paths: backtest segments are the segments you would have had live |
| Placement | Your platform in the jurisdiction's cloud region; private connectivity; p99 10 ms at the edge on Mission Critical |
| Operations | Venue trading hours registered as blackout periods; capacity sized for the open and the close |

More: [Finance](../industries/finance.mdx), and the full set of [quant fund views](quant/index.md).

Next: [Detailed flows](flows.md).
