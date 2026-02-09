module "domain" {
  source = "./modules/domain"

  domain_name    = local.domain_name
  hosted_zone_id = var.hosted_zone_id

  depends_on = [module.cloudtrail]
}
