resource "aws_dynamodb_table" "batch_stats" {
  name         = "${var.app_name}-stats"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "batch_id"
  range_key    = "record_type"

  attribute {
    name = "batch_id"
    type = "S"
  }

  attribute {
    name = "record_type"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "BatchesByCreatedAt"
    hash_key        = "record_type"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }
}
