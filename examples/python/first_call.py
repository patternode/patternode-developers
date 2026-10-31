"""Your first call: who am I, then the demonstration series. Works with a test key.

    PATTERNODE_API_KEY=pnk_test_... python examples/python/first_call.py
"""

from patternode_client import Patternode

pn = Patternode()
me = pn.get("/v1/whoami")
print(f"key {me['id']} ({me['kind']}) on account {me['account']}, tier {me['tier']}")

result = pn.post("/v1/segmentations", {"demo": "walk"})
print(f"{result['bars']} bars, {result['depth']} levels, {len(result['segments'])} segments")
for seg in result["segments"][:3]:
    edge = " (provisional)" if seg["provisional"] else ""
    print(f"  {seg['id']}: level {seg['height']}, {seg['bars']} bars, {seg['open']} -> {seg['close']}{edge}")
