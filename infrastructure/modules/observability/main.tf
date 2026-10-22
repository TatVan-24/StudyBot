# 1. CloudWatch Log Groups cho Lambda (retention 7 ngày)
resource "aws_cloudwatch_log_group" "lambda_log_groups" {
  for_each          = toset(var.lambda_function_names)
  name              = "/aws/lambda/${each.value}"
  retention_in_days = 7

  tags = {
    Name = "${var.project}-${var.environment}-log-group-${each.value}"
  }
}

# 2. SNS Topic nhận Cảnh báo
resource "aws_sns_topic" "alerts" {
  name = "${var.project}-${var.environment}-alerts"
}

# 3. Email Subscription (chỉ tạo khi var.alert_email không rỗng)
resource "aws_sns_topic_subscription" "email_alert" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# 4. Alarm DLQ Depth > 0 (Message đọng trong DLQ)
resource "aws_cloudwatch_metric_alarm" "dlq_depth" {
  for_each            = toset(var.dlq_names)
  alarm_name          = "${var.project}-${var.environment}-alarm-dlq-${each.value}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alarm when DLQ ${each.value} has 1 or more messages"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    QueueName = each.value
  }
}

# 5. Alarm Lambda Errors (Lỗi trong Lambda)
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each            = toset(var.lambda_function_names)
  alarm_name          = "${var.project}-${var.environment}-alarm-lambda-${each.value}-errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Alarm when Lambda function ${each.value} encounters errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = each.value
  }
}

# 6. Alarm SQS Oldest Message Age > 300s (Queue bị nghẽn)
resource "aws_cloudwatch_metric_alarm" "sqs_oldest_message_age" {
  for_each            = toset(var.queue_names)
  alarm_name          = "${var.project}-${var.environment}-alarm-sqs-${each.value}-age"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateAgeOfOldestMessage"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Maximum"
  threshold           = 300
  alarm_description   = "Alarm when oldest message in SQS queue ${each.value} exceeds 300s"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    QueueName = each.value
  }
}

# 7. AWS Budget Alert (Tùy chọn chi phí)
resource "aws_budgets_budget" "cost_budget" {
  count             = var.alert_email != "" ? 1 : 0
  name              = "${var.project}-${var.environment}-monthly-budget"
  budget_type       = "COST"
  limit_amount      = tostring(var.monthly_budget_usd)
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  time_period_start = "2026-01-01_00:00"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
}