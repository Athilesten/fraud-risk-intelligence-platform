variable "project_name" {
  type = string
}

variable "vpc_id" {
  type = string
}

# Production target: Amazon MSK cluster with TLS, private subnets, security
# groups, encryption at rest, and SASL/SCRAM or IAM authentication.
locals {
  raw_topic     = "fraud.transactions.raw"
  scored_topic  = "fraud.transactions.scored"
  errors_topic  = "fraud.transactions.errors"
}
