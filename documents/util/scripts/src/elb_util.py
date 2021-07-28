import random

import boto3
import logging
import string

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
                'TargetGroupArn': target_group.get('TargetGroupArn'),
                'LoadBalancerArn': events['LoadBalancerArn'],
                'HealthCheckProtocol': target_group.get('HealthCheckProtocol'),
                'HealthCheckPort': target_group.get('HealthCheckPort'),
                'HealthCheckEnabled': target_group.get('HealthCheckEnabled'),
                'HealthCheckIntervalSeconds': target_group.get('HealthCheckIntervalSeconds'),
                'HealthCheckTimeoutSeconds': target_group.get('HealthCheckTimeoutSeconds'),
                'HealthyThresholdCount': target_group.get('HealthyThresholdCount'),
                'UnhealthyThresholdCount': target_group.get('UnhealthyThresholdCount'),
                'HealthCheckPath': target_group.get('HealthCheckPath'),
                'Matcher': {
                    'HttpCode': target_group.get('Matcher', {}).get('HttpCode'),
                    'GrpcCode': target_group.get('Matcher', {}).get('GrpcCode'),
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
            HealthyThresholdCount=2,
            HealthCheckPort=str(events['HealthCheckPort'])
        )


def restore_targets_healthcheck_port(events: dict, context: dict) -> None:
    required_params = [
        "TargetGroups",
    ]
    check_required_params(required_params, events)
    elb_client = boto3.client('elbv2')
    for target_group in events['TargetGroups']:
        target_group.pop('LoadBalancerArn')
        elb_client.modify_target_group(**target_group)


def remove_security_group_from_alb(events: dict, context: dict) -> None:
    required_params = [
        "LoadBalancerArn",
        "SecurityGroupIdsToDelete"
    ]
    check_required_params(required_params, events)
    elb_client = boto3.client('elbv2')

    describe_params = {
        'LoadBalancerArns': [events['LoadBalancerArn']]
    }

    # security_group_ids_to_delete = events['SecurityGroupIdsToDelete']
    # if security_group_ids_to_delete:
    #     pass
    # else:

    # create an empty security group
    ec2_client = boto3.client('ec2')
    sg_description = 'inject_failure_sg_descr_' + ''.join(random.choice(string.ascii_uppercase) for _ in range(20))
    sg_name = 'inject_failure_sg_name' + ''.join(random.choice(string.ascii_uppercase) for _ in range(10))

    lb_item = get_load_balancer(describe_params)

    resp = ec2_client.create_security_group(
        Description=sg_description,
        GroupName=sg_name,
        VpcId=lb_item['VpcId']
    )
    security_groups = [resp['GroupId']]
    elb_client.set_security_groups(
        LoadBalancerArn=events['LoadBalancerArn'],
        SecurityGroups=security_groups
    )


def update_security_groups(events: dict, context: dict) -> None:
    required_params = [
        "LoadBalancerArn",
        "SecurityGroups"
    ]
    check_required_params(required_params, events)
    elb_client = boto3.client('elbv2')

    elb_client.set_security_groups(
        LoadBalancerArn=events['LoadBalancerArn'],
        SecurityGroups=events['SecurityGroups'],
    )


# 1.call [boto3.describe_load_balancers]
#   Params: LoadBalancerArns=[params.LoadBalancerArn]
#   take '.SecurityGroups[]' collection and return as SecurityGroups
def backup_security_groups(events: dict, context: dict) -> dict:
    required_params = [
        "LoadBalancerArn",
    ]
    check_required_params(required_params, events)
    logger.info(f"Load balancer arn {events['LoadBalancerArn']}")

    describe_params = {
        'LoadBalancerArns': [events['LoadBalancerArn']]
    }

    load_balancer = get_load_balancer(describe_params)

    result = []
    if load_balancer:
        result = load_balancer.get('SecurityGroups')
    logger.info(f"Security groups {result}")
    return result


def get_load_balancer(describe_params):
    elb_client = boto3.client('elbv2')
    paginator = elb_client.get_paginator('describe_load_balancers')
    pages = paginator.paginate(**describe_params)
    load_balancers = []
    for page in pages:
        load_balancers = page.get('LoadBalancers')
    return load_balancers[0] if len(load_balancers) > 0 else {}
