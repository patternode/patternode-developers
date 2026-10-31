// Runs against the mock: start it first (python mock/mock_patternode.py), then npm test.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import { Patternode, PatternodeError } from "./client.ts";
import { verify } from "./webhooks.ts";

const base = process.env.PATTERNODE_BASE_URL ?? "http://127.0.0.1:4010";
const live = new Patternode({ apiKey: "pnk_live_" + "B".repeat(36), baseUrl: base });

test("demo series with a test key", async () => {
  const pn = new Patternode({ apiKey: "pnk_test_" + "A".repeat(36), baseUrl: base });
  const r = await pn.post("/v1/segmentations", { demo: "walk" });
  assert.equal(r.object, "segmentation");
  assert.ok(r.segments.length > 0);
});

test("errors carry the code", async () => {
  await assert.rejects(live.post("/v1/segmentations", { series: "x", bars: [[5, 6, 1, 1, 1, 1], [3, 4, 1, 1, 1, 1]] }),
    (e: PatternodeError) => e.code === "invalid_series" && e.problems[0].problem === "times_not_increasing");
});

test("a forming series carries its edge; nothing is kept between calls", async () => {
  let edge: string | undefined;
  let closed = 0;
  for (let i = 0; i < 12; i++) {
    const body: any = { series: "ts/forming", profile: "standard@2026-11", bars: [[i * 10, i * 10 + 9, 1, 2, 1, 2]] };
    if (edge) body.edge = edge;
    const r = await live.post("/v1/segmentations/extend", body);
    closed += r.closed.length;
    edge = r.edge;
  }
  assert.ok(closed > 0);
  const again = await live.post("/v1/segmentations/extend", { series: "ts/forming", edge, bars: [[200, 209, 1, 2, 1, 2]] });
  const retry = await live.post("/v1/segmentations/extend", { series: "ts/forming", edge, bars: [[200, 209, 1, 2, 1, 2]] });
  assert.deepEqual(again.right_edge, retry.right_edge);
});

test("webhook signatures verify and reject tampering", () => {
  const secret = "whsec_" + Buffer.alloc(32, "k").toString("base64");
  const body = JSON.stringify({ type: "segmentation.job.succeeded", data: {} });
  const ts = String(Math.floor(Date.now() / 1000));
  const sig = createHmac("sha256", Buffer.alloc(32, "k")).update(`msg_1.${ts}.${body}`).digest("base64");
  const h = { "webhook-id": "msg_1", "webhook-timestamp": ts, "webhook-signature": `v1,${sig}` };
  assert.equal(verify(secret, h, body).type, "segmentation.job.succeeded");
  assert.throws(() => verify(secret, h, body.replace("succeeded", "failed")));
});

test("the segment store carries the edge and cuts by width", async () => {
  const { SegmentStore } = await import("./segment-store.ts");
  const store = new SegmentStore();
  for (let i = 0; i < 40; i++) await store.extend(live, "ts/store", [[i * 10, i * 10 + 9, 1 + i, 2 + i, 1 + i, 2 + i]]);
  assert.ok(store.edge("ts/store")?.token.startsWith("pne1."));
  assert.ok(store.rightEdge("ts/store").length > 0);
  assert.ok(store.cut("ts/store", 0, 400, 20).length < store.cut("ts/store", 0, 400, 4000).length);
});
