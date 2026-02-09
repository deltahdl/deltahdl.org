terraform {
  required_version = ">= 1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = local.aws_region

  default_tags {
    tags = {
      ManagedBy = "OpenTofu"
      Project   = "DeltaHDL"
      Stack     = "redirect"
    }
  }
}

provider "aws" {
  alias  = "us-east-1"
  region = "us-east-1"

  default_tags {
    tags = {
      ManagedBy = "OpenTofu"
      Project   = "DeltaHDL"
      Stack     = "redirect"
    }
  }
}
