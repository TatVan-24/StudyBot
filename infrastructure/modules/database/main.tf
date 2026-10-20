# 1. StudyBotJobs
resource "aws_dynamodb_table" "jobs" {
  name         = "${var.project}-${var.environment}-jobs"
  billing_mode = var.billing_mode
  hash_key     = "job_id"

  attribute {
    name = "job_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery
  }

  lifecycle {
    prevent_destroy = true
  }
}

# 2. StudyBotDocuments
resource "aws_dynamodb_table" "documents" {
  name         = "${var.project}-${var.environment}-documents"
  billing_mode = var.billing_mode
  hash_key     = "document_id"

  attribute {
    name = "document_id"
    type = "S"
  }
  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "UserDocuments"
    hash_key        = "user_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery
  }

  lifecycle {
    prevent_destroy = true
  }
}

# 3. StudyBotSessions
resource "aws_dynamodb_table" "sessions" {
  name         = "${var.project}-${var.environment}-sessions"
  billing_mode = var.billing_mode
  hash_key     = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }
  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "updated_at"
    type = "S"
  }

  global_secondary_index {
    name            = "UserSessions"
    hash_key        = "user_id"
    range_key       = "updated_at"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery
  }

  lifecycle {
    prevent_destroy = true
  }
}

# 4. StudyBotSessionDocuments
resource "aws_dynamodb_table" "session_documents" {
  name         = "${var.project}-${var.environment}-session-documents"
  billing_mode = var.billing_mode
  hash_key     = "session_id"
  range_key    = "document_id"

  attribute {
    name = "session_id"
    type = "S"
  }
  attribute {
    name = "document_id"
    type = "S"
  }

  global_secondary_index {
    name            = "DocumentSessions"
    hash_key        = "document_id"
    range_key       = "session_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery
  }

  lifecycle {
    prevent_destroy = true
  }
}

# 5. StudyBotMessages
resource "aws_dynamodb_table" "messages" {
  name         = "${var.project}-${var.environment}-messages"
  billing_mode = var.billing_mode
  hash_key     = "session_id"
  range_key    = "message_id"

  attribute {
    name = "session_id"
    type = "S"
  }
  attribute {
    name = "message_id" # Chứa format: created_at#message_id
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery
  }

  lifecycle {
    prevent_destroy = true
  }
}

# 6. StudyBotFlashcards
resource "aws_dynamodb_table" "flashcards" {
  name         = "${var.project}-${var.environment}-flashcards"
  billing_mode = var.billing_mode
  hash_key     = "session_id"
  range_key    = "flashcard_id"

  attribute {
    name = "session_id"
    type = "S"
  }
  attribute {
    name = "flashcard_id"
    type = "S"
  }
  attribute {
    name = "document_id"
    type = "S"
  }

  global_secondary_index {
    name            = "DocumentFlashcards"
    hash_key        = "document_id"
    range_key       = "flashcard_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery
  }

  lifecycle {
    prevent_destroy = true
  }
}

# 7. StudyBotWorkers
resource "aws_dynamodb_table" "workers" {
  name         = "${var.project}-${var.environment}-workers"
  billing_mode = var.billing_mode
  hash_key     = "worker_id"

  attribute {
    name = "worker_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery
  }

  lifecycle {
    prevent_destroy = true
  }
}