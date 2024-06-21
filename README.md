
# Comet Monitor Lambda Function with Terraform

This repository contains the configuration for deploying a Lambda function to notify on Comet metric thresholds, on a regular schedule, using AWS services. The setup includes an S3 bucket for storing the Lambda function code package, Secrets Manager for storing your Comet API key, Systems Manager Parameter Store for other Comet environment variables, and CloudWatch Events for scheduling the Lambda function.

## Overview

- **Lambda Function**: Monitors a specified Comet metric and sends notifications via SNS if thresholds are breached.
- **S3 Bucket**: Stores the Lambda function code.
- **Secrets Manager**: Stores the Comet API key.
- **SSM Parameter Store**: Stores other Comet API request environment variables.
- **CloudWatch Events**: Schedules the Lambda function to run periodically.

## Prerequisites

- AWS CLI configured with appropriate permissions.
- Terraform installed.

## Setup Instructions

1. **Clone the Repository**:
    \`\`\`sh
    git clone https://github.com/your-repo/comet-monitor.git
    cd comet-monitor
    \`\`\`

2. **Create the Lambda Function ZIP**:
    Ensure \`lambda_function.py\` is updated as needed.
    \`\`\`sh
    zip comet_monitor.zip lambda_function.py
    \`\`\`

3. **Create \`terraform.tfvars\`**:
    Create a \`terraform.tfvars\` file in the root directory with your values. Example:
    \`\`\`hcl
    comet_url_override = "http://comet.your-company.net/clientlib/"
    comet_workspace = "your-workspace"
    comet_project = "your-project"
    comet_experiment_key = "your-experiment-key"
    comet_api_key = "your-api-key"
    comet_notification_email = "your@email.com"
    \`\`\`

4. **Update Terraform Configuration**:
    Ensure the S3 bucket name and paths in \`main.tf\` match your setup.

5. **Initialize Terraform**:
    \`\`\`sh
    terraform init
    \`\`\`

6. **Apply the Terraform Configuration**:
    \`\`\`sh
    terraform apply -var-file="terraform.tfvars"
    \`\`\`

## Detailed Configuration

### Lambda Function

The Lambda function monitors a specific Comet metric and sends notifications if the metric values breach the defined thresholds. The function retrieves configuration values from Secrets Manager and SSM Parameter Store.

### S3 Bucket

An S3 bucket is created to store the Lambda function code. The ZIP file is uploaded to this bucket.

### Secrets Manager

The Comet API key is stored securely in AWS Secrets Manager. Ensure the secret name \`/comet/cisco/comet_api_key\` is used.

### Parameter Store

Other parameters such as workspace, project, and SNS topic ARN are stored in Systems Manager Parameter Store with the following names:
- \`/comet/cisco/workspace\`
- \`/comet/cisco/project\`
- \`/comet/cisco/sns_topic_arn\`
- \`/comet/cisco/url-override\`

### CloudWatch Events

A CloudWatch Event Rule is created to schedule the Lambda function to run each day.