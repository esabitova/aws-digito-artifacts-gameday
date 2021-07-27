import json
import boto3
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def check_required_params(required_params, events):
    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')


def backup_targets(events: dict, context: dict) -> str:

    required_params = [
        "LoadBalancerArn"
    ]
    check_required_params(required_params, events)
    elb_client = boto3.client('elbv2')
    paginator = elb_client.get_paginator('describe_target_groups')
    pages = paginator.paginate(
        LoadBalancerArn=events['LoadBalancerArn']
    )
    res = []
    for page in pages:
        target_groups = page.get('TargetGroups')
        for target_group in target_groups:

            backed_group = {
                'LoadBalancerArn': events['LoadBalancerArn'],
            }
            for key in [
                'TargetGroupArn',
                'HealthCheckProtocol',
                'HealthCheckPort',
                'HealthCheckEnabled',
                'HealthCheckIntervalSeconds',
                'HealthCheckTimeoutSeconds',
                'HealthyThresholdCount',
                'UnhealthyThresholdCount',
                'HealthCheckPath'
            ]:
                if target_group.get(key):
                    backed_group[key] = target_group.get(key)

            res.append(backed_group)
    return json.dumps(res)


def break_targets_healthcheck_port(events: dict, context: dict) -> None:
    required_params = [
        "TargetGroups",
        "HealthCheckPort"
    ]
    check_required_params(required_params, events)
    elb_client = boto3.client('elbv2')
    target_groups = json.loads(events['TargetGroups'])
    for target_group in target_groups:
        elb_client.modify_target_group(
            TargetGroupArn=target_group['TargetGroupArn'],
            HealthCheckEnabled=True,
            HealthCheckIntervalSeconds=10,
            HealthyThresholdCount=2,
            HealthCheckPort=str(events['HealthCheckPort'])
        )


def restore_targets_healthcheck_port(events: dict, context: dict) -> None:
    required_params = [
        "TargetGroups",
    ]
    check_required_params(required_params, events)
    target_groups = json.loads(events['TargetGroups'])
    elb_client = boto3.client('elbv2')
    for target_group in target_groups:
        target_group.pop('LoadBalancerArn')
        elb_client.modify_target_group(**target_group)
