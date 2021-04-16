import json
from datetime import datetime, timezone, timedelta
from io import BytesIO

import boto3
import urllib3
from dateutil.tz import tzutc

AUTOMATION_EXECUTION_ID = '123e4567-e89b-12d3-a456-426614174000'
STEP_NAME = 'StepName'
MISSING_STEP_NAME = 'MissingStepName'
INSTANCE_ID = 'i-12345'
SUCCESS_STATUS = 'Success'
RESPONSE_FIELD_1 = 'Status'
RESPONSE_FIELD_2 = 'InstanceId'
APPLICATION_SUBNET_ID = 'subnet-12345'
ROUTE_TABLE_ID = 'rtb-12345'
NAT_GATEWAY_ID = 'nat-12345'
IGW_ID = 'igw-12345'
INTERNET_DESTINATION = '0.0.0.0/0'
STEP_DURATION = 8
EXECUTION_START_TIME = datetime.now(timezone.utc) - timedelta(seconds=STEP_DURATION)
EXECUTION_END_TIME = datetime.now(timezone.utc)
DB_INSTANCE_ID = 'db'
TARGET_DB_INSTANCE_ID = 'db-new'
RECOVERY_POINT = 300
S3_SERVICE_NAME = 'S3'
DYNAMODB_SERVICE_NAME = 'DYNAMODB'
S3_USW2_IP_PREFIX = '1.1.1.1/32'
S3_USE1_IP_PREFIX = '2.2.2.2/32'
DYNAMODB_USW2_IP_PREFIX = '3.3.3.3/32'
DYNAMODB_USE1_IP_PREFIX = '4.4.4.4/32'
ADDITIONAL_IP_PREFIX_1 = '101.101.101.101/32'
ADDITIONAL_IP_PREFIX_2 = '102.102.102.102/32'
AMI_NAME = 'amzn-ami-vpc-nat-2018.03.0.20200206.0-x86_64-ebs'
AMI_ID = 'ami-0f482d2adde2d9206'
ASG_NAME = 'AsgName'
SECURITY_GROUP = 'sg-fewkhf'
SUBNET_GROUPS = 'subnet-12345,subnet-45678'
LAUNCH_CONFIGURATION_NAME = 'launchConfigurationName'
ACCOUNT_ID = '123456789123'
VPC_ID = 'vpc-12345'
PUBLIC_SUBNET_ID = 'subnet-public'
INSTANCE_REFRESH_ID = 'refresh-id'
AZ_USW2A = 'us-west-2a'
SSM_EXECUTION_PARAMETER_1 = 'AutomationAssumeRole'
SSM_EXECUTION_PARAMETER_1_VALUE = \
    [f'arn:aws:iam::{ACCOUNT_ID}:role/AutomationAssumeRoleTempl-DigitoSQSCapacityFailure-PK7O48UEHKGL']
SSM_EXECUTION_PARAMETER_2 = 'QueueUrl'
SSM_EXECUTION_PARAMETER_2_VALUE = \
    [f'https://sqs.ap-southeast-1.amazonaws.com/{ACCOUNT_ID}/SqsTemplate-0-SqsStandardQueue-1EO9FAEL376IM']
SSM_EXECUTION_PARAMETER_3 = 'SentMessageSizeAlarmName'
SSM_EXECUTION_PARAMETER_3_VALUE = \
    ['SqsSQSAlwaysOKAlarm']
ROLE = f'arn:aws:iam::{ACCOUNT_ID}:role/S3Template-0-RoleApproveCleanBucket-ON41KTFFSIPD'
SESSION = boto3.Session()
ACCESS_KEY_ID = 'asdadlkj'
SECRET_ACCESS_KEY = '12l3k1j3'
SESSION_TOKEN = '1lk23j1kj'
ASSUME_ROLE_RESPONSE = {
    'Credentials':
        {'AccessKeyId': ACCESS_KEY_ID,
         'SecretAccessKey': SECRET_ACCESS_KEY,
         'SessionToken': SESSION_TOKEN,
         'Expiration': datetime(2021, 4, 5, 17, 27, 27, tzinfo=tzutc())
         },
    'AssumedRoleUser':
        {
            'AssumedRoleId': '123AWLAST5TN232VAQSRH:72069623-cfd8-4ad3-9239-45ec9b58a123',
            'Arn': f'arn:aws:sts::{ACCOUNT_ID}:assumed-role/S3Template-0-RoleApproveCleanBucket-ON41KTFFSIPD/72069623'
                   f'-cfd8-4ad3-9239-45ec9b58a34c'
        },
    'ResponseMetadata': {
        'RequestId': 'e1ba494f-74cc-4515-b6e0-188969e08d8b', 'HTTPStatusCode': 200,
        'HTTPHeaders': {'x-amzn-requestid': 'e1ba494f-74cc-4515-b6e0-188969e08d8b',
                        'content-type': 'text/xml', 'content-length': '1175',
                        'date': 'Mon, 05 Apr 2021 16:27:27 GMT'},
        'RetryAttempts': 0}
}
BACKUP_PENDING_RECOVERY_ARN = f'arn:aws:backup:eu-south-1:{ACCOUNT_ID}:recovery-point:TestPending'
BACKUP_COMPLETED_RECOVERY_ARN = f'arn:aws:backup:eu-south-1:{ACCOUNT_ID}:recovery-point:TestCompleted'
BACKUP_VAULT_NAME = "test-backup-vault"


def get_sample_ssm_execution_response():
    step_execution_outputs = {}
    step_execution_outputs[RESPONSE_FIELD_1] = [SUCCESS_STATUS]
    step_execution_outputs[RESPONSE_FIELD_2] = [INSTANCE_ID]

    step_execution = {}
    step_execution['Outputs'] = step_execution_outputs
    step_execution['StepName'] = STEP_NAME
    step_execution['ExecutionStartTime'] = EXECUTION_START_TIME
    step_execution['ExecutionEndTime'] = EXECUTION_END_TIME

    automation_execution = {}
    automation_execution['StepExecutions'] = [step_execution]
    automation_execution['AutomationExecutionId'] = AUTOMATION_EXECUTION_ID
    automation_execution['Parameters'] = {
        SSM_EXECUTION_PARAMETER_1: SSM_EXECUTION_PARAMETER_1_VALUE,
        SSM_EXECUTION_PARAMETER_2: SSM_EXECUTION_PARAMETER_2_VALUE,
        SSM_EXECUTION_PARAMETER_3: SSM_EXECUTION_PARAMETER_3_VALUE
    }

    ssm_execution_response = {}
    ssm_execution_response['AutomationExecution'] = automation_execution

    return ssm_execution_response


def get_sample_route_table_response():
    route_1 = {}
    route_1['DestinationCidrBlock'] = '10.0.0.0/16'
    route_1['GatewayId'] = 'local'
    route_1['Origin'] = 'CreateRouteTable'
    route_1['State'] = 'active'

    route_natgw = {}
    route_natgw['DestinationCidrBlock'] = INTERNET_DESTINATION
    route_natgw['NatGatewayId'] = NAT_GATEWAY_ID
    route_natgw['Origin'] = 'CreateRoute'
    route_natgw['State'] = 'active'

    route_igw = {}
    route_igw['DestinationCidrBlock'] = INTERNET_DESTINATION
    route_igw['GatewayId'] = IGW_ID
    route_igw['Origin'] = 'CreateRoute'
    route_igw['State'] = 'active'

    route_table_1 = {}
    route_table_1['RouteTableId'] = ROUTE_TABLE_ID
    route_table_1['Routes'] = [route_1, route_natgw]

    route_table_2 = {}
    route_table_2['RouteTableId'] = ROUTE_TABLE_ID
    route_table_2['Routes'] = [route_1, route_igw]

    association = {}
    association['SubnetId'] = PUBLIC_SUBNET_ID
    route_table_2['Associations'] = [association]

    route_table_response = {}
    route_table_response['RouteTables'] = [route_table_1, route_table_2]
    route_table_response['ResponseMetadata'] = {'HTTPStatusCode': 200}

    return route_table_response


def get_sample_route_table_response_filtered_by_nat():
    route_1 = {}
    route_1['DestinationCidrBlock'] = '10.0.0.0/16'
    route_1['GatewayId'] = 'local'
    route_1['Origin'] = 'CreateRouteTable'
    route_1['State'] = 'active'

    route_natgw = {}
    route_natgw['DestinationCidrBlock'] = INTERNET_DESTINATION
    route_natgw['NatGatewayId'] = NAT_GATEWAY_ID
    route_natgw['Origin'] = 'CreateRoute'
    route_natgw['State'] = 'active'

    route_table_1 = {}
    route_table_1['RouteTableId'] = ROUTE_TABLE_ID
    route_table_1['Routes'] = [route_1, route_natgw]

    association = {}
    association['SubnetId'] = PUBLIC_SUBNET_ID

    route_table_response = {}
    route_table_response['RouteTables'] = [route_table_1]
    route_table_response['ResponseMetadata'] = {'HTTPStatusCode': 200}

    return route_table_response


def get_sample_delete_route_response():
    response = {}
    response['ResponseMetadata'] = {'HTTPStatusCode': 200}

    return response


def get_sample_describe_db_instances_response():
    db_instances_response = {}

    vpc_security_group = {}
    vpc_security_group['VpcSecurityGroupId'] = 'sg-12345'

    db_subnet_group = {}
    db_subnet_group['DBSubnetGroupName'] = 'db-subnet-group'

    db_instance = {}
    db_instance['LatestRestorableTime'] = datetime.now(timezone.utc) - timedelta(seconds=RECOVERY_POINT)
    db_instance['MultiAZ'] = True
    db_instance['PubliclyAccessible'] = True
    db_instance['CopyTagsToSnapshot'] = True
    db_instance['VpcSecurityGroups'] = [vpc_security_group]
    db_instance['DBSubnetGroup'] = db_subnet_group

    db_instances_response['DBInstances'] = [db_instance]

    return db_instances_response


def get_sample_aws_ip_ranges():
    aws_ip_ranges = {}

    s3_usw2_ip_prefix = {}
    s3_usw2_ip_prefix["ip_prefix"] = S3_USW2_IP_PREFIX
    s3_usw2_ip_prefix["region"] = "us-west-2"
    s3_usw2_ip_prefix["service"] = "S3"

    s3_use1_ip_prefix = {}
    s3_use1_ip_prefix["ip_prefix"] = S3_USE1_IP_PREFIX
    s3_use1_ip_prefix["region"] = "us-east-1"
    s3_use1_ip_prefix["service"] = "S3"

    dynamodb_usw2_ip_prefix = {}
    dynamodb_usw2_ip_prefix["ip_prefix"] = DYNAMODB_USW2_IP_PREFIX
    dynamodb_usw2_ip_prefix["region"] = "us-west-2"
    dynamodb_usw2_ip_prefix["service"] = "DYNAMODB"

    dynamodb_use1_ip_prefix = {}
    dynamodb_use1_ip_prefix["ip_prefix"] = DYNAMODB_USE1_IP_PREFIX
    dynamodb_use1_ip_prefix["region"] = "us-east-1"
    dynamodb_use1_ip_prefix["service"] = "DYNAMODB"

    aws_ip_ranges['prefixes'] = [s3_usw2_ip_prefix, s3_use1_ip_prefix, dynamodb_usw2_ip_prefix, dynamodb_use1_ip_prefix]

    headers = urllib3.response.HTTPHeaderDict(None)

    body = BytesIO(json.dumps(aws_ip_ranges).encode('utf-8'))

    urllib3_response = urllib3.response.HTTPResponse(body,
                                                     headers,
                                                     200,
                                                     preload_content=False)

    return urllib3_response


def get_sample_describe_images_response():
    describe_images_response = {}

    image = {}
    image['ImageId'] = AMI_ID
    describe_images_response['Images'] = [image]

    return describe_images_response


def get_sample_describe_auto_scaling_groups_response():
    describe_auto_scaling_groups_response = {}

    instance = {}
    instance['InstanceId'] = INSTANCE_ID
    instance['AvailabilityZone'] = AZ_USW2A

    auto_scaling_group = {}
    auto_scaling_group['Instances'] = [instance]
    auto_scaling_group['VPCZoneIdentifier'] = SUBNET_GROUPS
    auto_scaling_group['LaunchConfigurationName'] = LAUNCH_CONFIGURATION_NAME
    auto_scaling_group['SuspendedProcesses'] = []

    describe_auto_scaling_groups_response['AutoScalingGroups'] = [auto_scaling_group]

    return describe_auto_scaling_groups_response


def get_sample_describe_auto_scaling_groups_response_with_suspended_processes():
    describe_auto_scaling_groups_response = {}

    instance = {}
    instance['InstanceId'] = INSTANCE_ID

    auto_scaling_group = {}
    auto_scaling_group['Instances'] = [instance]
    auto_scaling_group['VPCZoneIdentifier'] = SUBNET_GROUPS
    auto_scaling_group['LaunchConfigurationName'] = LAUNCH_CONFIGURATION_NAME

    suspended_process = {}
    auto_scaling_group['SuspendedProcesses'] = [suspended_process]

    describe_auto_scaling_groups_response['AutoScalingGroups'] = [auto_scaling_group]

    return describe_auto_scaling_groups_response


def get_sample_describe_launch_configurations_response():
    launch_configurations_response = {}

    launch_configuration = {}
    launch_configuration['SecurityGroups'] = [SECURITY_GROUP]

    launch_configurations_response['LaunchConfigurations'] = [launch_configuration]
    return launch_configurations_response


def get_sample_describe_security_groups_response():
    describe_security_groups_response = {}

    user_id_group_pair = {}
    user_id_group_pair['UserId'] = ACCOUNT_ID
    user_id_group_pair['GroupId'] = SECURITY_GROUP

    ip_permission = {}
    ip_permission['UserIdGroupPairs'] = [user_id_group_pair]
    ip_permission['IpProtocol'] = "-1"

    security_group = {}
    security_group['IpPermissions'] = [ip_permission]

    describe_security_groups_response['SecurityGroups'] = [security_group]
    return describe_security_groups_response


def get_sample_describe_subnets_response():
    describe_subnets_response = {}

    subnet = {}
    subnet['VpcId'] = VPC_ID

    describe_subnets_response['Subnets'] = [subnet]
    return describe_subnets_response


def get_sample_describe_instance_refreshes_response(status):
    describe_instance_refreshes_response = {}

    instance_refresh = {}
    instance_refresh['Status'] = status
    instance_refresh['InstanceRefreshId'] = INSTANCE_REFRESH_ID

    describe_instance_refreshes_response['InstanceRefreshes'] = [instance_refresh]
    return describe_instance_refreshes_response


def get_instance_ids_by_count(count):
    ec2_instnce_ids = []
    for i in range(count):
        ec2_instnce_ids.append('test-ec2-instance-' + str(i))
    return ec2_instnce_ids


# EFS
def get_sample_describe_file_systems_response(fs_id):
    return {'FileSystems': [{
        "OwnerId": "435978235099",
        "CreationToken": "2021-04-13_14.17.16",
        "FileSystemId": fs_id,
        "FileSystemArn": "arn:aws:elasticfilesystem:eu-south-1:435978235099:file-system/" + fs_id,
        "CreationTime": "2021-04-13T17:27:17+03:00",
        "LifeCycleState": "available",
        "NumberOfMountTargets": 0,
        "SizeInBytes": {
            "Value": 24576,
            "Timestamp": "2021-04-14T15:18:54+03:00",
            "ValueInIA": 0,
            "ValueInStandard": 24576
        },
        "PerformanceMode": "generalPurpose",
        "Encrypted": False,
        "ThroughputMode": "bursting",
        "Tags": []
    }]}


# BACKUP

def get_sample_empty_recovery_points_list():
    return {
        "RecoveryPoints": []
    }


def get_sample_efs_recovery_points_by_backup_vault(backup_vault_name):
    return {
        "RecoveryPoints": [
            {
                "RecoveryPointArn": BACKUP_PENDING_RECOVERY_ARN,
                "backup_vault_name": backup_vault_name,
                "BackupVaultArn": f"arn:aws:backup:eu-south-1:{ACCOUNT_ID}:backup-vault:" + backup_vault_name,
                "ResourceArn": f"arn:aws:elasticfilesystem:eu-south-1:{ACCOUNT_ID}:file-system/fs-fb67d43e",
                "ResourceType": "EFS",
                "IamRoleArn": f"arn:aws:iam::{ACCOUNT_ID}:role/service-role/AWSBackupDefaultServiceRole",
                "Status": "PENDING",
                "CreationDate": "2021-04-16T10:55:24.093000+03:00",
                "CompletionDate": "2021-04-16T10:55:31.997000+03:00",
                "BackupSizeInBytes": 0,
                "EncryptionKeyArn": f"arn:aws:kms:eu-south-1:{ACCOUNT_ID}:key/TestKeyId",
                "IsEncrypted": True,
                "LastRestoreTime": "2021-04-16T11:05:59.952000+03:00"
            },
            {
                "RecoveryPointArn": BACKUP_COMPLETED_RECOVERY_ARN,
                "backup_vault_name": backup_vault_name,
                "BackupVaultArn": f"arn:aws:backup:eu-south-1:{ACCOUNT_ID}:backup-vault:" + backup_vault_name,
                "ResourceArn": f"arn:aws:elasticfilesystem:eu-south-1:{ACCOUNT_ID}:file-system/fs-fb67d43e",
                "ResourceType": "EFS",
                "IamRoleArn": f"arn:aws:iam::{ACCOUNT_ID}:role/service-role/AWSBackupDefaultServiceRole",
                "Status": "COMPLETED",
                "CreationDate": "2021-04-16T10:47:48.679000+03:00",
                "CompletionDate": "2021-04-16T10:47:55.851000+03:00",
                "BackupSizeInBytes": 0,
                "EncryptionKeyArn": f"arn:aws:kms:eu-south-1:{ACCOUNT_ID}:key/TestKeyId",
                "IsEncrypted": True
            }
        ]
    }


# IAM

def get_sample_role(role_name):
    return {
        "Role": {
            "Path": "/",
            "RoleName": role_name,
            "RoleId": "XXXXXXXXXXXXXXXXXXX",
            "Arn": f"arn:aws:iam::{ACCOUNT_ID}:role/" + role_name,
            "CreateDate": "2021-04-13T11:59:03+00:00",
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "ssm.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            },
            "Description": "",
            "MaxSessionDuration": 3600,
            "RoleLastUsed": {}
        }
    }
