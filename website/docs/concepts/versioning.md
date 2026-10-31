---
title: Versioning and status
sidebar_position: 6
description: How the API changes, what x-status means, and how you hear about it.
---

# Versioning and status

The version is in the path (`/v1/`). Within a version:

| Change | Notice |
|---|---|
| A new route, a new optional field, a new event type, a new `error_code` | None. Ignore what you do not know |
| A breaking change to an `available` route | Never within `v1`. A `v2` would run beside `v1` for at least 12 months |
| A change to a `preview` route | 30 days, in the [changelog](../resources/changelog.md) and by email to technical contacts |
| A `planned` route | Specified to design against; it answers 404 until it ships |

Every operation in `specs/openapi.yaml` and every message in `specs/asyncapi.yaml` carries `x-status`. Write clients that tolerate unknown fields and unknown enum values.
