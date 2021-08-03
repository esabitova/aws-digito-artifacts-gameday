import json
import boto3
import logging


from botocore.config import Config

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
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    elb_client = boto3.client('elbv2', config=config)
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
    """
    :param events:
    :param context:
    """
    required_params = [
        "TargetGroups",
        "HealthCheckPort"
    ]
    check_required_params(required_params, events)
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    elb_client = boto3.client('elbv2', config=config)
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
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    elb_client = boto3.client('elbv2', config=config)
    for target_group in target_groups:
        target_group.pop('LoadBalancerArn')
        elb_client.modify_target_group(**target_group)


def remove_security_groups_from_list(events: dict, context: dict) -> list:
    """
    Return result of subtraction security_group ids from the original list of security group ids
    :param events: SecurityGroupIdsToDelete, SecurityGroups
    :param context:
    """
    required_params = [
        "SecurityGroups",
        "SecurityGroupIdsToDelete"
    ]
    check_required_params(required_params, events)

    security_group_ids_to_delete = events['SecurityGroupIdsToDelete']
    security_groups = events['SecurityGroups']

    new_security_groups = []
    for security_group in security_groups:
        if security_group not in security_group_ids_to_delete:
            new_security_groups.append(security_group)

    return new_security_groups


def get_length_of_list(events: dict, context: dict) -> int:
    """
    :param events:
    :param context:
    :return:
    """
    required_params = [
        "List"
    ]
    check_required_params(required_params, events)

    return len(events['List'])
