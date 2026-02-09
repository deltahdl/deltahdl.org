terraform {
  backend "s3" {
    bucket       = "deltahdl-opentofu-state-us-east-2"
    key          = "www-redirect/terraform.tfstate"
    region       = "us-east-2"
    encrypt      = true
    use_lockfile = true
  }
}
