output "admin_iam_user" {
  value = "jdrowne"
}

output "aws_account_id" {
  value = local.aws_account_id
}

output "aws_region" {
  value = local.aws_region
}

output "domain_name" {
  value = "deltahdl.org"
}

output "github_org" {
  value = "deltahdl"
}

output "name_for_central_logs_bucket" {
  value = "deltahdl-central-logs-us-east-2"
}

output "name_for_github_repo" {
  value = "deltahdl.org"
}

output "name_for_opentofu_state_bucket" {
  value = "deltahdl-opentofu-state-us-east-2"
}

output "resource_prefix" {
  value = local.resource_prefix
}
