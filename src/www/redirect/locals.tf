locals {
  aws_region            = module.common.aws_region
  domain_name           = module.common.domain_name
  apex_fqdn             = module.common.domain_name
  www_fqdn              = "www.${module.common.domain_name}"
  redirect_target       = "https://github.com/deltahdl/deltahdl"
  name_for_central_logs = module.common.name_for_central_logs_bucket
  resource_prefix       = "${module.common.resource_prefix}Redirect"
}
