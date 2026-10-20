variable "project" { default = "studybot" }
variable "environment" { default = "dev" }
variable "region" { default = "ap-southeast-2" }
variable "account_id" { type = string }
variable "lambda_runtime" { default = "python3.12" }
variable "lambda_memory_mb" { default = 512 }
variable "lambda_timeout_seconds" { default = 30 }
variable "source_dir" { default = "../../src/lambdas" }

variable "table_jobs_name" { type = string }
variable "table_documents_name" { type = string }
variable "table_sessions_name" { type = string }
variable "table_session_documents_name" { type = string }
variable "table_messages_name" { type = string }
variable "table_flashcards_name" { type = string }

variable "document_bucket_name" { type = string }
variable "document_bucket_arn" { type = string }

variable "interactive_queue_url" { type = string }
variable "interactive_queue_arn" { type = string }
variable "document_queue_url" { type = string }
variable "document_queue_arn" { type = string }

variable "user_pool_id" { type = string }
variable "user_pool_arn" { type = string }