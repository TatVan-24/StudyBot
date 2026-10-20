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

variable "frontend_bucket_name" {
  description = "Frontend bucket name"
  type        = string
}

variable "document_bucket_name" {
  description = "Document bucket name"
  type        = string
}

variable "enable_versioning" {
  description = "Enable versioning"
  type        = bool
  default     = true
}

variable "cors_allowed_origins" {
  description = "Cors allowed originsg"
  type        = list(string)
  default     = ["*"]
}