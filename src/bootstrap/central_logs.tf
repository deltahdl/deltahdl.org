module "central_logs" {
  source = "./modules/central_logs"

  bucket_name    = local.name_for_central_logs_bucket
  aws_account_id = local.aws_account_id
}
