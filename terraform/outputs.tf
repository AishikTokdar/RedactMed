output "bucket_name" {
  value       = aws_s3_bucket.storage.bucket
  description = "Name of the S3 storage bucket"
}

output "api_url" {
  value       = "${aws_api_gateway_stage.prod.invoke_url}/"
  description = "Invoke URL for the REST API Gateway"
}

output "user_pool_id" {
  value       = aws_cognito_user_pool.users.id
  description = "Amazon Cognito User Pool ID"
}

output "user_pool_client_id" {
  value       = aws_cognito_user_pool_client.client.id
  description = "Amazon Cognito User Pool Client ID"
}

output "aws_region" {
  value       = var.aws_region
  description = "AWS Deployment Region"
}

output "sqs_queue_url" {
  value       = aws_sqs_queue.main.queue_url
  description = "Main SQS Queue URL"
}

output "dlq_queue_url" {
  value       = aws_sqs_queue.dlq.queue_url
  description = "Dead-Letter Queue URL"
}

output "dynamodb_table_name" {
  value       = aws_dynamodb_table.batch_stats.name
  description = "DynamoDB Batch Stats Table Name"
}
