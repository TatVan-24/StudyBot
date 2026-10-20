output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "log_group_names" {
  description = "List of CloudWatch Log Group names created for Lambda functions"
  value       = [for lg in aws_cloudwatch_log_group.lambda_log_groups : lg.name]
}

output "alarm_names" {
  description = "List of CloudWatch Metric Alarm names"
  value = concat(
    [for a in aws_cloudwatch_metric_alarm.dlq_depth : a.alarm_name],
    [for a in aws_cloudwatch_metric_alarm.lambda_errors : a.alarm_name],
    [for a in aws_cloudwatch_metric_alarm.sqs_oldest_message_age : a.alarm_name]
  )
}