resource "aws_s3_bucket" "opentofu_state" {
  bucket        = local.name_for_opentofu_state_bucket
  force_destroy = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "opentofu_state" {
  bucket = aws_s3_bucket.opentofu_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "opentofu_state" {
  bucket = aws_s3_bucket.opentofu_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_logging" "opentofu_state" {
  bucket = aws_s3_bucket.opentofu_state.id

  target_bucket = local.name_for_cloudtrail_bucket
  target_prefix = "s3-access/opentofu-state/"
}

resource "aws_s3_bucket_policy" "opentofu_state" {
  bucket = aws_s3_bucket.opentofu_state.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowOpenTofuAccess"
        Effect = "Allow"
        Principal = {
          AWS = [
            "arn:aws:iam::${local.aws_account_id}:user/${local.admin_iam_user}",
            "arn:aws:iam::${local.aws_account_id}:role/${local.name_for_github_actions_role}"
          ]
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.opentofu_state.arn,
          "${aws_s3_bucket.opentofu_state.arn}/*"
        ]
      },
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.opentofu_state.arn,
          "${aws_s3_bucket.opentofu_state.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}
