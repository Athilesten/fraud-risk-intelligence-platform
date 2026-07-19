variable "project_name" {
  type = string
}

resource "aws_vpc" "main" {
  cidr_block           = "10.40.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

output "vpc_id" {
  value = aws_vpc.main.id
}
