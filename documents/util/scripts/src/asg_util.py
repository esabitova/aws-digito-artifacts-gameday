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


def wait_for_in_service(events, context):
    client = boto3.client('autoscaling')
    while (True):
        res = client.describe_auto_scaling_groups(AutoScalingGroupNames=[events['AutoScalingGroupName']])
        instances = res['AutoScalingGroups'][0]['Instances']
        num_in_service = sum(instance['LifecycleState'] == 'InService' for instance in instances)
        if (num_in_service >= events['NewDesiredCapacity']):
            return True
        time.sleep(15)


def get_instance_data(events, context):
    asg = boto3.client('autoscaling')
    ec2 = boto3.client('ec2')
    describe_asg = asg.describe_auto_scaling_groups(AutoScalingGroupNames=[events['AutoScalingGroupName']])
    if 'MixedInstancesPolicy' in describe_asg['AutoScalingGroups'][0]:
        raise Exception('Cannot run this SOP on ASG that has a MixedInstancesPolicy')
    current_state = get_current_state(ec2, asg, describe_asg)
    bigger_instance_type = get_bigger_instance(current_state['OriginalInstanceType'], ec2)
    return {**current_state, **{'BiggerInstanceType': bigger_instance_type}}


def get_current_state(ec2, asg, describe_asg):
    if 'LaunchTemplate' in describe_asg['AutoScalingGroups'][0]:
        launch_template_version = describe_asg['AutoScalingGroups'][0]['LaunchTemplate']['Version']
        launch_template_name = describe_asg['AutoScalingGroups'][0]['LaunchTemplate']['LaunchTemplateName']
        describe_template = ec2.describe_launch_template_versions(
            LaunchTemplateName=launch_template_name, Versions=[launch_template_version])
        current_instance_type = describe_template['LaunchTemplateVersions'][0]['LaunchTemplateData']['InstanceType']
        return {'OriginalInstanceType': current_instance_type, 'LaunchTemplateVersion': launch_template_version,
                'LaunchTemplateName': launch_template_name, 'LaunchConfigurationName': ''}
    else:
        launch_config_name = describe_asg['AutoScalingGroups'][0]['LaunchConfigurationName']
        launch_config = asg.describe_launch_configurations(LaunchConfigurationNames=[launch_config_name])
        return {'OriginalInstanceType': launch_config['LaunchConfigurations'][0]['InstanceType'],
                'LaunchTemplateVersion': '',
                'LaunchTemplateName': '',
                'LaunchConfigurationName': launch_config_name}


def get_bigger_instance(current_instance_type, ec2):
    instance_type_size = current_instance_type.rsplit(".", 1)
    instance_sizes = ["nano", "micro", "small", "medium", "large", "xlarge", "2xlarge", "3xlarge", "4xlarge",
                      "6xlarge", "8xlarge", "9xlarge", "10xlarge", "12xlarge", "16xlarge", "18xlarge", "24xlarge",
                      "32xlarge", "56xlarge", "112xlarge"]
    bigger_size_start_idx = instance_sizes.index(instance_type_size[1]) + 1
    possible_instance_types = []
    for i in range(len(instance_sizes) - bigger_size_start_idx):
        possible_instance_types.append(instance_type_size[0] + "." + instance_sizes[bigger_size_start_idx + i])
    instance_types_response = ec2.describe_instance_type_offerings(
        Filters=[{'Name': 'instance-type', "Values": [instance_type_size[0] + ".*"]}])
    all_instance_types = [offering['InstanceType'] for offering in instance_types_response['InstanceTypeOfferings']]
    bigger_instances = [candidate for candidate in possible_instance_types if candidate in all_instance_types]
    if bigger_instances:
        return bigger_instances[0]
    else:
        raise Exception("Could not identify bigger instance type than current instance type: " + current_instance_type)


def update_asg(events, context):
    asg = boto3.client('autoscaling')
    ec2 = boto3.client('ec2')
    new_instance_type = events['BiggerInstanceType']
    if events['LaunchTemplateName']:
        create_template_response = ec2.create_launch_template_version(
            LaunchTemplateName=events['LaunchTemplateName'],
            SourceVersion=events['LaunchTemplateVersion'],
            LaunchTemplateData={'InstanceType': new_instance_type},
            VersionDescription="Uses instance type " + new_instance_type)
        new_version = str(create_template_response['LaunchTemplateVersion']['VersionNumber'])
        asg.update_auto_scaling_group(AutoScalingGroupName=events['AutoScalingGroupName'],
                                      LaunchTemplate={'LaunchTemplateName': events['LaunchTemplateName'],
                                                      'Version': new_version})
        return {'LaunchConfigOrTemplate': events['LaunchTemplateName'] + ':' + new_version}
    else:
        describe_asg = asg.describe_auto_scaling_groups(AutoScalingGroupNames=[events['AutoScalingGroupName']])
        describe_launch_config = asg.describe_launch_configurations(
            LaunchConfigurationNames=[describe_asg['AutoScalingGroups'][0]['LaunchConfigurationName']])
        launch_config = describe_launch_config['LaunchConfigurations'][0]
        launch_config.pop('LaunchConfigurationARN')
        launch_config.pop('CreatedTime')
        launch_config['InstanceType'] = new_instance_type
        launch_config['LaunchConfigurationName'] = launch_config['LaunchConfigurationName'] + \
            "-" + str(random.randint(1000, 9999))
        asg.create_launch_configuration(**{key: value for (key, value) in launch_config.items() if value != ''})
        asg.update_auto_scaling_group(AutoScalingGroupName=events['AutoScalingGroupName'],
                                      LaunchConfigurationName=launch_config['LaunchConfigurationName'])
        return {'LaunchConfigOrTemplate': launch_config['LaunchConfigurationName']}


def rollback_scaleup(events, context):
    asg = boto3.client('autoscaling')
    ec2 = boto3.client('ec2')
    if events['LaunchTemplateName']:
        name_version = events['LaunchConfigOrTemplate'].rsplit(":", 1)
        asg.update_auto_scaling_group(AutoScalingGroupName=events['AutoScalingGroupName'],
                                      LaunchTemplate={'LaunchTemplateName': events['LaunchTemplateName'],
                                                      'Version': events['LaunchTemplateVersion']})
        ec2.delete_launch_template_versions(LaunchTemplateName=name_version[0], Versions=[name_version[1]])
    else:
        asg.update_auto_scaling_group(AutoScalingGroupName=events['AutoScalingGroupName'],
                                      LaunchConfigurationName=events['LaunchConfigurationName'])
        asg.delete_launch_configuration(LaunchConfigurationName=events['LaunchConfigOrTemplate'])
