output "ingestion_event_function_arn" { value = aws_lambda_function.lambdas["ingestion_event"].arn }
output "ingestion_event_function_name" { value = aws_lambda_function.lambdas["ingestion_event"].function_name }

output "document_invoke_arn" { value = aws_lambda_function.lambdas["document"].invoke_arn }
output "document_function_name" { value = aws_lambda_function.lambdas["document"].function_name }

output "session_invoke_arn" { value = aws_lambda_function.lambdas["session"].invoke_arn }
output "session_function_name" { value = aws_lambda_function.lambdas["session"].function_name }

output "query_invoke_arn" { value = aws_lambda_function.lambdas["query"].invoke_arn }
output "query_function_name" { value = aws_lambda_function.lambdas["query"].function_name }

output "flashcard_invoke_arn" { value = aws_lambda_function.lambdas["flashcard"].invoke_arn }
output "flashcard_function_name" { value = aws_lambda_function.lambdas["flashcard"].function_name }

output "job_invoke_arn" { value = aws_lambda_function.lambdas["job"].invoke_arn }
output "job_function_name" { value = aws_lambda_function.lambdas["job"].function_name }
