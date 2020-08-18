import boto3

def get_instance_ids_in_asg(events, context):
    if 'AutoScalingGroupName' not in events:
        raise KeyError('Requires AutoScalingGroupName in events')

    autoscaling = boto3.client('autoscaling')

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

def get_networking_configuration_from_asg(events, context):
    if 'AutoScalingGroupName' not in events:
        raise KeyError('Requires AutoScalingGroupName in events')

    autoscaling = boto3.client('autoscaling')

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