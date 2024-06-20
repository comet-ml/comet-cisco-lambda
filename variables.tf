variable "comet_url_override" {
  description = "Key used within Lambda function for making calls to Comet API"
  type        = string
}

variable "comet_api_key" {
  description = "Key used within Lambda function for making calls to Comet API"
  type        = string
}

variable "comet_project" {
  description = "Project for the Comet API request"
  type        = string
}

variable "comet_workspace" {
  description = "Workspace for the Comet API request"
  type        = string
}