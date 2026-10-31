---
title: Data boundary
sidebar_position: 4
description: What Patternode receives, keeps and never sees, and how to name series so it learns nothing about your clients.
---

# Data boundary

Patternode keeps none of your series: no copies, no checkpoints, no results.

| | Finished series | Forming series |
|---|---|---|
| Patternode receives | Bars and a series name | Bars, a series name, and the edge you stored |
| Patternode keeps | Nothing of the series. Usage records (counts, key, time) for billing | The same: nothing. The series' state is in its edge, which you keep |
| Jobs | Read from a link to your storage, written to a link to your storage; the job record holds only status and usage | |
| Patternode never sees | Who the client is, what the asset is, units, location, labels | The same |

## Naming series

The series name is the only text you send. Make it opaque and stable:

```python
h = lambda s: hashlib.sha256((SALT + s).encode()).hexdigest()[:12]
name = f"{h(client_id)}/{h(asset_id)}/{measure}"     # e.g. 7f3a9c1b02e4/91cd0e55aa21/ac-power
```

- Keep `SALT` secret and per environment, so names cannot be matched to your records by anyone else.
- Keep the mapping from name to client and asset in your own store.
- The measure suffix is optional. Leave it out if even the kind of measure is sensitive.

## Your client's prefix

Store each client's readings and segments under that client's own prefix (a bucket prefix, a schema, a tenant id). Your app then reads only from the prefix of the client it is serving, and deleting a client is deleting a prefix. The [AWS recipe](../guides/aws-terraform.md) creates one bucket for every client; keep the prefix in every key you write.
