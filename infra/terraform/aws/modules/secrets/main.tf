variable "project_name" {
  type = string
}

resource "aws_secretsmanager_secret" "app" {
  name = "${var.project_name}/app"
}

output "secrets_prefix" {
  value = aws_secretsmanager_secret.app.name
}
