terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    # Will be configured via backend-config
  }
}

provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source = "./modules/vpc"
  # VPC configuration will be added here
}

module "eks" {
  source = "./modules/eks"
  # EKS configuration will be added here
}

module "s3" {
  source = "./modules/s3"
  # S3 configuration for model storage will be added here
}

# Variables
variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-west-2"
}

# Outputs
output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "model_storage_bucket" {
  description = "S3 bucket for model storage"
  value       = module.s3.bucket_name
} 