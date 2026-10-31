// Your segment store, in memory: keep what Patternode returns, query it, and carry forming
// series forward. Patternode keeps none of your series; this is where they live. Replace the
// Map with your database and keep the logic. The Python twin is examples/python/segment_store.py.
import type { Patternode } from "./client.ts";

export interface Segment {
  id: string; parent: string | null; height: number; order: number; bars: number;
  open_time: number | string; open: number; high_time: number | string; high: number;
  low_time: number | string; low: number; close_time: number | string; close: number; provisional: boolean;
}

interface Doc { version: number; profile_version: string; segments: Map<string, Segment>; edge?: string; edge_last_close_time?: number | string }

export class SegmentStore {
  private docs = new Map<string, Doc>();

  /** Send the stored edge with the new bars, then store the answer. Safe to retry. */
  async extend(pn: Patternode, series: string, bars: unknown[], profile = "standard"): Promise<any> {
    const doc = this.docs.get(series);
    const body: any = { series, bars, profile: doc?.profile_version ?? profile };
    if (doc?.edge) body.edge = doc.edge;
    const r = await pn.post("/v1/segmentations/extend", body);
    this.applyExtension(series, r, doc?.version ?? 0);
    return r;
  }

  applyExtension(series: string, r: any, expectedVersion?: number): void {
    const doc = this.docs.get(series);
    if (expectedVersion !== undefined && (doc?.version ?? 0) !== expectedVersion) throw new Error(`stale write: ${series}`);
    const segments = new Map([...(doc?.segments ?? new Map()).entries()].filter(([, s]) => !s.provisional));
    for (const s of [...r.closed, ...r.right_edge]) segments.set(s.id, s);
    this.docs.set(series, { version: (doc?.version ?? 0) + 1, profile_version: r.profile_version, segments,
      edge: r.edge, edge_last_close_time: r.edge_last_close_time });
  }

  /** What Patternode needs to carry the series on: the sealed edge and where the next bar must start. */
  edge(series: string) {
    const d = this.docs.get(series);
    return d?.edge ? { token: d.edge, lastCloseTime: d.edge_last_close_time, profileVersion: d.profile_version } : undefined;
  }

  /** The open segment at each level, bottom up. */
  rightEdge(series: string): Segment[] {
    return [...(this.docs.get(series)?.segments.values() ?? [])].filter((s) => s.provisional).sort((a, b) => a.height - b.height);
  }

  /** What a chart widthPx wide over [start, end] should draw: the finest level at least minPx wide at the median. */
  cut(series: string, start: number, end: number, widthPx: number, minPx = 6): Segment[] {
    const all = [...(this.docs.get(series)?.segments.values() ?? [])]
      .filter((s) => Number(s.close_time) >= start && Number(s.open_time) <= end);
    const levels = [...new Set(all.map((s) => s.height))].sort((a, b) => a - b);
    for (const level of levels) {
      const segs = all.filter((s) => s.height === level).sort((a, b) => Number(a.open_time) - Number(b.open_time));
      const widths = segs.map((s) => ((Number(s.close_time) - Number(s.open_time)) / Math.max(end - start, 1)) * widthPx).sort((a, b) => a - b);
      if (widths[Math.floor(widths.length / 2)] >= minPx) return segs;
    }
    return levels.length ? all.filter((s) => s.height === levels[levels.length - 1]) : [];
  }
}
