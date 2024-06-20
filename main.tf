provider "aws" {
  region = "eu-west-1"
}

resource "aws_sns_topic" "comet_monitor_alerts" {
  name = "CometMonitorAlerts"
}

resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.comet_monitor_alerts.arn
  protocol  = "email"
  endpoint  = "deployment-team@comet.com" # Replace with your email
}

resource "aws_ssm_parameter" "comet_url_override" {
  name  = "/comet/cisco/comet_url_override"
  type  = "String"
  value = var.comet_url_override  # Replace with your actual URL override if any
}

resource "aws_ssm_parameter" "workspace" {
  name  = "/comet/cisco/workspace"
  type  = "String"
  value = var.comet_workspace # Replace with your workspace
}

resource "aws_ssm_parameter" "project" {
  name  = "/comet/cisco/project"
  type  = "String"
  value = var.comet_project # Replace with your project
}

resource "aws_ssm_parameter" "sns_topic_arn" {
  name  = "/comet/cisco/sns_topic_arn"
  type  = "String"
  value = aws_sns_topic.comet_monitor_alerts.arn
}

resource "aws_secretsmanager_secret" "comet_api_key" {
  name = "/comet/cisco/comet_api_key"
}

resource "aws_secretsmanager_secret_version" "comet_api_key_version" {
  secret_id = aws_secretsmanager_secret.comet_api_key.id
  secret_string = jsonencode({
    comet_api_key = var.comet_api_key # Replace with your API key
  })
}

resource "aws_s3_bucket" "lambda_bucket" {
  bucket = "comet-cisco-lambda-bucket"  # Replace with your bucket name
}

resource "aws_s3_object" "lambda_zip" {
  bucket = aws_s3_bucket.lambda_bucket.bucket
  key    = "comet_monitor.zip"
  source = "comet_monitor.zip"
  etag   = filemd5("comet_monitor.zip")
}

resource "aws_lambda_function" "comet_monitor" {
  function_name = "CometMonitorLambda"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.8"

  s3_bucket = "comet-cisco-lambda-bucket"
  s3_key    = "comet_monitor.zip"

  environment {
    variables = {
      SSM_PREFIX  = "/comet"
      SECRET_NAME = "/comet/cisco/comet_api_key"
    }
  }

  role = aws_iam_role.lambda_execution_role.arn
}

resource "aws_iam_role" "lambda_execution_role" {
  name = "lambda_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "lambda_policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "ssm:GetParameter",
          "secretsmanager:GetSecretValue",
          "sns:Publish"
        ]
        Effect = "Allow"
        Resource = [
          "arn:aws:logs:*:*:*",
          "arn:aws:ssm:*:*:parameter/comet/*",
          aws_secretsmanager_secret.comet_api_key.arn,
          aws_sns_topic.comet_monitor_alerts.arn
        ]
      },
      {
        Action = [
          "comet:getExperiment"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_cloudwatch_event_rule" "schedule_rule" {
  name                = "comet_monitor_schedule"
  description         = "Schedule for Comet monitoring"
  schedule_expression = "cron(0 12 * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.schedule_rule.name
  target_id = "comet_monitor_target"
  arn       = aws_lambda_function.comet_monitor.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.comet_monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule_rule.arn
}