"""Turn your raw readings into bars, the unit Delve reads. Standard library only.

A bar is [open_time, close_time, open, high, low, close], times in epoch milliseconds.
Rules this follows, which are the contract's:

- Bars are in time order and never overlap.
- Leave a gap where nothing happened. An interval with too few readings, or one in which
  nothing moved or nothing flowed, is not sent as a flat bar; it is simply absent. Irregular
  spacing is fine and expected.
- Every value must be above zero. If your measure crosses zero (net export, a temperature
  in Celsius), send it with a fixed offset and remove the offset when you draw.
"""

from __future__ import annotations

from collections.abc import Iterable


def bars_from_samples(samples: Iterable[tuple[int, float]], width_ms: int, min_samples: int = 3,
                      offset: float = 0.0, drop_flat: bool = True) -> list[list[float]]:
    """Bucket (time_ms, value) samples, already in time order, into bars `width_ms` wide."""
    bars: list[list[float]] = []
    bucket: list[tuple[int, float]] = []
    start = None

    def flush():
        if len(bucket) < min_samples:
            return
        values = [v + offset for _, v in bucket]
        if drop_flat and max(values) == min(values):
            return
        if min(values) <= 0:
            raise ValueError(f"values at or below zero near {bucket[0][0]}: raise `offset`")
        bars.append([bucket[0][0], bucket[-1][0], values[0], max(values), min(values), values[-1]])

    for t, v in samples:
        if start is None or t >= start + width_ms:
            flush()
            bucket = []
            start = t - (t % width_ms)
        bucket.append((t, v))
    flush()
    return bars
