# Industry overlays

An industry extension to the core API is an [OpenAPI Overlay 1.0](https://spec.openapis.org/overlay/v1.0.0.html) document here, named for its industry (`utilities.yaml`, `finance.yaml`), applied on top of `../openapi.yaml`. An overlay may add operations, fields and enum values marked `x-industry`; it never removes or changes anything in the core, so a client of the core is a client of every overlay.

There are none yet.
