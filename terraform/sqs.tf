resource "aws_sqs_queue" "dlq" {
  name                      = "${var.app_name}-dlq"
  message_retention_seconds = 1209600 # 14 days
}

resource "aws_sqs_queue" "main" {
  name                       = "${var.app_name}-queue"
  visibility_timeout_seconds = 360 # 6 minutes
  message_retention_seconds  = 345600 # 4 days

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.sqs_max_receive_count
  })
}
