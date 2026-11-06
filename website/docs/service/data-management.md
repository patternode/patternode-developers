---
title: Data management
sidebar_position: 5
description: How Patternode keeps, separates, protects and uses data when a product keeps it for you and your clients, and what you can tell your clients.
---

# Data management

How Patternode looks after data it keeps for you: where it is, how your clients' data is kept apart, who can read it, what it is used for, and how it is removed. It ends with a table you can give your own clients.

## Two modes

| | Patternode keeps nothing | Patternode keeps data for you |
|---|---|---|
| Products | Delve: segmentation of the series you send | Products whose terms keep your data, such as a gallery of your assets with their series and documents |
| What Patternode holds | Usage records only: counts, key, time ([Data boundary](../concepts/data-boundary.md)) | Your datasets, in a tenancy of your own |
| Status | `available` | `planned`: no product keeps customer data yet. This page states what each such product will commit to |

Everything below is about the second mode. With Delve, nothing of your series is kept, and your clients' data stays in your own storage under the prefixes you choose.

## Words

| Word | Means |
|---|---|
| Tenancy | Your boundary: everything Patternode keeps for you, apart from every other customer's |
| Zone | A part of your tenancy. Your own data is in one zone, data you offer all your clients in another, and each of your clients' data in a zone of its own |
| Dataset | One named, versioned set of records, whatever its form: a table, a set of series, documents, files or 3D models |
| Facet | One kind of information about a thing (an asset, a company, an instrument): its identity, readings, events, documents, shape and so on |
| Link | A record that your key for a thing refers to someone else's key for the same thing. A link joins; it gives no access |
| Share | Permission you give another tenancy to read named facets of yours, by reference, until you revoke it |

## Your tenancy

| Zone | Holds | Read by |
|---|---|---|
| Your own | Your configuration, your models, your reference data | You, and Patternode's services acting for you |
| Common | Templates and reference data you offer every client | You, and every one of your clients |
| One per client, such as Example Utility | That client's data | That client, you under your contract with it, and Patternode's services acting for you |

If you use Patternode for yourself rather than for clients, your tenancy has one zone.

## How your clients are kept apart

- Each client's zone has its own storage prefix, its own encryption key and its own database in every store that serves it.
- A request made for one client carries that client's zone in its credentials, never in its payload. Patternode's services act with those credentials, and the storage, keys and databases refuse anything outside that zone.
- Nothing moves from one client's zone to another's.
- Data Patternode offers every customer (market data, reference data) reaches your products by reference, under its licence. Your data never enters it.

## Combining your data with your clients' and Patternode's

You, your client and Patternode may each keep facets about the same asset, company or instrument, each under its own key. Each of you can build one 360 view of it from your own facets and the others', without copying them.

| View | Built by | Combines |
|---|---|---|
| 1 | Patternode, for you | What Patternode computes for you (segments, scores, extracted facts) and its common data (asset types and models, weather, instruments, companies) |
| 2 | You | Your own facets (alarms, configuration, readings, analytics) and view 1 |
| 3 | Your client | Its own facets (registers, work orders, positions) and view 2, which you share with it |

![Three aggregations, one 360 view. Above: your client's view (level 3) contains your view (level 2), which contains Patternode's facets (level 1); beside it, an inverter as your client sees it, every fact labelled C, V or P for whether your client, you (the vendor) or Patternode keeps it. Below: where the data lives. Your client's tenancy holds its register, work orders, location and parties, and links its key same-as your key. Your tenancy, in the zone for this client, holds alarms, configuration, readings and analytics, with what Patternode computes for you, and links to Patternode's asset type and the weather at the site. You share your zone's facets with your client; data Patternode offers every customer reaches each of you under your own plan and is never passed on. A strip at the foot shows the same pattern for a bank, a risk analytics vendor and Patternode](img/combined-views.svg)

In the picture, your client is `northvale`, you are `monitorco`, and Patternode's data for every customer is the root tenancy, with `cohort=utilities` holding what it offers utilities. The names are invented.


How the pieces fit:

- Each of you links your key to the others' keys, so a view can join them. A link gives no access on its own.
- You decide what your client reads, with a share: the facets, the things they cover, the purpose and the end date. Your client can read through it, or keep only the fields its own view needs. You can revoke it at any time, and every read through it is in your audit events, which your client can see too.
- Data Patternode offers every customer (market and reference data, asset type models, weather) is never passed on through a share. Your client reads it under its own plan, through the links, so nobody receives data it has not licensed.
- Every fact in a combined view says who keeps it: your client, you or Patternode.
- A client that keeps its own data outside Patternode combines the same way through the API: it reads what you share and joins it to its own data by the link keys.

## Who can read what

A read is allowed only when all of these hold. The first two are enforced by the infrastructure itself, so a mistaken grant cannot cross them.

| Check | Passes when |
|---|---|
| Tenancy | The reader acts for your tenancy, or holds a share you made that covers the data |
| Zone | The reader may act in the dataset's zone: a client in its own zone and the zones you share with it |
| Grant | The reader holds read on the dataset, or on what contains it |
| Tier | A production service reads only datasets published for production |
| Licence | The use is one the dataset's licence allows |
| Classification | The reader is cleared for the dataset's sensitivity: personal data only for the purposes your terms name |

Patternode's research, its agents and its people have no access to your tenancy. Support works on metadata only. In an emergency, access to your tenancy needs a stated reason, a second approver and a time limit, and it appears in your audit events.

## Encryption and keys

| | |
|---|---|
| In transit | TLS 1.3; TLS 1.2 with forward-secret ciphers only for clients that cannot use 1.3 |
| At rest | Your tenancy has its own key, and each client's zone has its own |
| Keys you hold | On Mission Critical and Dedicated, your tenancy's key can be held in your own key service and granted to Patternode. Revoking the grant makes your tenancy unreadable to Patternode, which also ends the service |

## Audit

Every read and change of your tenancy's data, every use of its keys, and every support access is recorded, kept for 7 years outside your tenancy, and shown to you through your audit events ([Security](security.md#audit)). You can filter them to one client's zone and pass them on.

## What your data is used for

| Use | Allowed |
|---|---|
| The service your terms describe, including its enrichment: segments, scores, extracted facts | Yes |
| Benchmarks across customers | Only with your agreement, and your client's for its data; only aggregates leave the zone, and the record of who contributed is kept |
| Patternode's research, experiments or agents | No |
| Training or evaluating models used for anyone else | No, unless you agree in writing for named data |
| Another customer's service | Never |
| Sale or disclosure | Never, except as the law requires, and then you are told unless the law forbids it |

## Removing data

| Event | What happens |
|---|---|
| A client leaves you | You ask for its zone to be exported, if you want it, then deleted. Its storage and databases are deleted and its key is destroyed, so no remaining copy, backups included, can be read. The rest of your tenancy is untouched |
| You leave | Your whole tenancy is exported, if you ask, then deleted the same way |
| Export | Every dataset in open formats: Parquet, JSON lines and your original files |

## Roles

| Arrangement | Controller | Processor | Sub-processor |
|---|---|---|---|
| You use Patternode for yourself | You | Patternode | Patternode's cloud providers |
| You serve your clients | Your client | You | Patternode, and its cloud providers |

Your terms confirm the roles. If an incident may touch personal data in your tenancy, Patternode tells you without undue delay, with what is known, so you and your clients can meet your own obligations ([Support](support.md)).

## What you can tell your clients

A table you can adapt and pass on. Replace the names with yours.

| Your client asks | You can answer |
|---|---|
| Where is my data? | In a zone of your own inside our tenancy on Patternode, under its own encryption key, with its own databases |
| Who can read it? | Your users, us under our contract with you, and Patternode's services acting for us. No other client of ours, and no other Patternode customer |
| Is it mixed with anyone else's? | No. Shared reference data reaches you by reference; your data never enters another client's zone |
| Can I see what you see about my assets? | Yes. We share our view of your assets with you, and you can combine it with your own records. Each fact says whether it is yours, ours or Patternode's |
| Is it used for anything else? | Only for the service. Benchmarks only with your agreement, and only as aggregates. Never for training models for anyone else |
| Where is it kept? | In the region named in our terms with Patternode |
| Can I see who accessed it? | Yes. Every access is recorded, and we can give you the record for your zone |
| Can I have it back, and how is it deleted? | Yes, in open formats. Deletion removes your zone everywhere and destroys its key, so no copy can be read afterwards |

## Related

- [Data boundary](../concepts/data-boundary.md): what Delve receives and keeps (nothing of your series).
- [Security](security.md): authentication, network, encryption and audit.
- [Shared responsibility](shared-responsibility.md): what Patternode looks after and what you do.
