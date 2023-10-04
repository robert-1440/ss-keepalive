terraform {
  backend "s3" {
    bucket               = "infra-terraform-1440"
    key                  = "ss-keepalive/terraform.tfstate"
    region               = "us-west-1"
    workspace_key_prefix = "envs"
  }

}
