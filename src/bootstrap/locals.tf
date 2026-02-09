locals {
  admin_iam_user                 = module.common.admin_iam_user
  aws_account_id                 = module.common.aws_account_id
  aws_region                     = module.common.aws_region
  domain_name                    = module.common.domain_name
  github_org                     = module.common.github_org
  name_for_central_logs_bucket   = module.common.name_for_central_logs_bucket
  name_for_cloudtrail            = "${local.resource_prefix}-cloudtrail"
  name_for_cloudtrail_bucket     = module.common.name_for_central_logs_bucket
  name_for_cloudtrail_iam_role   = "${local.resource_prefix}CloudTrailLogsRole"
  name_for_cloudtrail_log_group  = "/aws/cloudtrail/${local.resource_prefix}"
  name_for_github_actions_role   = "${local.resource_prefix}GitHubActionsRole"
  name_for_github_repo           = module.common.name_for_github_repo
  name_for_opentofu_state_bucket = module.common.name_for_opentofu_state_bucket
  resource_prefix                = module.common.resource_prefix
}
