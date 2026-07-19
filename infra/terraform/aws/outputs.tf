output "vpc_id" {
  description = "Placeholder VPC id from the network module."
  value       = module.network.vpc_id
}

output "datalake_bucket_name" {
  description = "Placeholder S3 bucket name for the Delta Lake."
  value       = module.s3_datalake.bucket_name
}

output "secrets_prefix" {
  description = "Secret path prefix used by the application."
  value       = module.secrets.secrets_prefix
}
