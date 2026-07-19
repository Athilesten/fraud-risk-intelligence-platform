variable "project_name" {
  description = "Name prefix for fraud platform cloud resources."
  type        = string
  default     = "fraud-risk-platform"
}

variable "aws_region" {
  description = "AWS region for the production blueprint."
  type        = string
  default     = "us-east-1"
}
