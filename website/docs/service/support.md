---
title: Support
sidebar_position: 7
description: Severities, response times, incident communication and post-incident reports.
---

# Support

## Severities

| Severity | Means |
|---|---|
| 1 | The service is down or badly degraded in production for you, and no workaround exists |
| 2 | A production function is impaired, or a workaround is burdensome |
| 3 | A problem with a workaround, or a non-production environment down |
| 4 | A question or a request |

## Response

| Plan | Hours | Severity 1 | Severity 2 | Severity 3 | Severity 4 | Channels |
|---|---|---|---|---|---|---|
| Evaluation | | | | | Best effort | Community, email |
| Production | Business hours in your jurisdiction | 4 hours | 8 hours | 2 business days | 5 business days | Email, portal |
| Mission Critical | 24x7 for Severity 1 and 2 | 15 minutes | 1 hour | 1 business day | 2 business days | Portal, phone, shared chat channel |
| Dedicated | 24x7 | 15 minutes, with a named engineer | 1 hour | 4 hours | 1 business day | As Mission Critical, plus a named technical account manager |

Response is a person working on it, not an acknowledgement. Severity 1 continues around the clock until resolved.

## Incidents

When Patternode has an incident affecting you:

| When | Patternode MUST |
|---|---|
| Within 15 minutes of detection (Mission Critical, Dedicated) or 1 hour (Production) | Post it on `status.patternode.com` and notify subscribers |
| Every 30 minutes until resolved | Post an update |
| Within 24 hours of a major incident affecting you | Give you the initial notification details your regulator needs (DORA, NERC, national regimes) |
| Within 5 business days | Publish a post-incident report: timeline, cause, impact, and the actions taken and planned |

## Your side

Open Severity 1 and 2 by phone or portal, not email. Include request ids, times in UTC, the jurisdiction, and the transport. Technical contacts named in the order form can open any severity; others can open Severity 3 and 4.
