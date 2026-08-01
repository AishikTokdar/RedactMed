resource "random_string" "bucket_suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "aws_s3_bucket" "storage" {
  bucket        = "${var.app_name}-storage-${random_string.bucket_suffix.result}"
  force_destroy = false
}

resource "aws_s3_bucket_public_access_block" "public_block" {
  bucket = aws_s3_bucket.storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
