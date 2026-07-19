variable "project_name" {
  type = string
}

variable "vpc_id" {
  type = string
}

# Production target: deploy FastAPI and optional frontend containers to ECS
# Fargate or EKS behind an HTTPS load balancer.
locals {
  fastapi_container  = "${var.project_name}-fastapi"
  frontend_container = "${var.project_name}-frontend"
}
