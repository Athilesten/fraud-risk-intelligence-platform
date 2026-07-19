variable "project_name" {
  type = string
}

resource "aws_s3_bucket" "datalake" {
  bucket = "${var.project_name}-datalake-placeholder"

  tags = {
    Name        = "${var.project_name}-datalake"
    Environment = "blueprint"
  }
}

output "bucket_name" {
  value = aws_s3_bucket.datalake.bucket
}
