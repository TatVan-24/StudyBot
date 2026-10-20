output "state_bucket_name" {
  description = "S3 bucket name for Terraform state"
  value       = aws_s3_bucket.tfstate.id
}

output "state_bucket_arn" {
  description = "S3 bucket ARN for Terraform state"
  value       = aws_s3_bucket.tfstate.arn
}

output "lock_table_name" {
  description = "DynamoDB table name for state lock"
  value       = aws_dynamodb_table.tflock.name
}

output "lock_table_arn" {
  description = "DynamoDB table ARN for state lock"
  value       = aws_dynamodb_table.tflock.arn
}