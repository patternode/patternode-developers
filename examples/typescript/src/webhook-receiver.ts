// The webhook receiver: verify, deduplicate, answer 2xx at once, then do the work.
//   PATTERNODE_WEBHOOK_SECRET=whsec_... node src/webhook-receiver.ts    # :8787
import { createServer } from "node:http";
import { verify } from "./webhooks.ts";

const seen = new Set<string>(); // in production: a table with a TTL, keyed on webhook-id

createServer((req, res) => {
  const chunks: Buffer[] = [];
  req.on("data", (c) => chunks.push(c));
  req.on("end", () => {
    const body = Buffer.concat(chunks);
    let event: any;
    try {
      event = verify(process.env.PATTERNODE_WEBHOOK_SECRET!, req.headers as Record<string, string>, body);
    } catch (e) {
      res.writeHead(400).end(String(e));
      return;
    }
    res.writeHead(204).end();
    const id = req.headers["webhook-id"] as string;
    if (seen.has(id)) return;
    seen.add(id);
    console.log(`${event.type}: ${event.data?.id ?? ""}`); // your work goes here, after the answer
  });
}).listen(Number(process.env.PORT ?? 8787), "127.0.0.1");
