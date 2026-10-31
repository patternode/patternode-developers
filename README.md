# Patternode for developers

Everything you need to integrate with Patternode's products: Delve, the shards toolkit, and Essence, Sentinel and Foresight, which run on it. This repository is the source of [developers.patternode.com](https://developers.patternode.com).

## Start here

| You are | Do this |
|---|---|
| Trying it out | Run the mock and the first example below. No account needed |
| Ready for real keys | Read [Getting access](website/docs/get-started/access.md): email `partners@patternode.com` for an evaluation account |
| An enterprise or solution architect | Read the [architecture overview](website/docs/architecture/index.md), then the views for your role |
| Planning an integration | Follow the [Delve onboarding playbook](website/docs/playbooks/delve-onboarding.md), eleven stages from plan to go-live |
| A coding agent | Read [AGENTS.md](AGENTS.md), then [`llms.txt`](llms.txt) |
| Checking what we commit to | Read the [service contract](website/docs/service/index.md): plans, service levels, resilience, security, support |
| In utilities or finance | Start from your [industry](website/docs/industries/index.md): examples and data in your shape |

## Try it in a minute

Python 3.10 or newer, nothing to install:

```bash
git clone https://github.com/patternode/patternode-developers
cd patternode-developers
python mock/mock_patternode.py &
PATTERNODE_API_KEY=pnk_test_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA python examples/python/first_call.py
```

The mock answers in the real API's shapes with fake segments, so what you build against it runs unchanged against `https://api.patternode.com` with your own key.

## What is here

| Path | What |
|---|---|
| `specs/` | The contracts: `openapi.yaml` (REST), `asyncapi.yaml` (webhooks, subscriptions, event buses), `proto/` (gRPC), `schemas/` (JSON Schema). Generate clients from them |
| `examples/` | Code that runs: a client, every integration pattern and key management in Python and TypeScript; curl; industry overlays in `examples/industries/` |
| `mock/` | A local stand-in for the API, one file of standard-library Python |
| `tests/contract/` | The contract as tests: run against the mock in CI, and against any deployment of the API |
| `terraform/` | Your side on AWS: key vault, segment store, webhook receiver |
| `website/` | The Docusaurus site; its pages are in `website/docs/` |

## Check it

```bash
python -m unittest discover -s examples/python/tests -v       # every Python example against the mock
(cd examples/typescript && npm test)                          # the TypeScript examples, with the mock running
(cd website && npm ci && npm run build)                       # the site; fails on any broken link
```

## Help

| Need | Where |
|---|---|
| Access, or a question about integrating | `partners@patternode.com` |
| A mistake in the docs or examples | [Open an issue](https://github.com/patternode/patternode-developers/issues/new/choose) |
| Service status | [status.patternode.com](https://status.patternode.com) |
| A security issue | `security@patternode.com`, see [SECURITY.md](SECURITY.md) |

## Licence

| What | Licence |
|---|---|
| Code, specs and configuration: `specs/`, `examples/`, `mock/`, `terraform/`, and the site's code (`website/*.ts`, `website/scripts/`, `website/src/`) | [Apache License 2.0](LICENSE) |
| The documentation: `website/docs/` | [Creative Commons Attribution 4.0 International](LICENSE-docs) |
| The names Patternode, Delve, Essence, Sentinel and Foresight, and the logos in `website/static/img/` | Not licensed. They are Patternode's marks: refer to the products by name, but do not use the marks to suggest your product is Patternode's |

So you can copy the client, the examples and the Terraform into your own code, generate clients from the specs, and quote the docs with attribution.
