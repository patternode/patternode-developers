output "webhook_url" {
  description = "Set this as webhook_url with PATCH /v1/account (playbook, stage 5)."
  value       = aws_lambda_function_url.receiver.function_url
}

output "live_key_secret_arn" {
  value = aws_secretsmanager_secret.live_key.arn
}

output "webhook_secret_arn" {
  value = aws_secretsmanager_secret.webhook_secret.arn
}

output "shard_bucket" {
  value = aws_s3_bucket.shards.bucket
}

output "events_queue_url" {
  description = "Verified, deduplicated Patternode events, for your workers."
  value       = aws_sqs_queue.events.url
}

output "ingest_policy_arn" {
  value = aws_iam_policy.ingest.arn
}
