variable "aws_region" {
  type        = string
  default     = "us-west-1"
  description = "The AWS region"
}

variable "lambda_memory_size" {
  type        = number
  default     = 512
  description = "Memory size to allocate for lambda (in megabytes)"
}

variable "domain_name" {
  type        = string
  description = "The domain name to use."
}

variable "cert_arn" {
  type        = string
  description = "The ARN of the ACM certificate to use for API Gateway."
}
