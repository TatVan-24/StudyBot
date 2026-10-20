variable "project" {
  description = "Project name"
  type        = string
  default     = "studybot"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "alert_email" {
  description = "Email address for SNS alert notifications"
  type        = string
  default     = ""
}

variable "lambda_function_names" {
  description = "List of Lambda function names to monitor"
  type        = list(string)
  default     = []
}

variable "queue_names" {
  description = "List of main SQS queue names to monitor"
  type        = list(string)
  default     = []
}

variable "dlq_names" {
  description = "List of DLQ queue names to monitor"
  type        = list(string)
  default     = []
}

variable "monthly_budget_usd" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 10
}