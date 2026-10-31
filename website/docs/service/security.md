---
title: Security
sidebar_position: 5
description: Authentication, private connectivity, encryption and keys you manage, audit, and how Patternode looks after the service.
---

# Security

## Authentication

| Method | Plans | Use when |
|---|---|---|
| API keys | All | The default ([Getting your API keys](../get-started/api-keys.md)) |
| OAuth 2.0 client credentials, with `private_key_jwt` (RFC 7523) | Mission Critical, Dedicated | Your workloads should hold no long-lived secret: they sign a short assertion with a key that never leaves your KMS or HSM, and get an access token valid for 15 minutes |
| Mutual TLS, alone or binding the token (RFC 8705) | Mission Critical, Dedicated | Your policy requires client certificates, as many operational technology and trading networks do |
| Workload identity federation | Mission Critical, Dedicated | You want your cloud's own workload identity (AWS IAM, Azure Entra, Google) to stand in for a key |

Whatever the method, the scopes are the same.

## Network

- TLS 1.3 everywhere; TLS 1.2 with forward-secret ciphers only for clients that cannot do 1.3.
- Private connectivity on Mission Critical and Dedicated: AWS PrivateLink, Azure Private Link, Google Private Service Connect, and dedicated interconnect on Dedicated. Private endpoints are the only route to your account if you ask.
- An IP allow list per key, on any plan.
- Webhooks come from published address ranges, and can be sent to a private endpoint.

## Encryption

Data is encrypted in transit and at rest. On Mission Critical and Dedicated you MAY hold the key: Patternode keeps none of your series, so there is nothing of yours at rest to encrypt; your key seals your edges instead, so revoking it makes every edge unreadable to Patternode, which is also a way to end the service.

## Audit

`GET /v1/audit_events` lists every change to your account and keys, and every sign-in and support access, with actor, time, source address and request id, kept for 7 years. It reaches your security tooling as events (`audit.*`) on Mission Critical and Dedicated.

Patternode staff MUST NOT access your series. Support access to your account's metadata is logged and shown to you.

## How Patternode runs the service

- Least privilege, short-lived credentials and hardware-backed multi-factor authentication for every person with production access.
- Every change reviewed and deployed by pipeline; nobody changes production by hand.
- Dependencies scanned, software bills of materials published for client libraries, and build provenance to SLSA level 3.
- Penetration tested by an independent firm every year and after major change; Mission Critical and Dedicated customers get the summary.
- Vulnerability reports to `security@patternode.com`, under the disclosure policy in `SECURITY.md`.
