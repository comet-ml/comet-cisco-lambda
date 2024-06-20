import json
import boto3
from comet_ml import API

ssm_client = boto3.client('ssm')
secrets_client = boto3.client('secretsmanager')
sns_client = boto3.client('sns')

def get_parameter(name):
    response = ssm_client.get_parameter(Name=name, WithDecryption=True)
    return response['Parameter']['Value']

def get_secret(name):
    response = secrets_client.get_secret_value(SecretId=name)
    return json.loads(response['SecretString'])[name]

def get_experiment(api_key, workspace, project_name, experiment_key):
    api = API(api_key=api_key)
    return api.get_experiment(workspace=workspace, project_name=project_name, experiment=experiment_key)

def check_metric_thresholds(experiment, metric_name, threshold_high, threshold_low):
    metric = experiment.get_metrics(metric_name)
    last_value = float(metric[-1]['metricValue'])
    if last_value > threshold_high:
        return f"Notification: {metric_name} value too high: {last_value}"
    elif last_value < threshold_low:
        return f"Notification: {metric_name} value too low: {last_value}"
    else:
        return "All good - no notification"

def send_notification(message, topic_arn):
    sns_client.publish(
        TopicArn=topic_arn,
        Message=message,
        Subject="Comet Metric Alert"
    )

def lambda_handler(event, context):
    COMET_URL_OVERRIDE = get_parameter('/comet/cisco/comet_url_override')
    WORKSPACE = get_parameter('/comet/cisco/workspace')
    PROJECT = get_parameter('/comet/cisco/project')
    COMET_API_KEY = get_secret('/comet/cisco/comet_api_key')
    EXPERIMENT_KEY = 'network0000700000000000000000000010'
    THRESHOLD_HIGH = 0.4
    THRESHOLD_LOW = 0.1
    METRIC = 'logMediaBitsPerSec_performance'
    SNS_TOPIC_ARN = get_parameter('/comet/cisco/sns_topic_arn')

    experiment = get_experiment(COMET_URL_OVERRIDE, COMET_API_KEY, WORKSPACE, PROJECT, EXPERIMENT_KEY)
    notification_message = check_metric_thresholds(experiment, METRIC, THRESHOLD_HIGH, THRESHOLD_LOW)

    if "Notification" in notification_message:
        send_notification(notification_message, SNS_TOPIC_ARN)

    return {
        'statusCode': 200,
        'body': json.dumps(notification_message)
    }