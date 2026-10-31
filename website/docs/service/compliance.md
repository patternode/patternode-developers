---
title: Compliance
sidebar_position: 6
description: Assurance reports Patternode provides, and how the service supports the regimes utilities and funds work under.
---

# Compliance

## Assurance

| Assurance | Plans |
|---|---|
| SOC 2 Type II report, covering security, availability and confidentiality, every year | Production and above, under NDA |
| ISO/IEC 27001 certification | Production and above |
| Penetration test summary, every year | Mission Critical, Dedicated |
| Completed security questionnaire (CAIQ, SIG Lite) | On request |
| Right to audit, with notice | Dedicated |
| Subprocessor list, with 30 days' notice of change | All |
| Data processing agreement | All |

## Regimes

Patternode is not regulated for you; the obligations below are yours. The table says what the service gives you to meet them.

| Regime | Applies to | What the service gives you |
|---|---|---|
| EU Digital Operational Resilience Act (DORA) | Funds and other financial entities in the EU, for ICT third-party services | Contract terms in the order form for its Article 30 (service levels, locations, access, audit, exit); incident notification within the times of [Support](support.md); resilience testing results; exit plans; subprocessor list |
| UK operational resilience (PRA SS1/21, FCA SYSC 15A) and outsourcing (PRA SS2/21) | UK firms | The same terms; impact tolerances you set can rely on the published recovery objectives |
| MiFID II RTS 25, SEC Rule 613 (CAT) | Trading venues and firms with clock-sync duties | Nanosecond timestamps kept exactly as sent; Patternode's own clocks synchronised to UTC within 100 microseconds |
| Model risk management (SR 11-7, PRA SS1/23) | Firms using segment outputs in models | Determinism by profile version; profile versions served 24 months; a description of each profile's inputs, outputs and limits under NDA |
| NERC CIP | North American bulk electric system entities | No inbound connection into your electronic security perimeter is ever needed: your systems call out, or receive events through a broker you control. Private connectivity and mutual TLS for your CIP-011 information protection. Evidence pack under NDA |
| IEC 62443 | Operators of industrial automation and control systems | The same outbound-only pattern, so Patternode sits in your enterprise zone or a DMZ conduit, never in a control zone |
| Australian Security of Critical Infrastructure Act, and the NZ equivalents | Critical infrastructure in Australia and New Zealand | The ANZ jurisdiction keeps data in Australia and New Zealand; ownership and offshore access disclosed |
| GDPR, the NZ Privacy Act 2020, the Australian Privacy Act 1988 | Anyone sending personal data | You need not send any: series names are opaque ([Data boundary](../concepts/data-boundary.md)). A data processing agreement in any case |
