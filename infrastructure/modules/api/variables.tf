variable "project" { default = "studybot" }
variable "environment" { default = "dev" }
variable "aws_region" { type = string }
variable "user_pool_id" { type = string }
variable "user_pool_endpoint" { type = string }
variable "client_id" { type = string }
variable "cors_allowed_origins" { default = ["*"] }

variable "document_invoke_arn" { type = string }
variable "document_function_name" { type = string }
variable "session_invoke_arn" { type = string }
variable "session_function_name" { type = string }
variable "query_invoke_arn" { type = string }
variable "query_function_name" { type = string }
variable "flashcard_invoke_arn" { type = string }
variable "flashcard_function_name" { type = string }
variable "job_invoke_arn" { type = string }
variable "job_function_name" { type = string }