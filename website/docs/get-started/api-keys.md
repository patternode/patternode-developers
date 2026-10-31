---
title: Getting your API keys
sidebar_position: 3
description: How Patternode issues keys to a partner, the three kinds, scopes and expiry, where to keep them, and how to rotate and revoke them.
---

# Getting your API keys

Patternode issues you two keys to start: a test key, and an admin key you use once to make your own. Patternode never sees, sends or stores your live keys in readable form. It keeps only a keyed hash of each key, so it cannot recover a key for you, only help you replace it.

## The three kinds

| Kind | Prefix | Can | Cannot |
|---|---|---|---|
| Test | `pnk_test_` | Run the demonstration series (`{"demo": "walk"}`, `{"demo": "sensor"}`); free | Run your own series |
| Live | `pnk_live_` | Run your own series; billed from your credit | Manage keys or the account |
| Admin | `pnk_admin_` | Create, disable and delete keys; set limits, the webhook URL and auto-reload; read usage; buy credit | Run anything |

A key is its prefix, 30 random characters and a 6-character checksum. Every key matches

```text
\bpnk_(live|test|admin)_[0-9A-Za-z]{36}\b
```

which is published so that secret scanners (GitHub secret scanning, gitleaks, trufflehog) can find a leaked key. Add it to yours.

## How you receive them

| Step | What happens | Channel |
|---|---|---|
| 1 | The order form names two technical contacts | Order form |
| 2 | Patternode creates your account, sets your tier and profiles | |
| 3 | Both contacts get the welcome email: account id, tier, profiles, base URL and the test key | Email |
| 4 | The first contact gets a one-time link to the admin key. It opens once, then expires; unopened, it expires after 72 hours | Email, one-time link |
| 5 | The passphrase for that link is read out on the kick-off call, never written down | Voice |
| 6 | You make your own admin key with the delivered one, then delete the delivered one ([playbook, stage 5](../playbooks/delve-onboarding.md#stage-5-take-control-of-your-credentials)) | The API |
| 7 | You create live keys yourself, straight into your secret store | The API |

So the only key that crosses a channel you do not control is the delivered admin key, it crosses once, behind a code spoken on a call, and it is deleted within the hour. If the link has expired or was opened by someone else, tell Patternode at once: the admin key is revoked and a new link sent.

Patternode will never ask you for a key, by email, chat, call or a support ticket. A message that does is not from Patternode.

## Scopes

Scopes are fixed when a key is created. A preset is the usual choice.

| Scope | Grants |
|---|---|
| `segment:run` | `POST /v1/segmentations`, `/extend`, `/extend/batch`, `/jobs` |
| `segment:read` | `GET /v1/segmentations/jobs/{id}` |
| `usage:read` | `GET /v1/account`, the usage and cost reports |
| `keys:manage` | Keys, limits, webhook URL and secret |
| `billing:manage` | Credit purchase, auto-reload |

| Preset | Scopes | For |
|---|---|---|
| `full` | `segment:run`, `segment:read` | An ingest workload |
| `read-only` | `segment:read` | A dashboard that checks job status |
| `admin` | `usage:read`, `keys:manage`, `billing:manage` | Admin keys only |

Give each workload and each environment its own live key, with the narrowest preset that works. A leaked key is then one workload's problem, and its usage is visible on its own line of the usage report.

## Expiry and limits

Expiry is chosen at creation (1, 7, 30 or 90 days, a date, or never) and cannot be changed. Use 90 days for live keys and rotate before they expire; use 1 or 7 days for a key given to a contractor or a CI job. A key can also carry its own monthly spend limit and request rate, below the account's.

## Where to keep them

| Key | Keep it in | Read by |
|---|---|---|
| Admin | Your password manager, shared by the two technical contacts | People, by hand |
| Live | Your cloud secret store (AWS Secrets Manager, Google Secret Manager, Azure Key Vault, Vault) | The ingest workload's role, at start |
| Test | Your CI secrets | CI |
| Webhook secret | Your cloud secret store | The webhook receiver |

Never in source code, container images, `.env` files that are committed, client-side code, logs or tickets. Send keys only from your backend: a key in a browser or a mobile app is a published key.

## Rotating

Live key, with no downtime:

1. Create the new key with the same scopes and put it in the secret store as the current version.
2. Let your workloads pick it up (a restart, or the cache TTL of your secret client).
3. Check `last_used_at` of the old key in `GET /v1/keys` stops moving.
4. Delete the old key.

Webhook secret: issue a new one (`POST /v1/account/webhook_secret`). Deliveries are signed with the new and the previous secret until the next rotation, so update your receiver's secret at leisure, keeping the previous one as `previous`.

Admin key: create a new admin key, store it, and delete the old one with the new one. A key cannot delete itself.

## If a key leaks

1. Disable it at once: `POST /v1/keys/{id}/disable` with your admin key. Disabling is reversible and takes effect within a minute.
2. Create a replacement and roll it out as in Rotating.
3. Read `GET /v1/usage_report` for the leaked key's line, and tell Patternode if it shows use that was not yours.
4. Delete the leaked key.

If you lose every admin key, the technical contacts ask Patternode for a new delivery. That goes through the same one-time link and spoken passphrase.
