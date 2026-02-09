module "cloudtrail" {
  source = "./modules/cloudtrail"

  trail_name                    = local.name_for_cloudtrail
  aws_account_id                = local.aws_account_id
  aws_region                    = local.aws_region
  name_for_cloudtrail_bucket    = local.name_for_cloudtrail_bucket
  name_for_cloudtrail_log_group = local.name_for_cloudtrail_log_group
  name_for_cloudtrail_iam_role  = local.name_for_cloudtrail_iam_role
}
