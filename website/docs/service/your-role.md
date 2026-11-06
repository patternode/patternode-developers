---
title: Your data, by role
sidebar_position: 6
description: What Patternode does with data for a vendor that uses it, a customer that uses it directly, and a customer whose vendor uses it, and how a vendor describes Patternode to its clients as a subprocessor.
---

# Your data, by role

Three kinds of organisation meet Patternode, and each needs a different account of what happens to its data. Find yours, then read its section.

| You are | You contract with | Patternode is | Read |
|---|---|---|---|
| A vendor that builds Patternode into its product for its clients (monitoring, analytics, risk) | Patternode | Your subprocessor, for your clients' data | [A vendor using Patternode](#a-vendor-using-patternode), then [Describing Patternode to your clients](#describing-patternode-to-your-clients) |
| A customer that uses Patternode directly (a utility, a fund, a bank) | Patternode | Your processor | [A customer using Patternode](#a-customer-using-patternode) |
| A customer whose vendor uses Patternode | Your vendor, not Patternode | Your vendor's subprocessor | [A customer whose vendor uses Patternode](#a-customer-whose-vendor-uses-patternode) |

In each case there are two modes, and the [Data management](data-management.md) page describes both.

| Mode | Status | What Patternode keeps |
|---|---|---|
| Patternode keeps nothing: Delve segments what it is sent | `available` | Usage records only (counts, key, time). No series, no copies, no results ([Data boundary](../concepts/data-boundary.md)) |
| A product keeps data in a tenancy | `planned` | The datasets the product's terms name, in a tenancy of its own, each client in a zone of its own |

## A vendor using Patternode

You send Patternode your clients' data, or Patternode keeps it for you, so Patternode processes your clients' data on your behalf. Your client is the controller, you are its processor, and Patternode is your subprocessor.

What Patternode does for you:

| | Delve (`available`) | A product that keeps data (`planned`) |
|---|---|---|
| Receives | Bars and an opaque series name per request | Your clients' datasets, through intake you control |
| Keeps | Usage records only | Each client's data in its own zone of your tenancy, under its own key |
| Computes | Segments, returned to you and not kept | Segments, scores and extracted facts, kept in that client's zone |
| Shares | Nothing | Only what you share, with whom you choose, until you revoke it ([Combining your data](data-management.md#combining-your-data-with-your-clients-and-patternodes)) |

What you do:

| Your obligation | How Patternode supports it |
|---|---|
| Name Patternode as a subprocessor to your clients, in your subprocessor list and your agreements with them | [Describing Patternode to your clients](#describing-patternode-to-your-clients) below gives the words |
| Pass Patternode's terms down: the data processing agreement, the locations, the security commitments | The [data processing agreement and assurance](compliance.md) on every plan |
| Tell your clients before Patternode's own subprocessors change, as your agreements require | Patternode gives you 30 days' notice of a change to its subprocessor list |
| Send only what is needed. With Delve, keep series names opaque and keep the mapping to clients and assets yourself | [Data boundary](../concepts/data-boundary.md) |
| Keep each client's data apart in your own systems | [Your client's prefix](../concepts/data-boundary.md#your-clients-prefix); and, when a product keeps data, a zone per client |
| Get your client's agreement before you share its data, or contribute it to a benchmark | Shares and benchmarks need it; Patternode records who agreed |
| Tell your client of an incident that may touch its data | Patternode tells you without undue delay ([Support](support.md)) |
| Answer your client's audits and questionnaires | Patternode's SOC 2 report, ISO/IEC 27001 certificate and questionnaires ([Compliance](compliance.md)) |
| Give your client its data back, or delete it, when it leaves | Export and deletion of one client's zone, with its key destroyed |

## Describing Patternode to your clients

Use the entry that matches the mode you use, in your subprocessor list or your agreement with each client. Replace the bracketed parts. The legal entity, its address and the locations are those in your agreement with Patternode.

### Delve: Patternode keeps nothing

| | |
|---|---|
| Subprocessor | Patternode ([legal entity, address]) |
| Service | Segmentation of time series |
| Data processed | Readings of the series we monitor for you, each under an opaque name that does not identify you, your sites or your assets |
| Purpose | To compute segments that our product shows you |
| Kept by Patternode | Nothing of the readings or the results. Usage records (counts and times) for billing |
| Location | [the jurisdiction in your agreement with Patternode] |
| Security | Encrypted in transit; Patternode's SOC 2 Type II report and ISO/IEC 27001 certification |
| Further subprocessors | Patternode's cloud providers, as in its subprocessor list, with 30 days' notice of change |

### A product that keeps data (`planned`)

| | |
|---|---|
| Subprocessor | Patternode ([legal entity, address]) |
| Service | [the product: for example, storage and analysis of asset data and its 360 view] |
| Data processed | [the datasets: for example, your asset register, readings, documents and 3D models] |
| Purpose | To provide our product's [named features] to you |
| Where it is kept | In a zone of its own inside our tenancy on Patternode, under its own encryption key, with its own databases. No other client of ours can read it |
| Who can read it | Your users, us under our agreement with you, and Patternode's services acting for us. Not Patternode's research, its staff (except recorded emergency access you are shown), or any other customer |
| Used for | Only our service to you. Benchmarks only with your agreement, and only as aggregates. Never to train models for anyone else |
| Kept for | [the retention in your agreement]; deleted with its key destroyed when you leave or ask |
| Location | [the region in your agreement with Patternode] |
| Audit | Every access is recorded and can be given to you for your data |
| Further subprocessors | Patternode's cloud providers, as in its subprocessor list, with 30 days' notice of change |

## A customer using Patternode

You contract with Patternode directly. You are the controller and Patternode is your processor, under the data processing agreement in your order form.

| You want to know | Where |
|---|---|
| What Patternode keeps and where | [Data management](data-management.md): your tenancy, its keys and databases, and the two modes |
| Who can read your data | [Who can read what](data-management.md#who-can-read-what) |
| What it is used for | [What your data is used for](data-management.md#what-your-data-is-used-for) |
| How to get it back, or have it deleted | [Removing data](data-management.md#removing-data) |
| Patternode's own subprocessors and assurance | [Compliance](compliance.md) |
| Who does what | [Shared responsibility](shared-responsibility.md) |

If you also use a vendor that uses Patternode, the two are separate: your own tenancy, and the zone your vendor keeps for you in its tenancy. They meet only where you and your vendor link your records and your vendor shares its view of your data with you.

## A customer whose vendor uses Patternode

Your vendor uses Patternode to provide its service to you. You contract with your vendor; Patternode is your vendor's subprocessor, and acts only on your vendor's instructions under its agreement with Patternode. Your vendor should name Patternode in its subprocessor list, using an entry like those above.

What to ask your vendor:

| Ask | What a vendor using Patternode can answer |
|---|---|
| Which mode do you use? | Delve, where Patternode keeps nothing of your data; or a product that keeps data, in a zone of your own |
| What do you send Patternode? | With Delve, readings under opaque names that do not identify you. With a product that keeps data, the datasets named in your agreement |
| Is my data kept apart from your other clients'? | Yes: its own zone, its own encryption key and its own databases |
| Can I see what you see about my assets? | Yes, if your vendor shares its view with you. Each fact says whether it is yours, your vendor's or Patternode's ([Combining your data](data-management.md#combining-your-data-with-your-clients-and-patternodes)) |
| Is my data used for anything else? | Only for your vendor's service to you. Benchmarks only with your agreement. Never to train models for anyone else |
| Where is it kept? | In the jurisdiction or region in your vendor's agreement with Patternode |
| Who at Patternode can see it? | No one routinely. Emergency access is recorded, needs a second approver, and appears in the audit record your vendor can give you |
| What happens when I leave my vendor? | Your zone is exported to your vendor if you ask, then deleted and its key destroyed. Nothing else in your vendor's tenancy is affected |
| What assurance is there? | Patternode gives your vendor its SOC 2 report, ISO/IEC 27001 certificate and questionnaires ([Compliance](compliance.md)); your vendor's agreement with you says what it passes on |

Your rights over your data (access, correction, deletion, export) are exercised through your vendor, which instructs Patternode.
