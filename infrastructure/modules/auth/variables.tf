variable "project" {
  description = "Project name"
  type        = string
  default     = "studybot"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "password_minimum_length" {
  description = "Minimum password length"
  type        = number
  default     = 8
}

variable "password_require_uppercase" {
  type    = bool
  default = true
}

variable "password_require_lowercase" {
  type    = bool
  default = true
}

variable "password_require_numbers" {
  type    = bool
  default = true
}

variable "password_require_symbols" {
  type    = bool
  default = true
}

variable "callback_urls" {
  type    = list(string)
  default = ["http://localhost:3000"]
}

variable "logout_urls" {
  type    = list(string)
  default = ["http://localhost:3000"]
}

variable "mfa_configuration" {
  type    = string
  default = "OFF"
}