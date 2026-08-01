variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for infrastructure deployment"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Deployment environment (dev, staging, prod)"
}

variable "app_name" {
  type        = string
  default     = "redactmed"
  description = "Application lowercase name prefix"
}

variable "bedrock_model_id" {
  type        = string
  default     = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
  description = "Amazon Bedrock model ID for clinical entity detection"
}

variable "sqs_max_receive_count" {
  type        = number
  default     = 3
  description = "Max receive count before moving messages to DLQ"
}
