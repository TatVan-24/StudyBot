output "frontend_bucket_name" {
  description = "Frontend bucket name"
  value       = module.storage.frontend_bucket_id
}

output "document_bucket_name" {
  description = "Document bucket name"
  value       = module.storage.document_bucket_id
}

output "frontend_bucket_domain" {
  description = "Frontend bucket regional domain name"
  value       = module.storage.frontend_bucket_regional_domain_name
}

output "document_bucket_domain" {
  description = "Document bucket regional domain name"
  value       = module.storage.document_bucket_regional_domain_name
}

output "jobs_table_name" {
  value = module.database.jobs_table_name
}

output "documents_table_name" {
  value = module.database.documents_table_name
}

output "interactive_queue_url" {
  value = module.messaging.interactive_queue_url
}

output "document_queue_url" {
  value = module.messaging.document_queue_url
}

output "user_pool_id" {
  value = module.auth.user_pool_id
}

output "user_pool_endpoint" {
  value = module.auth.user_pool_endpoint
}

output "auth_client_id" {
  value = module.auth.client_id
}

output "api_endpoint" {
  value = module.api.api_endpoint
}

output "cloudfront_url" {
  value = "https://${module.frontend.distribution_domain_name}"
}
output "distribution_id" {
  value = module.frontend.distribution_id
}

output "sns_topic_arn" {
  description = "SNS Alert Topic ARN"
  value       = module.observability.sns_topic_arn
}

output "alarm_names" {
  description = "List of CloudWatch alarms created"
  value       = module.observability.alarm_names
}

output "auth_domain" {
  value = module.auth.domain
}