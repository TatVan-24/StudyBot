output "jobs_table_name" {
  value = aws_dynamodb_table.jobs.name
}

output "jobs_table_arn" {
  value = aws_dynamodb_table.jobs.arn
}

output "documents_table_name" {
  value = aws_dynamodb_table.documents.name
}

output "documents_table_arn" {
  value = aws_dynamodb_table.documents.arn
}

output "sessions_table_name" {
  value = aws_dynamodb_table.sessions.name
}

output "sessions_table_arn" {
  value = aws_dynamodb_table.sessions.arn
}

output "session_documents_table_name" {
  value = aws_dynamodb_table.session_documents.name
}

output "session_documents_table_arn" {
  value = aws_dynamodb_table.session_documents.arn
}

output "messages_table_name" {
  value = aws_dynamodb_table.messages.name
}

output "messages_table_arn" {
  value = aws_dynamodb_table.messages.arn
}

output "flashcards_table_name" {
  value = aws_dynamodb_table.flashcards.name
}

output "flashcards_table_arn" {
  value = aws_dynamodb_table.flashcards.arn
}

output "workers_table_name" {
  value = aws_dynamodb_table.workers.name
}

output "workers_table_arn" {
  value = aws_dynamodb_table.workers.arn
}
