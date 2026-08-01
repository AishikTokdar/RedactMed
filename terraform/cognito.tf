resource "aws_cognito_user_pool" "users" {
  name = "${var.app_name}-users"

  auto_verified_attributes = ["email"]
  username_attributes      = ["email"]

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = false
  }

  schema {
    attribute_data_type = "String"
    name                = "email"
    required            = true
    mutable             = true
  }

  schema {
    attribute_data_type = "String"
    name                = "given_name"
    required            = true
    mutable             = true
  }

  schema {
    attribute_data_type = "String"
    name                = "family_name"
    required            = true
    mutable             = true
  }
}

resource "aws_cognito_user_pool_client" "client" {
  name         = "${var.app_name}-web-client"
  user_pool_id = aws_cognito_user_pool.users.id

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  generate_secret = false
}
