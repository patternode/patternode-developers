---
title: Getting access
sidebar_position: 2
description: The three ways in, from no account at all to production, what to send Patternode, and what happens next.
---

# Getting access

There are three levels of access. You can start on the first today, without asking anyone.

| Level | What you can do | How to get it | How long |
|---|---|---|---|
| 1. No account | Read everything here, generate clients from the specs, run every example against the mock server | Nothing: clone the repository | Now |
| 2. Evaluation | Call the real API with a test key (demonstration series, free) and a live key with a small credit, on the Evaluation plan | Ask for an evaluation account (below) | 2 business days |
| 3. Production | Your own series in production, on the plan you choose | An order form, then the [onboarding playbook](../playbooks/delve-onboarding.md) | From a week, depending on the plan |

## Level 1: no account

```bash
git clone https://github.com/patternode/patternode-developers
cd patternode-developers
python mock/mock_patternode.py &
PATTERNODE_API_KEY=pnk_test_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA python examples/python/first_call.py
```

Then the [Quickstart](quickstart.mdx). Everything you build against the mock works unchanged against the real API.

## Level 2: ask for an evaluation account

Email `partners@patternode.com` with the subject "Evaluation account", and say:

| Tell us | Why |
|---|---|
| Your organisation and website | The account is in its name |
| Two technical contacts: name, work email, role | They receive the keys ([Getting your API keys](api-keys.md)) |
| Which products: Delve now; Essence, Sentinel or Foresight when they open | To set up your account |
| Your industry and the kind of data (historian tags, meter reads, trades, bars) | So the onboarding pack suits it |
| The jurisdiction your data must stay in: Australia and New Zealand, the EU or the US | Your account's home ([Resilience](../service/resilience.md#jurisdictions)) |
| Roughly how many series, and how often a bar closes | To set your quotas |

Do not send data, keys or anything confidential by email. Patternode answers within 2 business days, and then:

1. Both contacts get the welcome email: account id, plan, endpoint, quotas and the test key.
2. The first contact gets the one-time link to the admin key; its passphrase is read out on a short kick-off call.
3. You follow stages 2 to 6 of the [onboarding playbook](../playbooks/delve-onboarding.md).

## Level 3: production

When you are ready, tell your Patternode contact the plan ([Plans](../service/plans.md)), the jurisdiction and the transports you need. Patternode sends an order form; once it is signed, your production account is created and the onboarding pack arrives as for evaluation. The [onboarding playbook](../playbooks/delve-onboarding.md) takes you from there to go-live.

## Help

| Need | Where |
|---|---|
| A question about integrating | `partners@patternode.com`, or your shared channel once you have one |
| A mistake in these docs or examples | A [GitHub issue](https://github.com/patternode/patternode-developers/issues/new/choose) |
| A production problem | [Support](../service/support.md), by your plan's channel |
| A security issue | `security@patternode.com` ([SECURITY.md](https://github.com/patternode/patternode-developers/blob/main/SECURITY.md)) |
| Service status | `status.patternode.com` |
