---
title: Partner building blocks
sidebar_position: 6
description: The parts you build on your side, what each must do, and what realises each in the AWS recipe.
---

# Partner building blocks

The abstract building blocks of any Delve integration, whatever your stack, with the contract each must meet and one realisation of each.

| Building block | Must | AWS recipe realises it with |
|---|---|---|
| Key vault | Hold the live key and webhook secret encrypted; let only the ingest role and the receiver read them; keep versions for rotation | Secrets Manager, a KMS key |
| Bar builder | Turn readings into ordered, non-overlapping bars above zero; leave gaps | Your code; `examples/python/bars.py` |
| Patternode client | Send the key, the body hash, an idempotency key; retry 429 and 5xx with backoff and `retry-after` | Your code; `examples/*/client` |
| Ingest workload | Call Patternode from your backend, never a browser; one writer per stream | Your service, with the ingest IAM policy |
| Shard store | Keep segments by client prefix, series, level and id; replace provisional segments; keep final ones | S3, versioned, encrypted |
| Webhook receiver | Verify, reject stale, deduplicate, answer 2xx at once, queue | Lambda Function URL, DynamoDB, SQS with a dead-letter queue |
| Renderer | Draw each chart from the level its width and window can read | Your app |
| Series registry | Map opaque series names and stream ids to client and asset | Your database |

A different stack is fine: the contract column is what matters. [AWS with Terraform](aws-terraform.md) is the complete recipe for one.
