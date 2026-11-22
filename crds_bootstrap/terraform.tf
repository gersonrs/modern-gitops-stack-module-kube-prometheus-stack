terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = ">= 3"
    }
    utils = {
      source  = "cloudposse/utils"
      version = ">= 2"
    }
    null = {
      source  = "hashicorp/null"
      version = ">= 3"
    }
  }
  required_version = ">= 1.9.0"
}