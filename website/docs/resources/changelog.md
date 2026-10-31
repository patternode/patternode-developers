---
title: Changelog
sidebar_position: 2
description: Changes to the API, the events, the profiles and this site.
---

# Changelog

## 1.0.0-draft.2, 2026-10-31

- Patternode keeps none of your series. A forming series is carried by its sealed edge: `POST /v1/segmentations/extend` and `/extend/batch` replace the stream routes (`/v1/streams`, sequences, checkpoints), and `return_edge` lets a finished series carry on. Errors `edge_invalid` and `edge_mismatch` replace `sequence_gap`.
- Jobs read from and write to your own storage (`source_url`, `result_url`); `/v1/uploads` and result links are gone, and Parquet and Arrow are read.
- The WebSocket subscription and the `stream.segmented` event are gone: every segmentation answers in its own response.
- The segment store library for your side, in Python and TypeScript.
- A contract test suite (`tests/contract`), run against the mock in CI and against any deployment with `PATTERNODE_BASE_URL`.
- An Architecture section, with diagrams, for architects and engineers.

## 1.0.0-draft, 2026-10-30

- The contract published for review: REST (`specs/openapi.yaml`), events (`specs/asyncapi.yaml`), gRPC (`specs/proto/`), JSON Schemas, the service contract, and the Delve onboarding playbook.
- Delve is the first product.
- Profile `standard@2026-11`.
- Licensed: Apache 2.0 for code and specs, CC BY 4.0 for the docs.
