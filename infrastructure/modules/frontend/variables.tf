variable "project" { default = "studybot" }
variable "environment" { default = "dev" }
variable "frontend_bucket_id" { type = string }
variable "frontend_bucket_arn" { type = string }
variable "frontend_bucket_regional_domain_name" { type = string }
variable "default_root_object" { default = "index.html" }
variable "price_class" { default = "PriceClass_100" }
variable "default_ttl" { default = 3600 }