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

variable "visibility_timeout_seconds" {
  description = "Visibility timeout seconds"
  type        = number
  default     = 300
}

variable "message_retention_seconds" {
  description = "Message retention seconds"
  type        = number
  default     = 345600
}

variable "max_receive_count" {
  description = "Max receive count"
  type        = number
  default     = 3
}