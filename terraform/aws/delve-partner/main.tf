# Partner-side infrastructure for Delve on AWS: where the keys live, where the segments are
# stored, and the endpoint that receives Patternode's webhooks. Nothing here runs at
# Patternode; nothing here holds a secret value. Secret values are put by a person, once,
# with `aws secretsmanager put-secret-value` (playbook, stage 5).

locals {
  tags = merge({ "managed-by" = "terraform", "integration" = "patternode-delve" }, var.tags)
}

data "aws_caller_identity" "this" {}
data "aws_region" "this" {}

# Keys -------------------------------------------------------------------------------

resource "aws_kms_key" "this" {
  description         = "${var.name}: Patternode keys, webhook secret and stored segments"
  enable_key_rotation = true
  tags                = local.tags
}

resource "aws_secretsmanager_secret" "live_key" {
  name        = "${var.name}/patternode/live-key"
  description = "Patternode live key (pnk_live_...). Put by a person; rotated every 90 days or sooner."
  kms_key_id  = aws_kms_key.this.arn
  tags        = local.tags
}

resource "aws_secretsmanager_secret" "webhook_secret" {
  name        = "${var.name}/patternode/webhook-secret"
  description = "Patternode webhook signing secret (whsec_...), as JSON {\"current\": \"...\", \"previous\": \"...\"}."
  kms_key_id  = aws_kms_key.this.arn
  tags        = local.tags
}

# The admin key is deliberately not stored here: it lives in your password manager, held by
# the named technical contacts, and is used only to create and rotate keys.

# Shard store ------------------------------------------------------------------------

resource "aws_s3_bucket" "shards" {
  bucket_prefix = "${var.name}-shards-"
  tags          = local.tags
}

resource "aws_s3_bucket_public_access_block" "shards" {
  bucket                  = aws_s3_bucket.shards.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "shards" {
  bucket = aws_s3_bucket.shards.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "shards" {
  bucket = aws_s3_bucket.shards.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.this.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "shards" {
  bucket = aws_s3_bucket.shards.id
  rule {
    id     = "noncurrent"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration { noncurrent_days = var.shard_retention_days }
  }
}

# Webhook receiver -------------------------------------------------------------------

resource "aws_dynamodb_table" "seen" {
  name         = "${var.name}-patternode-webhooks-seen"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "webhook_id"
  attribute {
    name = "webhook_id"
    type = "S"
  }
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
  point_in_time_recovery { enabled = true }
  tags = local.tags
}

resource "aws_sqs_queue" "dlq" {
  name                      = "${var.name}-patternode-events-dlq"
  message_retention_seconds = 1209600
  kms_master_key_id         = aws_kms_key.this.arn
  tags                      = local.tags
}

resource "aws_sqs_queue" "events" {
  name                       = "${var.name}-patternode-events"
  visibility_timeout_seconds = 120
  kms_master_key_id          = aws_kms_key.this.arn
  redrive_policy             = jsonencode({ deadLetterTargetArn = aws_sqs_queue.dlq.arn, maxReceiveCount = 5 })
  tags                       = local.tags
}

data "archive_file" "receiver" {
  type        = "zip"
  source_file = "${path.module}/lambda/receiver.py"
  output_path = "${path.module}/.build/receiver.zip"
}

resource "aws_iam_role" "receiver" {
  name = "${var.name}-patternode-webhook-receiver"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = "lambda.amazonaws.com" } }]
  })
  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "receiver_logs" {
  role       = aws_iam_role.receiver.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "receiver" {
  role = aws_iam_role.receiver.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = aws_secretsmanager_secret.webhook_secret.arn },
      { Effect = "Allow", Action = ["kms:Decrypt", "kms:GenerateDataKey"], Resource = aws_kms_key.this.arn },
      { Effect = "Allow", Action = ["dynamodb:PutItem"], Resource = aws_dynamodb_table.seen.arn },
      { Effect = "Allow", Action = ["sqs:SendMessage"], Resource = aws_sqs_queue.events.arn },
    ]
  })
}

resource "aws_lambda_function" "receiver" {
  function_name    = "${var.name}-patternode-webhook-receiver"
  role             = aws_iam_role.receiver.arn
  runtime          = "python3.12"
  handler          = "receiver.handler"
  filename         = data.archive_file.receiver.output_path
  source_code_hash = data.archive_file.receiver.output_base64sha256
  timeout          = 10
  memory_size      = 256
  # Bounds what a flood of forged deliveries can cost you; genuine traffic is a few a minute.
  reserved_concurrent_executions = 5
  environment {
    variables = {
      WEBHOOK_SECRET_ARN = aws_secretsmanager_secret.webhook_secret.arn
      SEEN_TABLE         = aws_dynamodb_table.seen.name
      EVENTS_QUEUE_URL   = aws_sqs_queue.events.url
      DEDUPE_TTL_HOURS   = tostring(var.dedupe_ttl_hours)
    }
  }
  tags = local.tags
}

resource "aws_cloudwatch_log_group" "receiver" {
  name              = "/aws/lambda/${aws_lambda_function.receiver.function_name}"
  retention_in_days = 30
}

# A Function URL is the smallest public HTTPS endpoint. The signature, not the network,
# is what authenticates Patternode; put API Gateway or CloudFront with WAF in front if your
# policy requires it.
resource "aws_lambda_function_url" "receiver" {
  function_name      = aws_lambda_function.receiver.function_name
  authorization_type = "NONE"
}

# Your workloads ---------------------------------------------------------------------

data "aws_iam_policy_document" "ingest" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.live_key.arn]
  }
  statement {
    actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = [aws_kms_key.this.arn]
  }
  statement {
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.shards.arn}/*"]
  }
  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.shards.arn]
  }
  statement {
    actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.events.arn]
  }
}

resource "aws_iam_policy" "ingest" {
  name   = "${var.name}-patternode-ingest"
  policy = data.aws_iam_policy_document.ingest.json
  tags   = local.tags
}

resource "aws_iam_role_policy_attachment" "ingest" {
  for_each   = toset([for arn in var.ingest_role_arns : element(split("/", arn), length(split("/", arn)) - 1)])
  role       = each.value
  policy_arn = aws_iam_policy.ingest.arn
}
