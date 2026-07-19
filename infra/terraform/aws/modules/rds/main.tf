variable "project_name" {
  type = string
}

variable "vpc_id" {
  type = string
}

# Blueprint placeholder. Add aws_db_instance, subnet groups, security groups,
# parameter groups, and Secrets Manager password wiring before applying.
locals {
  engine            = "postgres"
  recommended_class = "db.t4g.medium"
  database_name     = "fraud_db"
}
