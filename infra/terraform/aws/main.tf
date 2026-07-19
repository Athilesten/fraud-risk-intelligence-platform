terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "network" {
  source       = "./modules/network"
  project_name = var.project_name
}

module "s3_datalake" {
  source       = "./modules/s3_datalake"
  project_name = var.project_name
}

module "secrets" {
  source       = "./modules/secrets"
  project_name = var.project_name
}

module "rds" {
  source       = "./modules/rds"
  project_name = var.project_name
  vpc_id       = module.network.vpc_id
}

module "msk" {
  source       = "./modules/msk"
  project_name = var.project_name
  vpc_id       = module.network.vpc_id
}

module "ecs_or_eks" {
  source       = "./modules/ecs_or_eks"
  project_name = var.project_name
  vpc_id       = module.network.vpc_id
}
