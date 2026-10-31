// Verify a Patternode webhook delivery (Standard Webhooks). Copy this function.
import { createHmac, timingSafeEqual } from "node:crypto";

export const TOLERANCE_S = 300;

export function verify(secret: string, headers: Record<string, string | undefined>, body: string | Buffer, now = Date.now() / 1000): any {
  const id = headers["webhook-id"], ts = headers["webhook-timestamp"], sigs = headers["webhook-signature"];
  if (!id || !ts || !sigs) throw new Error("missing webhook headers");
  if (!/^\d+$/.test(ts) || Math.abs(now - Number(ts)) > TOLERANCE_S) throw new Error("timestamp outside tolerance");
  const key = Buffer.from(secret.replace(/^whsec_/, ""), "base64");
  const expected = createHmac("sha256", key).update(`${id}.${ts}.`).update(body).digest();
  for (const sig of sigs.split(" ")) {
    const [version, value] = sig.split(",", 2);
    if (version !== "v1" || !value) continue;
    const got = Buffer.from(value, "base64");
    if (got.length === expected.length && timingSafeEqual(got, expected)) return JSON.parse(body.toString());
  }
  throw new Error("no signature matched");
}
