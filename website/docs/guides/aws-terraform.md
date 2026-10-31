---
title: AWS with Terraform
sidebar_position: 7
description: "A Terraform module for the partner side on AWS: key vault, shard store, webhook receiver and the ingest policy."
---

# AWS with Terraform

`terraform/aws/delve-partner` creates the partner side of a Delve integration in your AWS account. Nothing in it runs at Patternode, and no secret value is in it: values are put by a person ([playbook, stage 5](../playbooks/delve-onboarding.md#stage-5-take-control-of-your-credentials)).

| Resource | Is |
|---|---|
| `aws_kms_key` | Encrypts the secrets, the shard store and the queues |
| `aws_secretsmanager_secret.live_key`, `.webhook_secret` | The key vault. The webhook secret is JSON `{"current", "previous"}` for rotation |
| `aws_s3_bucket.shards` | The shard store: private, versioned, encrypted, noncurrent versions expire |
| `aws_lambda_function.receiver` with a Function URL | The webhook receiver; concurrency capped at 5 |
| `aws_dynamodb_table.seen` | `webhook-id`s seen, with a TTL |
| `aws_sqs_queue.events`, `.dlq` | Verified events for your workers; failures land in the dead-letter queue |
| `aws_iam_policy.ingest` | What your ingest workloads may do, attached to the roles you name |

## Parameters

| Variable | Default | Effect |
|---|---|---|
| `name` | required | Prefix for every resource |
| `ingest_role_arns` | `[]` | Roles that get the ingest policy |
| `shard_retention_days` | 30 | Days noncurrent segment versions are kept |
| `dedupe_ttl_hours` | 48 | How long a `webhook-id` is remembered |
| `tags` | `{}` | Added to everything |

## Apply

```bash
cd terraform/aws/delve-partner
cp examples.tfvars prod.tfvars    # edit
terraform init
terraform plan -var-file=prod.tfvars
terraform apply -var-file=prod.tfvars
terraform output webhook_url
```

## Verify

| Check | Expect |
|---|---|
| `curl -X POST "$(terraform output -raw webhook_url)" -d '{}'` | 400 `invalid`: an unsigned delivery is refused |
| A test job with your staging key | A message on the events queue, the `webhook-id` in the table |
| `aws s3api get-public-access-block --bucket "$(terraform output -raw shard_bucket)"` | Every setting `true` |

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Every delivery 400 | Secret not put, or put as a plain string | Put `{"current": "whsec_..."}` |
| Deliveries 400 after a rotation | Only the new secret stored | Store the old one as `previous` |
| Messages on the dead-letter queue | Your worker fails on them | Read one, fix the worker, redrive |
