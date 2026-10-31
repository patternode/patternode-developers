---
title: Products
sidebar_position: 2
description: Delve, Essence, Sentinel and Foresight, what each is, and what each offers through the API today.
---

# Products

| Product | What it is for you | Runs on | In the API |
|---|---|---|---|
| Delve | The shards toolkit. Turns a time series into segments at every level of its tree, so each chart draws the level it can read: every series in a gallery, one series at every level, live tiles, and later shape search | | Segmentations, uploads and jobs (available); streams (preview) |
| Essence | Patterns by precedent: what repeats | Delve | Planned |
| Sentinel | Anomalies by shape: what moves, and the alarm on it | Delve | Planned |
| Foresight | Forecasting: what comes next | Delve | Planned |

Delve was called Mosaic until 2026. Older material may use that name; it is the same product.

## Delve

| | |
|---|---|
| You send | A series as bars or samples, finished in one call or forming one bar at a time |
| You get | Segment boxes at every level, the open right edge marked provisional; for a forming series, whether each bar extended or segmented each level |
| You keep | The segments, in your own store, beside your own data |
| Patternode keeps | Nothing of a finished series after it answers; a checkpoint of the right edge of each open stream until you close it |
| Planned | Shape search across a gallery; a drawing kit (gallery, single view with levels, live tile) in your brand |

The status of each route is its `x-status` in the [API reference](/api/patternode-api): `available`, `preview` or `planned`.
