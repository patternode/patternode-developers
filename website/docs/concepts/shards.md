---
title: Shards and bars
sidebar_position: 3
description: What you send (bars), what you get back (segment boxes at every level), and how to read and draw them.
---

# Shards and bars

## What you send: bars

A bar is one interval of your series:

```json
[open_time, close_time, open, high, low, close]
```

Times are epoch milliseconds, UTC. The rules:

| Rule | Why |
|---|---|
| In time order, not overlapping | A series has one past |
| `low <= open, close <= high` | The four values describe the interval |
| Every value above zero | A contract constraint. If your measure crosses zero, add a fixed offset before sending and remove it when you draw |
| Leave gaps; never send a flat filler bar | An interval where nothing happened, too few readings, nothing moved, or nothing flowed (an inverter at night), is absent, not zero. Irregular spacing is expected and read well |

You can send samples, `[time, value]`, instead, and the service makes bars. Sending bars keeps the choice of width with you, and is the better default. `examples/python/bars.py` builds them.

A shard is a fragment of a time series that keeps its shape at any scale. Each segment Delve returns is one shard.

## What you get: segment boxes

```json
{ "id": "h2@1730246400000", "parent": "h3@1730246400000", "height": 2, "order": 0, "bars": 14,
  "open_time": 1730246400000, "open": 412.0, "high_time": 1730271600000, "high": 455.2,
  "low_time": 1730250000000, "low": 401.7, "close_time": 1730296799000, "close": 448.3,
  "provisional": false }
```

| Field | Meaning |
|---|---|
| `height` | The level. 1 is the finest segments above your bars; higher is coarser. The top is the whole series |
| `id` | `h<height>@<open_time>`. Stable: the same segment has the same id in a segmentation and in every stream event |
| `parent` | The segment one level up that contains it |
| `bars` | How many of your bars it covers |
| open, high, low, close with times | The four vertices of its shape |
| `provisional` | The open right edge at its level: it may still grow and its close may move. Every other segment is final |

## Drawing

- A chart of width W pixels over a time window shows the coarsest level whose segments are still wide enough to read in that window, and switches to finer levels as the viewer zooms in. Store all levels; pick per chart.
- Draw a segment as a box from `open_time` to `close_time` between `low` and `high`, and its line from open through high and low, in time order, to close.
- A trend is the same series at a coarser level, drawn faintly behind.
- The open segment at levels 1, 2 and 3 gives a reading at three timescales: rising if its close is above its open, falling if below, steady if close.

## Finished and forming

| | Finished | Forming |
|---|---|---|
| You have | The whole series, or a window of it | One more bar at a time |
| You call | `POST /v1/segmentations` (or an upload and a job) | `POST /v1/streams`, then `/observations` |
| You get | Every segment | What this bar did at each level, and the right edge |
| Same result | Yes: appending every bar gives the same segments as sending them all at once | |
