# 1. Cognito User Pool
resource "aws_cognito_user_pool" "main" {
  name = "${var.project}-${var.environment}-user-pool"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]
  mfa_configuration        = var.mfa_configuration

  password_policy {
    minimum_length    = var.password_minimum_length
    require_uppercase = var.password_require_uppercase
    require_lowercase = var.password_require_lowercase
    require_numbers   = var.password_require_numbers
    require_symbols   = var.password_require_symbols
  }

  admin_create_user_config {
    allow_admin_create_user_only = false
  }
}

# 2. Cognito User Pool Client
resource "aws_cognito_user_pool_client" "main" {
  name         = "${var.project}-${var.environment}-client"
  user_pool_id = aws_cognito_user_pool.main.id

  # Quan trọng: Không dùng secret cho SPA (Frontend)
  generate_secret = false
  
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH", 
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_ADMIN_USER_PASSWORD_AUTH" # Bật luồng này để bạn có thể test dễ dàng bằng AWS CLI
  ]

  callback_urls                        = var.callback_urls
  logout_urls                          = var.logout_urls
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  allowed_oauth_flows_user_pool_client = true
  supported_identity_providers         = ["COGNITO"]
}