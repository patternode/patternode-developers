#!/usr/bin/env bash
# The first calls, with curl. Works with a test key against production or the mock.
#   PATTERNODE_API_KEY=pnk_test_... ./examples/curl/quickstart.sh
set -euo pipefail
BASE="${PATTERNODE_BASE_URL:-http://127.0.0.1:4010}"
: "${PATTERNODE_API_KEY:?set PATTERNODE_API_KEY from your secret store}"

# 1. Who am I. Reads need only the key.
curl -sS "$BASE/v1/whoami" -H "authorization: Bearer $PATTERNODE_API_KEY"
echo

# 2. The demonstration series. Every write sends the SHA-256 of its exact body bytes,
#    and an Idempotency-Key so a retry cannot run it twice.
BODY='{"demo":"walk"}'
SHA=$(printf '%s' "$BODY" | sha256sum | cut -d' ' -f1)
curl -sS -X POST "$BASE/v1/segmentations" \
  -H "authorization: Bearer $PATTERNODE_API_KEY" \
  -H "content-type: application/json" \
  -H "x-amz-content-sha256: $SHA" \
  -H "idempotency-key: $(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen)" \
  --data-raw "$BODY" | head -c 600
echo
