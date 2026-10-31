# Security

Report a vulnerability in the Patternode service, its API or this repository to `security@patternode.com`. Please do not open a public issue.

- We acknowledge within 2 business days and agree a disclosure date with you, normally within 90 days.
- Test only against your own account, and never against another customer's data or the service's availability.
- If you find a Patternode API key (`pnk_live_`, `pnk_test_` or `pnk_admin_`) exposed anywhere, report it; we revoke it and tell its owner.

We do not take legal action against good-faith research that follows this policy.

A leaked key of your own: disable it at once with your admin key (`POST /v1/keys/{id}/disable`), then see [Getting your API keys](website/docs/get-started/api-keys.md#if-a-key-leaks).
