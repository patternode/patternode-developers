---
title: Industries
sidebar_position: 0
description: The same API, with examples, data and guidance in the shape of your industry's data.
---

# Industries

Every industry uses the same API, the same events and the same service contract. An industry overlay adds what makes it quick to start in your industry: examples that read your kind of data, sample data in its shape, the bar widths and plans that usually fit, and the regulations you will be asked about.

| Industry | Typical data | Overlay |
|---|---|---|
| [Utilities](utilities.mdx) | Historian tags, SCADA points, meter reads, inverter and transformer sensors | `examples/industries/utilities/` |
| [Finance](finance.mdx) | Trades, quotes and bars, across many instruments, live and in backtest | `examples/industries/finance/` |

## Extensions

If an industry ever needs something the core API does not have, it is added as an extension, never as a change to the core: an OpenAPI Overlay document in `specs/overlays/<industry>.yaml`, applied on top of `specs/openapi.yaml`. Code written against the core keeps working whether or not you use an extension. There are no extensions yet.
