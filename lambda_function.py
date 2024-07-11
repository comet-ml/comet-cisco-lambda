import json
import time
import os
import boto3
from comet_ml import API

ssm_client = boto3.client('ssm')
secrets_client = boto3.client('secretsmanager')
sns_client = boto3.client('sns')

def get_parameter(name):
    try:
        response = ssm_client.get_parameter(Name=name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Error getting parameter {name}: {e}")
        raise

def get_secret(name):
    try:
        response = secrets_client.get_secret_value(SecretId=name)
        return json.loads(response['SecretString'])[name.split('/')[-1]]
    except Exception as e:
        print(f"Error getting secret {name}: {e}")
        raise

def send_notification(customer, kpi, value, lowthres, highthres, exp, sns_topic_arn):
    other_lastdate = 'notification_kpi_' + kpi + '_lastdate'
    message = ""

    if value < lowthres:
        message = f'Notification for customer {customer}: KPI ({kpi}) value ({value}) below Low Threshold ({lowthres})'
        exp.log_other(other_lastdate, time.time())
    elif value > highthres:
        message = f'Notification for customer {customer}: KPI ({kpi}) value ({value}) above High Threshold ({highthres})'
        exp.log_other(other_lastdate, time.time())

    if message:
        try:
            print(message)
            sns_client.publish(
                TopicArn=sns_topic_arn,
                Message=message,
                Subject="Comet Metric Alert"
            )
        except Exception as e:
            print(f"Error sending SNS notification: {e}")

def get_experiments(api_key, workspace, project_name):
    try:
        api = API(api_key=api_key, cache=False)
        return api.get_experiments(workspace=workspace, project_name=project_name)
    except Exception as e:
        print(f"Error getting experiments for project {project_name} in workspace {workspace}: {e}")
        return []

def safe_get_summary(exp, key):
    try:
        summary = exp.get_others_summary(key)
        return summary[0] if summary else None
    except Exception as e:
        print(f"Error getting summary for key {key}: {e}")
        return None

def lambda_handler(event, context):
    try:
        COMET_API_KEY = get_secret('/comet/cisco/comet_api_key')
        WORKSPACE = get_parameter('/comet/cisco/workspace')
        PROJECT = get_parameter('/comet/cisco/project')
        SNS_TOPIC_ARN = get_parameter('/comet/cisco/sns_topic_arn')
        COMET_URL_OVERRIDE = get_parameter('/comet/cisco/comet_url_override')

        if COMET_URL_OVERRIDE:
            os.environ['COMET_URL_OVERRIDE'] = COMET_URL_OVERRIDE

        experiments = get_experiments(COMET_API_KEY, WORKSPACE, PROJECT)

        if not experiments:
            return {
                'statusCode': 404,
                'body': json.dumps(f"No experiments found for project {PROJECT} in workspace {WORKSPACE}")
            }

        kpis = ['avgHasFailed_performance', 'logTotalBitsPerSec_performance',
                'numAuthFailures_performance', 'numDhcpFailures_performance']

        for exp in experiments:
            for kpi in kpis:
                other_ena = 'notification_kpi_' + kpi + '_enabled'
                other_config = 'notification_kpi_' + kpi + '_config'

                ena_value = safe_get_summary(exp, other_ena)
                if ena_value == '1':
                    cust_id = safe_get_summary(exp, 'cust-id')
                    metric_summary = exp.get_metrics(kpi)
                    if metric_summary:
                        try:
                            value = float(metric_summary[-1]['metricValue'])
                        except (IndexError, ValueError) as e:
                            print(f"Error parsing metric value for KPI {kpi}: {e}")
                            continue
                        config_summary = safe_get_summary(exp, other_config)
                        if config_summary:
                            try:
                                config = json.loads(config_summary)
                                lowthres = config['threshold_low']
                                highthres = config['threshold_high']
                            except (json.JSONDecodeError, KeyError) as e:
                                print(f"Error parsing config for KPI {kpi}: {e}")
                                continue

                            if value < lowthres or value > highthres:
                                send_notification(cust_id, kpi, value, lowthres, highthres, exp, SNS_TOPIC_ARN)

        return {
            'statusCode': 200,
            'body': json.dumps("Execution completed")
        }
    except Exception as e:
        print(f"Unhandled error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Unhandled error: {e}")
        }