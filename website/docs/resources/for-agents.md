---
title: For coding agents
sidebar_position: 1
description: How a coding agent should use this site and repository to build a Patternode integration.
---

# For coding agents

This site is written to be read by agents as well as people.

| Resource | Where |
|---|---|
| An index of every page, for agents | [`/llms.txt`](pathname:///llms.txt) |
| Every page in one file | [`/llms-full.txt`](pathname:///llms-full.txt) |
| Any page as Markdown | The page's address with `.md` appended |
| The REST contract | [`/specs/openapi.yaml`](pathname:///specs/openapi.yaml) |
| The event contract | [`/specs/asyncapi.yaml`](pathname:///specs/asyncapi.yaml) |
| The gRPC contract | `specs/proto/patternode/delve/v1/delve.proto` in the repository |
| JSON Schemas | `specs/schemas/` in the repository |
| Step-by-step instructions for an agent, and the repository's own map | [`AGENTS.md`](https://github.com/patternode/patternode-developers/blob/main/AGENTS.md) and [`llms.txt`](https://github.com/patternode/patternode-developers/blob/main/llms.txt) at the repository's root |

## Rules for an agent building an integration

1. The specs are the contract. Where a page and a spec disagree, the spec wins; report the difference.
2. Build and test against the mock (`python mock/mock_patternode.py`) before any real key is used.
3. Never write a key into code, a file, a commit, a log or a message. Read it from the environment or a secret store. Never ask a person to paste one into a chat.
4. Never call a production endpoint with a live key unless the person you work for has asked you to, in this task.
5. Copy the client from `examples/` or generate one from the specs; keep the body hash, idempotency keys and retries, and store each forming series' edge with its segments ([Your segment store](../guides/segment-store.mdx)).
6. Respect `x-status`: do not build production paths on `planned` operations.
7. Start from the industry overlay that matches your user's data: `examples/industries/`.
8. Getting real access is a person's step ([Getting access](../get-started/access.md)): tell your user to email Patternode. Do not try to obtain keys yourself.
