import boto3
from botocore.config import Config


def get_bigger_instance(events, context):
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ec2 = boto3.client('ec2', config=config)
    requested_instance_type = events["RequestInstanceType"] or ""
    if requested_instance_type:
        instance_types_response = ec2.describe_instance_type_offerings(
            Filters=[{'Name': 'instance-type', "Values": [requested_instance_type]}])
        if instance_types_response:
            return {**{'TargetInstanceType': requested_instance_type}}
        else:
            raise Exception("Requested instance type is not valid: " + requested_instance_type)

    current_instance_type = events["CurrentInstanceType"]
    instance_type_size = current_instance_type.rsplit(".", 1)
    instance_sizes = ["nano", "micro", "small", "medium", "large", "xlarge", "2xlarge", "3xlarge", "4xlarge",
                      "6xlarge", "8xlarge", "9xlarge", "10xlarge", "12xlarge", "16xlarge", "18xlarge", "24xlarge",
                      "32xlarge", "56xlarge", "112xlarge"]
    bigger_size_start_idx = instance_sizes.index(instance_type_size[1]) + 1
    possible_instance_types = []
    for i in range(len(instance_sizes) - bigger_size_start_idx):
        possible_instance_types.append(instance_type_size[0] + "." + instance_sizes[bigger_size_start_idx + i])
    instance_types_response = ec2.describe_instance_type_offerings(
        MaxResults=1000,
        Filters=[{'Name': 'instance-type', "Values": [instance_type_size[0] + ".*"]}])
    all_instance_types = [offering['InstanceType'] for offering in instance_types_response['InstanceTypeOfferings']]
    bigger_instances = [candidate for candidate in possible_instance_types if candidate in all_instance_types]
    if bigger_instances:
        return {**{'OriginalInstanceType': current_instance_type}, **{'TargetInstanceType': bigger_instances[0]}}
    else:
        raise Exception("Could not identify bigger instance type than current instance type: " + current_instance_type)
