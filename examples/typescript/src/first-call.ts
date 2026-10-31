// Your first call: who am I, then the demonstration series. Works with a test key.
//   PATTERNODE_API_KEY=pnk_test_... node src/first-call.ts
import { Patternode } from "./client.ts";

const pn = new Patternode();
const me = await pn.get("/v1/whoami");
console.log(`key ${me.id} (${me.kind}) on account ${me.account}, tier ${me.tier}`);

const result = await pn.post("/v1/segmentations", { demo: "walk" });
console.log(`${result.bars} bars, ${result.depth} levels, ${result.segments.length} segments`);
