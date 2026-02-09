output "bucket_name" {
  value = aws_s3_bucket.central_logs.id
}

output "bucket_arn" {
  value = aws_s3_bucket.central_logs.arn
}

output "bucket_id" {
  value = aws_s3_bucket.central_logs.id
}

output "write_policy_arn" {
  value = aws_iam_policy.central_logs_write.arn
}
