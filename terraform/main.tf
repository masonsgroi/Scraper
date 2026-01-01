# AWS Provider Configuration
provider "aws" {
  region = "us-west-2"
}

# Data source for current AWS account ID
data "aws_caller_identity" "current" {}

# ECR Repository for Docker images
resource "aws_ecr_repository" "scraper" {
  name                 = "scraper"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name    = "scraper"
    Project = "scraper"
  }
}

# IAM Role for Lambda function
resource "aws_iam_role" "lambda_role" {
  name = "scraper-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name    = "scraper-lambda-role"
    Project = "scraper"
  }
}

# Attach AdministratorAccess policy to Lambda role
# Note: In production, use a more restrictive policy
resource "aws_iam_role_policy_attachment" "lambda_admin" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

# Lambda Function
resource "aws_lambda_function" "scraper" {
  function_name = "scraper"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.scraper.repository_url}:latest"
  timeout       = 60
  memory_size   = 512

  tags = {
    Name    = "scraper"
    Project = "scraper"
  }

  # Lifecycle rule to prevent destruction/recreation on image updates
  lifecycle {
    ignore_changes = [image_uri]
  }
}

# Outputs
output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.scraper.repository_url
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.scraper.function_name
}

