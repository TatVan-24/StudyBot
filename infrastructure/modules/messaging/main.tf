# 1. Interactive DLQ
resource "aws_sqs_queue" "interactive_dlq" {
  name                      = "${var.project}-${var.environment}-interactive-dlq"
  message_retention_seconds = 1209600 # 14 days
}

# 2. Document DLQ
resource "aws_sqs_queue" "document_dlq" {
  name                      = "${var.project}-${var.environment}-document-dlq"
  message_retention_seconds = 1209600 # 14 days
}

# 3. Interactive Queue
resource "aws_sqs_queue" "interactive_queue" {
  name                       = "${var.project}-${var.environment}-interactive-queue"
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.interactive_dlq.arn
    maxReceiveCount     = var.max_receive_count
  })
}

# 4. Document Queue
resource "aws_sqs_queue" "document_queue" {
  name                       = "${var.project}-${var.environment}-document-queue"
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.document_dlq.arn
    maxReceiveCount     = var.max_receive_count
  })
}