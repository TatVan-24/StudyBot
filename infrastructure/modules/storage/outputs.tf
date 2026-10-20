output "frontend_bucket_id" {
  description = "Frontend bucket id"
  value       = aws_s3_bucket.frontend.id
}

output "frontend_bucket_arn" {
  description = "Frontend bucket arn"
  value       = aws_s3_bucket.frontend.arn
}

output "frontend_bucket_regional_domain_name" {
  description = "Frontend bucket regional domain name"
  value       = aws_s3_bucket.frontend.bucket_regional_domain_name
}

output "document_bucket_id" {
  description = "Document bucket id"
  value       = aws_s3_bucket.document.id
}

output "document_bucket_arn" {
  description = "Document bucket arn"
  value       = aws_s3_bucket.document.arn
}

output "document_bucket_regional_domain_name" {
  description = "Document bucket regional domain name"
  value       = aws_s3_bucket.document.bucket_regional_domain_name
}