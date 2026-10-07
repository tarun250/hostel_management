terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }

  # Remote state (optional). Create the bucket first, then uncomment.
  # backend "s3" {
  #   bucket       = "hostelhub-tfstate-<account-id>"
  #   key          = "eks/terraform.tfstate"
  #   region       = "ap-south-1"
  #   use_lockfile = true
  # }
}

# Credentials come from the environment (aws configure / AWS_PROFILE / SSO).
# Nothing secret lives in this repo.
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.tags
  }
}
