variable "region" {
    description = "AWS region"
    type = string
    default = "ap-southeast-2"
}

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

variable "document_bucket_name" {
  description = "Document bucket name"
  type        = string
}

variable "cors_allowed_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["*"]
}

variable "frontend_bucket_name" {
  description = "Frontend bucket name"
  type        = string
}

variable "alert_email" {
  description = "Email address for CloudWatch & Budget SNS alerts"
  type        = string
  default     = ""
}