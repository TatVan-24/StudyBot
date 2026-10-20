variable "region" {
  description = "AWS Region deploy infracstructure"
  type        = string
  default     = "ap-southeast-2"
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

variable "state_bucket_name" {
  description = "Globally unique S3 bucket name for Terraform state"
  type        = string
}

variable "lock_table_name" {
  description = "DynamoDB table name for Terraform state lock"
  type        = string
  default     = "studybot-tflock"
}