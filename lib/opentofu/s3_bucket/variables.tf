variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "force_destroy" {
  description = "Allow bucket to be destroyed even if not empty"
  type        = bool
  default     = false
}

variable "versioning_enabled" {
  description = "Enable versioning on the bucket"
  type        = bool
  default     = false
}

variable "central_logs_bucket" {
  description = "Name of the central logs bucket for access logging (null to disable logging)"
  type        = string
  default     = null
}

variable "log_prefix" {
  description = "Prefix for access logs in the central logs bucket"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to the bucket"
  type        = map(string)
  default     = {}
}
