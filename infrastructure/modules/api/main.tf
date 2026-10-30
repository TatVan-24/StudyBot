resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project}-${var.environment}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = var.cors_allowed_origins
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Authorization", "Content-Type"]
    max_age       = 3600
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_authorizer" "jwt" {
  api_id           = aws_apigatewayv2_api.main.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "cognito-jwt"

  jwt_configuration {
    audience = [var.client_id]
    issuer   = "https://cognito-idp.${var.aws_region}.amazonaws.com/${var.user_pool_id}"
  }
}

# --- Cấu hình Router và Lambda ---
locals {
  lambdas = {
    document  = { invoke_arn = var.document_invoke_arn, function_name = var.document_function_name }
    session   = { invoke_arn = var.session_invoke_arn, function_name = var.session_function_name }
    query     = { invoke_arn = var.query_invoke_arn, function_name = var.query_function_name }
    flashcard = { invoke_arn = var.flashcard_invoke_arn, function_name = var.flashcard_function_name }
    job       = { invoke_arn = var.job_invoke_arn, function_name = var.job_function_name }
  }

  routes = {
    "POST /documents/uploads"                  = "document"
    "GET /documents"                           = "document"
    "GET /documents/{id}"                      = "document"
    "DELETE /documents/{id}"                   = "document"
    "POST /sessions"                           = "session"
    "GET /sessions"                            = "session"
    "DELETE /sessions/{id}"                    = "session"
    "GET /sessions/{id}"                       = "session"
    "POST /sessions/{id}/documents/{doc_id}"   = "session"
    "DELETE /sessions/{id}/documents/{doc_id}" = "session"
    "POST /sessions/{id}/questions"            = "query"
    "GET /sessions/{id}/messages"              = "query"
    "POST /sessions/{id}/flashcards"           = "flashcard"
    "GET /sessions/{id}/flashcards"            = "flashcard"
    "GET /jobs/{job_id}"                       = "job"
  }
}

resource "aws_apigatewayv2_integration" "lambdas" {
  for_each               = local.lambdas
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = each.value.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_lambda_permission" "apigw" {
  for_each      = local.lambdas
  statement_id  = "AllowAPIGatewayInvoke_${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_apigatewayv2_route" "routes" {
  for_each           = local.routes
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = each.key
  target             = "integrations/${aws_apigatewayv2_integration.lambdas[each.value].id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}
