locals {
  lambdas = ["document", "session", "query", "flashcard", "job", "ingestion_event"]
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_roles" {
  for_each           = toset(local.lambdas)
  name               = "${var.project}-${var.environment}-lambda-${each.key}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  for_each   = toset(local.lambdas)
  role       = aws_iam_role.lambda_roles[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# MVP: Tạm cấp quyền rộng một chút để các Lambda đều có thể chạy, 
# khi đưa lên Prod ta sẽ bóp chặt quyền lại sau.
resource "aws_iam_role_policy" "lambda_permissions" {
  for_each = toset(local.lambdas)
  name     = "lambda-${each.key}-policy"
  role     = aws_iam_role.lambda_roles[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["dynamodb:*"]
        Resource = ["arn:aws:dynamodb:${var.region}:${var.account_id}:table/${var.project}-${var.environment}-*"]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:*"]
        Resource = ["${var.document_bucket_arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["sqs:*"]
        Resource = ["arn:aws:sqs:${var.region}:${var.account_id}:${var.project}-${var.environment}-*"]
      }
    ]
  })
}