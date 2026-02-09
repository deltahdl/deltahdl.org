output "arn_for_central_logs_bucket" {
  value = module.central_logs.bucket_arn
}

output "arn_for_central_logs_write_policy" {
  value = module.central_logs.write_policy_arn
}

output "arn_for_github_actions_role" {
  value = module.github_oidc.github_actions_role_arn
}

output "name_for_github_actions_role" {
  value = module.github_oidc.github_actions_role_name
}

output "arn_for_oidc_provider" {
  value = module.github_oidc.oidc_provider_arn
}

output "arn_for_state_bucket" {
  value = aws_s3_bucket.opentofu_state.arn
}

output "hosted_zone_id" {
  value = module.domain.hosted_zone_id
}

output "name_for_cloudtrail" {
  value = module.cloudtrail.trail_name
}
