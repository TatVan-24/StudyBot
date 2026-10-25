data "aws_caller_identity" "current" {}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

module "storage" {
  source = "../../modules/storage"

  project              = var.project
  environment          = var.environment
  frontend_bucket_name = var.frontend_bucket_name
  document_bucket_name = var.document_bucket_name
  cors_allowed_origins = var.cors_allowed_origins
}

module "database" {
  source = "../../modules/database"

  project     = var.project
  environment = var.environment
}


module "messaging" {
  source = "../../modules/messaging"

  project     = var.project
  environment = var.environment
}

module "auth" {
  source      = "../../modules/auth"
  project     = var.project
  environment = var.environment

  callback_urls = [
    "https://${module.frontend.distribution_domain_name}"
  ]

  logout_urls = [
    "https://${module.frontend.distribution_domain_name}"
  ]
}

module "compute" {
  source = "../../modules/compute"

  account_id = data.aws_caller_identity.current.account_id

  table_jobs_name              = module.database.jobs_table_name
  table_documents_name         = module.database.documents_table_name
  table_sessions_name          = module.database.sessions_table_name
  table_session_documents_name = module.database.session_documents_table_name
  table_messages_name          = module.database.messages_table_name
  table_flashcards_name        = module.database.flashcards_table_name

  document_bucket_name = module.storage.document_bucket_id
  document_bucket_arn  = module.storage.document_bucket_arn

  interactive_queue_url = module.messaging.interactive_queue_url
  interactive_queue_arn = module.messaging.interactive_queue_arn
  document_queue_url    = module.messaging.document_queue_url
  document_queue_arn    = module.messaging.document_queue_arn

  user_pool_id  = module.auth.user_pool_id
  user_pool_arn = module.auth.user_pool_arn
}

# Thêm Event Notification S3 gọi Lambda (Giải quyết Circular Dependency)
resource "aws_s3_bucket_notification" "document" {
  bucket = module.storage.document_bucket_id

  lambda_function {
    lambda_function_arn = module.compute.ingestion_event_function_arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
    filter_suffix       = ".pdf"
  }
}

module "api" {
  source = "../../modules/api"

  project     = var.project
  environment = var.environment
  aws_region  = var.region

  user_pool_id       = module.auth.user_pool_id
  user_pool_endpoint = module.auth.user_pool_endpoint
  client_id          = module.auth.client_id

  document_invoke_arn     = module.compute.document_invoke_arn
  document_function_name  = module.compute.document_function_name
  session_invoke_arn      = module.compute.session_invoke_arn
  session_function_name   = module.compute.session_function_name
  query_invoke_arn        = module.compute.query_invoke_arn
  query_function_name     = module.compute.query_function_name
  flashcard_invoke_arn    = module.compute.flashcard_invoke_arn
  flashcard_function_name = module.compute.flashcard_function_name
  job_invoke_arn          = module.compute.job_invoke_arn
  job_function_name       = module.compute.job_function_name
}

module "frontend" {
  source = "../../modules/frontend"

  project     = var.project
  environment = var.environment

  frontend_bucket_id                   = module.storage.frontend_bucket_id
  frontend_bucket_arn                  = module.storage.frontend_bucket_arn
  frontend_bucket_regional_domain_name = module.storage.frontend_bucket_regional_domain_name
}

module "observability" {
  source = "../../modules/observability"

  project     = var.project
  environment = var.environment
  alert_email = var.alert_email

  lambda_function_names = [
    module.compute.ingestion_event_function_name,
    module.compute.document_function_name,
    module.compute.session_function_name,
    module.compute.query_function_name,
    module.compute.flashcard_function_name,
    module.compute.job_function_name
  ]

  queue_names = [
    "${var.project}-${var.environment}-interactive-queue",
    "${var.project}-${var.environment}-document-queue"
  ]

  dlq_names = [
    "${var.project}-${var.environment}-interactive-dlq",
    "${var.project}-${var.environment}-document-dlq"
  ]
}



# Tự động import các Log Group đã tồn tại trên AWS vào Terraform State
import {
  for_each = toset([
    module.compute.ingestion_event_function_name,
    module.compute.document_function_name,
    module.compute.session_function_name,
    module.compute.query_function_name,
    module.compute.flashcard_function_name,
    module.compute.job_function_name
  ])
  to = module.observability.aws_cloudwatch_log_group.lambda_log_groups[each.value]
  id = "/aws/lambda/${each.value}"
}