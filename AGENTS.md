# AGENTS.md

Instructions for coding agents, whichever tool runs them. `CLAUDE.md` points here.

There are two kinds of agent here. Read the part that is yours.

## If you are building an integration with Patternode

You are working for a partner who wants their system to use Delve (or later Essence, Sentinel or Foresight). Do this, in order:

1. Read [`llms.txt`](llms.txt) for the map, then `website/docs/concepts/shards.md` (what goes in and what comes out) and `website/docs/guides/integration-patterns.md` (which pattern your user needs).
2. If your user's data is utilities or finance data, start from `examples/industries/<industry>/`.
3. Start the mock: `python mock/mock_patternode.py`. Build and test everything against it first, with a fake key such as `pnk_live_` followed by 36 `B`s.
4. Copy the client from `examples/python/patternode_client.py` or `examples/typescript/src/client.ts`, or generate one from `specs/openapi.yaml`. Keep what it does on every call: the key header, the body's SHA-256 in `x-amz-content-sha256`, an `Idempotency-Key` on every POST, retries that honour `retry-after`. For a forming series, keep its edge with its segments and send it with the next bars: `examples/python/segment_store.py` does this.
5. Write tests like `examples/python/tests/test_examples.py`: a bad series, a retry, a bar before the edge, an edge from another series, a 429, a forged webhook. Then run `tests/contract` against the mock and, when your user has access, their staging account.
6. For infrastructure, adapt `terraform/aws/delve-partner/`. Do not apply it unless your user asks you to.
7. Real access is in `website/docs/get-started/access.md`. It is a person's step: your user emails Patternode. Tell them so; do not try to obtain keys yourself.

Rules:

- The specs in `specs/` are the contract. If a page and a spec disagree, follow the spec and tell your user.
- Never write an API key into code, a file, a commit, a log or a chat, and never ask a person to paste one into a chat. Read keys from the environment or a secret store.
- Never call `https://api.patternode.com` with a live key unless your user has asked you to in this task.
- Do not build production paths on operations or events whose `x-status` is `planned`.
- Plans change capacity and service levels, never the API: code written now works on every plan.
- Patternode keeps none of your user's series. Their segments and edges are theirs to store; losing an edge means sending the series again as a finished series.

## If you are changing this repository

1. The specs are the contract. Change a spec first, then the contract tests (`tests/contract`), then the mock, then the examples and their tests, then the pages. Never document behaviour the spec does not have.
2. One functional contract for every plan, product and industry. A route, field or event only one industry needs goes in `specs/overlays/<industry>.yaml` (OpenAPI Overlay 1.0), never in the core.
3. Every operation and event carries `x-status`: `available`, `preview` or `planned`. A change to an `available` one must not break a client.
4. Code shown on a page is imported from the file CI runs (`!!raw-loader!@examples/...` in an `.mdx` page). Never paste code into a page.
5. This repository is public. Nothing about how Patternode finds segments: no method, settings, research results or claims beyond the service levels. No real partner, customer or person; invented names only (Example Utility, EXMPL).
6. No key, real or plausible, anywhere but the mock's fake keys (`pnk_test_`, `pnk_live_` or `pnk_admin_` followed by 36 `A`s, `B`s or `C`s). CI fails on any other.
7. Work on a branch and open a pull request into `main`; `main` is protected.
8. If you work for Patternode, follow the Patternode playbook at the end of this file as well. A partner's agent can ignore it.

| Task | Command |
|---|---|
| Run the mock | `python mock/mock_patternode.py` |
| Test the Python examples | `python -m unittest discover -s examples/python/tests -v` |
| The contract suite | `python -m unittest discover -s tests/contract -v` (mock); with `PATTERNODE_BASE_URL` and `PATTERNODE_API_KEY`, against a deployment |
| Redraw the diagrams | `python website/diagrams/architecture.py` (edit the script, never the SVGs) |
| Test the TypeScript examples | `cd examples/typescript && npm test` (mock running) |
| Lint the specs | `npx @redocly/cli@2 lint specs/openapi.yaml specs/status.yaml` and `npx @asyncapi/cli@6 validate specs/asyncapi.yaml` |
| Build the site | `cd website && npm ci && npm run build` (regenerates the API and events pages; fails on broken links) |
| Preview the site | `cd website && npm start` |

Writing: plain words, short sentences, tables for anything with more than two attributes. No em dashes inside a sentence; no bold inside a sentence. `.md` pages are CommonMark; use `.mdx` only when a page imports code or components.

<!-- playbook:begin 1.0.1: generated from patternode-architecture governance/playbook/agents-block.md by playbook.mjs sync. Do not edit here. -->

## The Patternode playbook

One playbook governs how change moves in every Patternode repository: improvements, branches, commits, pull requests, merging, contracts, versions, releases, deploys, and who may do what. It wins over every other page on those topics, this file included. A repository's own documents add facts and procedures only.

Read it before you branch, open or merge a pull request, change a contract, release or deploy. It is the same file in three places; use the first you can reach:

1. `.agents/skills/patternode-playbook/SKILL.md`, the installed copy.
2. `../patternode-architecture/governance/playbook/SKILL.md`, a sibling clone.
3. https://github.com/patternode/patternode-architecture/blob/main/governance/playbook/SKILL.md

This repository's facts (its trunk, who merges, who releases, where its procedures are) are in `.agents/playbook.yaml`.

Even before you have read it:

- Trunk-based development, never Git Flow. No release, hotfix or long-lived feature branches. Branch from the remote trunk named in `.agents/playbook.yaml`. A branch called `develop`, `deploy` or `master` does not mean Git Flow: the profile says which branch is the trunk, and a production pointer or mirror is never a branch to work on.
- One change, one short-lived branch, one pull request into the trunk, citing its reason (`IMP-NNN`, an issue, a thread, an ADR, or `No reference:` and why). Push before your session ends.
- Merge, deploy, release or apply infrastructure only if `.agents/playbook.yaml` names your role. Otherwise send the ready note to the role that does, and stop.
- Units meet only through contracts. A contract change is its own pull request in the provider's repository, before any code that uses it, and never breaks a consumer.
- New behaviour ships switched off. Turning it on is a release: a change of its own, reversible.

<!-- playbook:end -->
