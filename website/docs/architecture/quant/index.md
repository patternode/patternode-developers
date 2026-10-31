---
title: Quant fund architecture
sidebar_label: Overview
sidebar_position: 0
description: The architecture views for a quantitative fund. How Patternode fits research, backtesting and live trading, from the CTO's view down to the engineer's.
---

# Quant fund architecture

For a fund's CTO, head of quant technology and their architects, then its engineers. These views apply the general [architecture](../index.md) to a fund that segments trades and bars across many instruments, in research and in live trading.

[![A quant fund with Patternode: venues and vendors feed the fund's data platform; research runs jobs over files in the fund's storage; the live platform extends each instrument from its stored edge; execution sends orders to brokers; the segment store holds segments and edges for risk and compliance](../img/quant-context.svg)](../img/quant-context.svg)

## At a glance, for a fund

| Concern | Answer |
|---|---|
| What Patternode sees | Bars (times and four prices) under instrument names you choose. Never positions, orders, signals, models or strategies |
| What Patternode keeps | Nothing. Research files stay in your storage; live state stays in your edges |
| Research | Jobs read Parquet or Arrow from your storage and write results back; a job per series, run in parallel |
| Live | Each instrument extended from its stored edge as its bar closes, over gRPC on one connection; p99 10 ms at the edge on Mission Critical |
| Time | Nanosecond timestamps, kept exactly as sent |
| Reproducibility | The same bars with the same profile version give the same segments, bit for bit, for at least 24 months. Backtest and live agree |
| Change | No change in your cells during your venues' trading hours (blackout periods) |
| Resilience | Patternode holds no state, so either region answers any call; a regional failover takes up to 60 seconds and loses nothing of yours |
| Regulation | Terms for DORA and UK outsourcing rules, model risk documentation per profile version, an exit plan ([Compliance](../../service/compliance.md)) |
| Plan | Production for research; Mission Critical for live; Dedicated at full scale or under critical third-party oversight |

## The views

| View | For | Covers |
|---|---|---|
| [Research and backtest](research.md) | Quant researchers' platform team | Jobs over your storage, features, backtests, handing over to live |
| [Live trading](live.md) | Trading platform engineers | The live path, edges in memory and at rest, the latency budget, failure handling |
| [Reproducibility](reproducibility.md) | Model risk, research leads | Profile versions, pinning, moving to a new version safely |
| [Operations and compliance](operations.md) | CTO, risk, compliance, operations | Placement, capacity, blackout periods, resilience, DORA, audit |
| [Flows](flows.md) | Engineers | Every call in backtest, go-live, intraday and recovery |
