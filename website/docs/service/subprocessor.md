---
title: Patternode as a subprocessor
sidebar_position: 7
description: For a vendor that uses Patternode to serve its clients. What to keep for your own records, and what to show your clients, in each mode.
---

# Patternode as a subprocessor

When you use Patternode to provide your service to your clients, Patternode processes your clients' data on your behalf. Your client is the controller, you are its processor, and Patternode is your subprocessor. This page has two parts: what you keep for your own records, and what you show your clients.

| Mode | Status | What Patternode keeps |
|---|---|---|
| Delve: Patternode segments what you send and keeps nothing | `available` | Usage records only: counts, key, time ([Data boundary](../concepts/data-boundary.md)) |
| A product that keeps data for you, in your tenancy, each client in its own zone | `planned` | What the product's terms name ([Data management](data-management.md)) |

## Part 1: for your own records

### What you get from Patternode

| You need | Patternode gives you | Where |
|---|---|---|
| A data processing agreement | One on every plan | [Compliance](compliance.md) |
| Patternode's own subprocessors | Its subprocessor list, with 30 days' notice of a change | [Compliance](compliance.md) |
| Assurance for your clients' questionnaires and audits | SOC 2 Type II report, ISO/IEC 27001 certification, completed questionnaires | [Compliance](compliance.md) |
| Where processing happens | The jurisdiction in your order form | [Plans](plans.md) |
| Security measures | Authentication, network, encryption, audit, how the service is run | [Security](security.md) |
| A record of access | Audit events for your account, keys and support access | [Security](security.md#audit) |
| Incident notice | Patternode tells you without undue delay, with what is known | [Support](support.md) |
| Your data back, and deletion | Export and deletion; nothing to return with Delve | [Data management](data-management.md#removing-data) |

### Your record of processing

An entry for your own register of processing activities, for the processing Patternode does for you. Replace the bracketed parts.

| | Delve | A product that keeps data |
|---|---|---|
| Subprocessor | Patternode ([legal entity, address]) | The same |
| Service and purpose | Segmentation of the series we monitor for our clients | [The product and its features] |
| Categories of data | Readings of time series, each under an opaque name that identifies no client, site or asset | [The datasets: registers, readings, documents, models] |
| Personal data | None, unless the readings themselves relate to a person (a household's meter, for example), when they are personal data even under an opaque name | [As the datasets contain] |
| Data subjects | None; or the households or people the readings relate to | [As above] |
| Kept by Patternode | Nothing; usage records for billing | In each client's zone, for the agreed retention |
| Location | [The jurisdiction in our order form] | [The region in our order form] |
| Security measures | As Patternode's [Security](security.md) page and its assurance reports | The same, and a key per client zone |
| Further subprocessors | Patternode's cloud providers, as in its subprocessor list | The same |

### Before you go live

1. Decide the mode, and whether any reading relates to a person. If one does, treat it as personal data in your own assessments, whatever its name.
2. Name your series opaquely and keep the mapping to clients and assets in your own store ([Data boundary](../concepts/data-boundary.md#naming-series)).
3. Keep each client's data apart in your own systems ([Your client's prefix](../concepts/data-boundary.md#your-clients-prefix)).
4. Add Patternode to your subprocessor list and to your agreements with your clients, using the entry in Part 2.
5. Route Patternode's incident notices and subprocessor changes to whoever tells your clients.

### When something changes

| Change | What you do |
|---|---|
| Patternode gives notice of a change to its subprocessors | Pass it on to your clients as your agreements with them require; you have 30 days |
| You move from Delve to a product that keeps data | Update your entry and tell your clients before any of their data is kept |
| A client leaves you | With Delve, nothing is held to delete. With a product that keeps data, ask for its zone to be exported or deleted |

## Part 2: what you show your clients

### Your subprocessor entry

Put the entry for your mode in your subprocessor list and your agreement with each client. The legal entity, its address and the locations are those in your agreement with Patternode.

#### Delve: Patternode keeps nothing

| | |
|---|---|
| Subprocessor | Patternode ([legal entity, address]) |
| Service | Segmentation of time series |
| Data processed | Readings of the series we monitor for you, each under an opaque name that does not identify you, your sites or your assets |
| Purpose | To compute segments that our product shows you |
| Kept by Patternode | Nothing of the readings or the results. Usage records (counts and times) for billing |
| Location | [the jurisdiction in our agreement with Patternode] |
| Security | Encrypted in transit; Patternode's SOC 2 Type II report and ISO/IEC 27001 certification |
| Further subprocessors | Patternode's cloud providers, as in its subprocessor list, with 30 days' notice of change |

#### A product that keeps data (`planned`)

| | |
|---|---|
| Subprocessor | Patternode ([legal entity, address]) |
| Service | [the product: for example, storage and analysis of asset data and its 360 view] |
| Data processed | [the datasets: for example, your asset register, readings, documents and 3D models] |
| Purpose | To provide our product's [named features] to you |
| Where it is kept | In a zone of its own inside our tenancy on Patternode, under its own encryption key, with its own databases. No other client of ours can read it |
| Who can read it | Your users, us under our agreement with you, and Patternode's services acting for us. Not Patternode's research, its staff (except recorded emergency access you are shown), or any other customer |
| Used for | Only our service to you. Benchmarks only with your agreement, and only as aggregates. Never to train models for anyone else |
| Kept for | [the retention in our agreement]; deleted with its key destroyed when you leave or ask |
| Location | [the region in our agreement with Patternode] |
| Audit | Every access is recorded and can be given to you for your data |
| Further subprocessors | Patternode's cloud providers, as in its subprocessor list, with 30 days' notice of change |

### A notice of change

When Patternode gives you notice of a change to its subprocessors, or you add Patternode, a notice like this one tells your clients what they need.

> Subject: A change to our subprocessors
>
> From [date], [our product] uses Patternode ([legal entity]) as a subprocessor for [the service]. [With Delve: Patternode receives readings under names that do not identify you, and keeps none of them.] [With a product that keeps data: your data is kept in a zone of its own, under its own encryption key, and is used only for our service to you.] Processing takes place in [the jurisdiction or region]. Our updated subprocessor list is at [link]. If you have questions or wish to object, contact [contact] by [date], as our agreement with you provides.

### Answering your clients' questions

The questions a client is likely to ask, and the answers you can give, are on [Your data, by role](your-role.md#a-customer-whose-vendor-uses-patternode). If you show your clients a combined view of their assets, it is described on [Data management](data-management.md#combining-your-data-with-your-clients-and-patternodes).

## What Patternode does not do

- It has no agreement with your clients and never contacts them. Your clients exercise their rights through you, and you instruct Patternode.
- With Delve, it never learns who your clients are, what your assets are, or where they are.
- It does not use your clients' data for anyone else, for its research, or to train models for anyone else.
