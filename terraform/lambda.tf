data "archive_file" "ingestion_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/lambda/ingestion"
  output_path = "${path.module}/builds/ingestion.zip"
}

resource "aws_lambda_function" "ingestion" {
  filename         = data.archive_file.ingestion_zip.output_path
  source_code_hash = data.archive_file.ingestion_zip.output_base64sha256
  function_name    = "${var.app_name}-ingestion"
  role             = aws_iam_role.ingestion_role.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  architectures    = ["arm64"]
  memory_size      = 256
  timeout          = 300

  environment {
    variables = {
      ENVIRONMENT      = var.environment
      LOG_LEVEL        = "INFO"
      QUEUE_URL        = aws_sqs_queue.main.queue_url
      BUCKET_NAME      = aws_s3_bucket.storage.bucket
      STATS_TABLE_NAME = aws_dynamodb_table.batch_stats.name
    }
  }
}

# Prepare worker source directory including agent and deidentification dependencies
resource "null_resource" "worker_prep" {
  triggers = {
    handler_hash = filemd5("${path.module}/../backend/lambda/worker/handler.py")
    agent_hash   = filemd5("${path.module}/../backend/agent/src/agent/agent.py")
  }

  provisioner "local-exec" {
    command = "python -c \"import shutil, os; dest=os.path.abspath('${path.module}/builds/worker_src'); shutil.rmtree(dest, ignore_errors=True); shutil.copytree(os.path.abspath('${path.module}/../backend/lambda/worker'), dest); shutil.copytree(os.path.abspath('${path.module}/../backend/agent/src/agent'), os.path.join(dest, 'agent')); shutil.copytree(os.path.abspath('${path.module}/../backend/deidentification/src/deidentification'), os.path.join(dest, 'deidentification'))\""
  }
}

data "archive_file" "worker_zip" {
  depends_on  = [null_resource.worker_prep]
  type        = "zip"
  source_dir  = "${path.module}/builds/worker_src"
  output_path = "${path.module}/builds/worker.zip"
}

resource "aws_lambda_function" "worker" {
  filename         = data.archive_file.worker_zip.output_path
  source_code_hash = data.archive_file.worker_zip.output_base64sha256
  function_name    = "${var.app_name}-worker"
  role             = aws_iam_role.worker_role.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  architectures    = ["arm64"]
  memory_size      = 1024
  timeout          = 120

  environment {
    variables = {
      ENVIRONMENT       = var.environment
      LOG_LEVEL         = "INFO"
      BUCKET_NAME       = aws_s3_bucket.storage.bucket
      BEDROCK_MODEL_ID  = var.bedrock_model_id
      STATS_TABLE_NAME  = aws_dynamodb_table.batch_stats.name
      MAX_RECEIVE_COUNT = tostring(var.sqs_max_receive_count)
    }
  }
}

resource "aws_lambda_event_source_mapping" "sqs_worker_trigger" {
  event_source_arn                   = aws_sqs_queue.main.arn
  function_name                      = aws_lambda_function.worker.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0
  function_response_types            = ["ReportBatchItemFailures"]
}

data "archive_file" "api_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/lambda/api"
  output_path = "${path.module}/builds/api.zip"
}

resource "aws_lambda_function" "api" {
  filename         = data.archive_file.api_zip.output_path
  source_code_hash = data.archive_file.api_zip.output_base64sha256
  function_name    = "${var.app_name}-api"
  role             = aws_iam_role.api_role.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  architectures    = ["arm64"]
  memory_size      = 256
  timeout          = 30

  environment {
    variables = {
      ENVIRONMENT             = var.environment
      LOG_LEVEL               = "INFO"
      BUCKET_NAME             = aws_s3_bucket.storage.bucket
      INGESTION_FUNCTION_NAME = aws_lambda_function.ingestion.function_name
      STATS_TABLE_NAME        = aws_dynamodb_table.batch_stats.name
      DLQ_URL                 = aws_sqs_queue.dlq.queue_url
      QUEUE_URL               = aws_sqs_queue.main.queue_url
    }
  }
}
