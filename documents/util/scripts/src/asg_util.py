import boto3
import time
import random
from math import ceil
from botocore.config import Config



def get_instance_ids_in_asg(events, context):
    if 'AutoScalingGroupName' not in events:
        raise KeyError('Requires AutoScalingGroupName in events')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    autoscaling = boto3.client('autoscaling', config=config)

    auto_scaling_groups = autoscaling.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            events['AutoScalingGroupName']
        ]
    )

    output = {}
    output['InstanceIds'] = []

    for instance in auto_scaling_groups['AutoScalingGroups'][0]['Instances']:
        output['InstanceIds'].append(instance['InstanceId'])
    return output


def get_healthy_instance_ids_in_asg(events, context):
    if 'AutoScalingGroupName' not in events:
        raise KeyError('Requires AutoScalingGroupName in events')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    autoscaling = boto3.client('autoscaling', config=config)

    auto_scaling_groups = autoscaling.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            events['AutoScalingGroupName']
        ]
    )

    # Take all healthy ASG EC2 instances
    asg_healthy_instances = []
    for instance in auto_scaling_groups['AutoScalingGroups'][0]['Instances']:
        if instance['HealthStatus'] == 'Healthy' and instance['LifecycleState'] == 'InService':
            asg_healthy_instances.append(instance['InstanceId'])

    output = {}
    output['InstanceIds'] = asg_healthy_instances
    return output


def filter_healthy_instance_ids_in_asg(events, context):
    if 'AutoScalingGroupName' not in events or 'InstanceIds' not in events:
        raise KeyError('Requires AutoScalingGroupName, InsatnceIds in events')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    autoscaling = boto3.client('autoscaling', config=config)

    auto_scaling_groups = autoscaling.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            events['AutoScalingGroupName']
        ]
    )

    # Take all healthy ASG EC2 instances
    asg_healthy_instances = []
    for instance in auto_scaling_groups['AutoScalingGroups'][0]['Instances']:
        if instance['HealthStatus'] == 'Healthy' and instance['LifecycleState'] == 'InService':
            asg_healthy_instances.append(instance['InstanceId'])

    output = {}
    output['InstanceIds'] = []
    given_instance_ids = events['InstanceIds']
    # Take only healthy given EC2 instances
    for instance_id in given_instance_ids:
        if instance_id in asg_healthy_instances:
            output['InstanceIds'].append(instance_id)

    return output


def get_instance_ids_in_asg_random_az(events, context):
    if 'AutoScalingGroupName' not in events:
        raise KeyError('Requires AutoScalingGroupName in events')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    autoscaling = boto3.client('autoscaling', config=config)

    auto_scaling_groups = autoscaling.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            events['AutoScalingGroupName']
        ]
    )

    instances_by_az = {}
    for instance in auto_scaling_groups['AutoScalingGroups'][0]['Instances']:
        instances_by_az.setdefault(instance['AvailabilityZone'], []).append(instance['InstanceId'])

    output = {}
    output['InstanceIds'] = random.choice(list(instances_by_az.values()))
    return output


def get_networking_configuration_from_asg(events, context):
    if 'AutoScalingGroupName' not in events:
        raise KeyError('Requires AutoScalingGroupName in events')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    autoscaling = boto3.client('autoscaling', config=config)

    auto_scaling_groups = autoscaling.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            events['AutoScalingGroupName']
        ]
    )

    subnets = auto_scaling_groups['AutoScalingGroups'][0]['VPCZoneIdentifier']

    launch_configurations = autoscaling.describe_launch_configurations(
        LaunchConfigurationNames=[
            auto_scaling_groups['AutoScalingGroups'][0]['LaunchConfigurationName']
        ]
    )

    security_group = launch_configurations['LaunchConfigurations'][0]['SecurityGroups'][0]

    output = {}
    output['SubnetIds'] = subnets.split(',')
    output['SecurityGroup'] = security_group
    return output


def suspend_launch(events, context):
    if 'AutoScalingGroupName' not in events:
        raise KeyError('Requires AutoScalingGroupName in events')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    autoscaling = boto3.client('autoscaling', config=config)
    autoscaling.suspend_processes(
        AutoScalingGroupName=events['AutoScalingGroupName'],
        ScalingProcesses=[
            'Launch'
        ]
    )


def start_instance_refresh(events, context):
    if 'AutoScalingGroupName' not in events or 'PercentageOfInstances' not in events:
        raise KeyError('Requires AutoScalingGroupName, PercentageOfInstances in events')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    autoscaling = boto3.client('autoscaling', config=config)
    refresh_response = autoscaling.start_instance_refresh(
        AutoScalingGroupName=events['AutoScalingGroupName'],
        Strategy='Rolling',
        Preferences={'MinHealthyPercentage': (100 - events['PercentageOfInstances'])}
    )

    output = {}
    output['InstanceRefreshId'] = refresh_response['InstanceRefreshId']
    return output


def cancel_instance_refresh(events, context):
    if 'AutoScalingGroupName' not in events:
        raise KeyError('Requires AutoScalingGroupName in events')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    autoscaling = boto3.client('autoscaling', config=config)
    autoscaling.cancel_instance_refresh(
        AutoScalingGroupName=events['AutoScalingGroupName']
    )


def wait_for_refresh_to_finish(events, context):
    if 'AutoScalingGroupName' not in events or 'InstanceRefreshId' not in events:
        raise KeyError('Requires AutoScalingGroupName, InstanceRefreshId in events')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    autoscaling = boto3.client('autoscaling', config=config)
    while True:
        instance_refresh_status = autoscaling.describe_instance_refreshes(
            AutoScalingGroupName=events['AutoScalingGroupName'],
            InstanceRefreshIds=[
                events['InstanceRefreshId']
            ]
        )
        if instance_refresh_status['InstanceRefreshes'][0]['Status'] not in ['Pending', 'InProgress']:
            if instance_refresh_status['InstanceRefreshes'][0]['Status'] not in ['Successful']:
                raise Exception('Instance refresh failed, refresh status %, refresh id %',
                                instance_refresh_status['InstanceRefreshes'][0]['Status'],
                                instance_refresh_status['InstanceRefreshes'][0]['InstanceRefreshId'])
            break
        # Sleep for 30 seconds
        time.sleep(30)


def assert_no_refresh_in_progress(events, context):
    if 'AutoScalingGroupName' not in events:
        raise KeyError('Requires AutoScalingGroupName in events')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    autoscaling = boto3.client('autoscaling', config=config)
    instance_refreshes = autoscaling.describe_instance_refreshes(
        AutoScalingGroupName=events['AutoScalingGroupName']
    )

    for instance_refresh in instance_refreshes['InstanceRefreshes']:
        if instance_refresh['Status'] in ['Pending', 'InProgress', 'Cancelling']:
            raise Exception('Instance refresh in progress, refresh status %, refresh id %',
                            instance_refreshes['InstanceRefreshes'][0]['Status'],
                            instance_refreshes['InstanceRefreshes'][0]['InstanceRefreshId'])


def assert_no_suspended_process(events, context):
    if 'AutoScalingGroupName' not in events:
        raise KeyError('Requires AutoScalingGroupName in events')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    autoscaling = boto3.client('autoscaling', config=config)
    auto_scaling_groups = autoscaling.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            events['AutoScalingGroupName']
        ]
    )

    if len(auto_scaling_groups['AutoScalingGroups'][0]['SuspendedProcesses']) > 0:
        raise Exception('ASG % has suspended processes', events['AutoScalingGroupName'])


def get_instance_ids_by_percentage(events, context):
    if 'InstanceIds' not in events or 'Percentage' not in events:
        raise KeyError('Requires InstanceIds and Percentage in events')
    instanceIds = events['InstanceIds']
    percentage = events['Percentage']
    instance_count = len(instanceIds)
    output = {}
    output['InstanceIds'] = []
    if instance_count < 1:
        raise Exception('No given EC2 instances')
    if percentage < 1:
        raise Exception('Given percentage should not be lower than 1%')
    instance_count = ceil(instance_count / 100 * percentage)
    for i in range(instance_count):
        output['InstanceIds'].append(instanceIds[i])
    return output
