output "interactive_queue_url" {
  value = aws_sqs_queue.interactive_queue.url
}

output "interactive_queue_arn" {
  value = aws_sqs_queue.interactive_queue.arn
}

output "interactive_dlq_arn" {
  value = aws_sqs_queue.interactive_dlq.arn
}

output "document_queue_url" {
  value = aws_sqs_queue.document_queue.url
}

output "document_queue_arn" {
  value = aws_sqs_queue.document_queue.arn
}

output "document_dlq_arn" {
  value = aws_sqs_queue.document_dlq.arn
}