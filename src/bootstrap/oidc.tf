module "github_oidc" {
  source = "./modules/github_oidc"

  github_org                   = local.github_org
  github_repo                  = local.name_for_github_repo
  aws_account_id               = local.aws_account_id
  name_for_github_actions_role = local.name_for_github_actions_role

  depends_on = [module.cloudtrail]
}
