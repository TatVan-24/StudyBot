data "archive_file" "lambda_zips" {
  for_each    = toset(local.lambdas)
  type        = "zip"
  source_dir  = "${path.module}/../../../src/lambdas"
  output_path = "${path.module}/.build/${each.key}.zip"
  excludes = [for l in local.lambdas : "${l}/*" if l != each.key]
}

resource "aws_lambda_function" "lambdas" {
  for_each         = toset(local.lambdas)
  function_name    = "${var.project}-${var.environment}-${each.key}"
  filename         = data.archive_file.lambda_zips[each.key].output_path
  source_code_hash = data.archive_file.lambda_zips[each.key].output_base64sha256
  handler          = "${each.key}.handler.lambda_handler"
  runtime          = var.lambda_runtime
  memory_size      = var.lambda_memory_mb
  timeout          = var.lambda_timeout_seconds
  role             = aws_iam_role.lambda_roles[each.key].arn

  environment {
    variables = {
      TABLE_JOBS              = var.table_jobs_name
      TABLE_DOCUMENTS         = var.table_documents_name
      TABLE_SESSIONS          = var.table_sessions_name
      TABLE_SESSION_DOCUMENTS = var.table_session_documents_name
      TABLE_MESSAGES          = var.table_messages_name
      TABLE_FLASHCARDS        = var.table_flashcards_name
      BUCKET_DOCUMENT         = var.document_bucket_name
      QUEUE_DOCUMENT_URL      = var.document_queue_url
      QUEUE_INTERACTIVE_URL   = var.interactive_queue_url
      USER_POOL_ID            = var.user_pool_id
    }
  }
}

# Cấp quyền riêng cho S3 gọi Lambda "ingestion_event"
resource "aws_lambda_permission" "s3_invoke" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambdas["ingestion_event"].function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.document_bucket_arn
}