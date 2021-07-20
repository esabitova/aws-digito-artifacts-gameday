import boto3
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def check_required_params(required_params, events):
    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')


def backup_targets(events: dict, context: dict) -> list:

    required_params = [
        "LoadBalancerArn"
    ]
    check_required_params(required_params, events)
    elb_client = boto3.client('elbv2')
    describe_params = {
        "LoadBalancerArn": events['LoadBalancerArn']
    }
    if "TargetGroupArns" in events and events['TargetGroupArns']:
        describe_params['TargetGroupArns'] = events['TargetGroupArns']
    paginator = elb_client.get_paginator('describe_target_groups')
    pages = paginator.paginate(**describe_params)
    res = []
    for page in pages:
        target_groups = page.get('TargetGroups')
        for target_group in target_groups:
            res.append({
                'TargetGroupArn': target_group['TargetGroupArn'],
                'LoadBalancerArn': events['LoadBalancerArn'],
                'HealthCheckProtocol': target_group['HealthCheckProtocol'],
                'HealthCheckPort': target_group['HealthCheckPort'],
                'HealthCheckEnabled': target_group['HealthCheckEnabled'],
                'HealthCheckIntervalSeconds': target_group['HealthCheckIntervalSeconds'],
                'HealthCheckTimeoutSeconds': target_group['HealthCheckTimeoutSeconds'],
                'HealthyThresholdCount': target_group['HealthyThresholdCount'],
                'UnhealthyThresholdCount': target_group['UnhealthyThresholdCount'],
                'HealthCheckPath': target_group['HealthCheckPath'],
                'Matcher': {
                    'HttpCode': target_group['Matcher']['HttpCode'],
                    'GrpcCode': target_group['Matcher']['GrpcCode'],
                },
            })
    return res


def break_targets_healthcheck_port(events: dict, context: dict) -> None:
    required_params = [
        "TargetGroups",
        "HealthCheckPort"
    ]
    check_required_params(required_params, events)
    elb_client = boto3.client('elbv2')
    for target_group in events['TargetGroups']:
        elb_client.modify_target_group(
            TargetGroupArn=target_group['TargetGroupArn'],
            HealthCheckEnabled=True,
            HealthCheckIntervalSeconds=10,
            HealthyThresholdCount=1,
            HealthCheckPort=events['HealthCheckPort']
        )


def restore_targets_healthcheck_port(events: dict, context: dict) -> None:
    required_params = [
        "TargetGroups",
    ]
    check_required_params(required_params, events)
    elb_client = boto3.client('elbv2')
    for target_group in events['TargetGroups']:
        elb_client.modify_target_group(**target_group)
