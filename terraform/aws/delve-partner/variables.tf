variable "name" {
  description = "Prefix for every resource, e.g. exampleco-delve-prod."
  type        = string
}

variable "ingest_role_arns" {
  description = "IAM roles of your workloads that call Patternode. They get read access to the live key and write access to the shard store."
  type        = list(string)
  default     = []
}

variable "shard_retention_days" {
  description = "Days to keep noncurrent versions of stored segments. Current versions are kept until you delete them."
  type        = number
  default     = 30
}

variable "dedupe_ttl_hours" {
  description = "How long a webhook-id is remembered. Patternode retries for well under a day."
  type        = number
  default     = 48
}

variable "tags" {
  type    = map(string)
  default = {}
}
