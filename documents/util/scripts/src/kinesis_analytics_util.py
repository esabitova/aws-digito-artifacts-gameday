import boto3
import logging
import time
from datetime import datetime

from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SNAPSHOTS_LIST_QUOTA = 49


def verify_snapshot_exists(events, context):
    """
    verify snapshot exists.
    If events['SnapshotName'] is 'LATEST' - take last on time creation snapshot
    If snapshot does not exist, raise Error
    """
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    kinesis_analytics_client = boto3.client('kinesisanalyticsv2', config=config)
    ApplicationName = events['ApplicationName']
    snapshot_name = events['SnapshotName']
    if snapshot_name == 'LATEST':
        snapshot_name = kinesis_analytics_client.list_application_snapshots(
            ApplicationName=ApplicationName,
            Limit=SNAPSHOTS_LIST_QUOTA)['SnapshotSummaries'][-1]['SnapshotName']
    snapshot_status = kinesis_analytics_client.describe_application_snapshot(
        ApplicationName=ApplicationName,
        SnapshotName=snapshot_name,
    )['SnapshotDetails']['SnapshotStatus']
    return snapshot_status


def obtain_s3_object_version_id(events, context):
    """
    return Kinesis Data Analytics application file s3 bucket version id
    """
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    kinesis_analytics_client = boto3.client('kinesisanalyticsv2', config=config)
    s3_client = boto3.client('s3', config=config)
    ApplicationName = events['ApplicationName']
    resp_new_app = kinesis_analytics_client.describe_application(
        ApplicationName=ApplicationName,
        IncludeAdditionalDetails=True)
    s3_app_bucket_arn = resp_new_app['ApplicationDetail']['ApplicationConfigurationDescription']
    s3_app_bucket_arn = s3_app_bucket_arn['ApplicationCodeConfigurationDescription']['CodeContentDescription']
    s3_app_bucket_arn = s3_app_bucket_arn['S3ApplicationCodeLocationDescription']['BucketARN']
    s3_app_bucket_name = s3_app_bucket_arn.split(':::')[1]
    s3_file_key = resp_new_app['ApplicationDetail']['ApplicationConfigurationDescription']
    s3_file_key = s3_file_key['ApplicationCodeConfigurationDescription']['CodeContentDescription']
    s3_file_key = s3_file_key['S3ApplicationCodeLocationDescription']['FileKey']
    s3_flink_app_bucket_version_id = s3_client.get_object(
        Bucket=s3_app_bucket_name,
        Key=s3_file_key)['VersionId']
    return {'VersionId': s3_flink_app_bucket_version_id}


def obtain_conditional_token(events, context, kinesis_analytics_client=None):
    """
    return Kinesis Data Analytics application conditional token
    """
    if not kinesis_analytics_client:
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        kinesis_analytics_client = boto3.client('kinesisanalyticsv2', config=config)
    app_name = events['ApplicationName']
    ConditionalToken = kinesis_analytics_client.describe_application(
        ApplicationName=app_name,
        IncludeAdditionalDetails=True)['ApplicationDetail']['ConditionalToken']
    return ConditionalToken


def restore_from_latest_snapshot(events, context):
    """
    updates Kinesis Data Analytics application - restore from latest snapshot
    """
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    kinesis_analytics_client = boto3.client('kinesisanalyticsv2', config=config)
    app_name = events['ApplicationName']
    conditional_token = events['ConditionalToken']
    app_s3file_obj_version = events['ObjectVersionId']
    recover_status = kinesis_analytics_client.update_application(
        ApplicationName=app_name,
        ConditionalToken=conditional_token,
        ApplicationConfigurationUpdate={
            'ApplicationCodeConfigurationUpdate':
            {'CodeContentUpdate':
             {'S3ContentLocationUpdate':
              {'ObjectVersionUpdate': app_s3file_obj_version}}}},
        RunConfigurationUpdate={
            'FlinkRunConfiguration':
            {'AllowNonRestoredState': True},
            'ApplicationRestoreConfiguration':
            {'ApplicationRestoreType': 'RESTORE_FROM_LATEST_SNAPSHOT'}})
    recover_status = recover_status['ResponseMetadata']['HTTPStatusCode']
    return recover_status


def restore_from_custom_snapshot(events, context):
    """
    updates Kinesis Data Analytics application - restore from provided custom snapshot
    """
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    kinesis_analytics_client = boto3.client('kinesisanalyticsv2', config=config)
    app_name = events['ApplicationName']
    snapshot_name = events['SnapshotName']
    conditional_token = events['ConditionalToken']
    app_s3file_obj_version = events['ObjectVersionId']
    recover_status = kinesis_analytics_client.update_application(
        ApplicationName=app_name,
        ConditionalToken=conditional_token,
        ApplicationConfigurationUpdate={
            'ApplicationCodeConfigurationUpdate':
            {'CodeContentUpdate':
             {'S3ContentLocationUpdate':
              {'ObjectVersionUpdate': app_s3file_obj_version}}}},
        RunConfigurationUpdate={
            'FlinkRunConfiguration':
            {'AllowNonRestoredState': True},
            'ApplicationRestoreConfiguration':
            {'ApplicationRestoreType': 'RESTORE_FROM_CUSTOM_SNAPSHOT',
             'SnapshotName': snapshot_name}})['ResponseMetadata']['HTTPStatusCode']
    return recover_status


def update_kda_vpc_security_group(events, context):
    """
    updates Kinesis Data Analytics application - cahanges VPC security group
    """
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    kinesis_analytics_client = boto3.client('kinesisanalyticsv2', config=config)
    app_name = events['ApplicationName']
    security_group_id = events['KDAVPCSecurityGroupMappingValue']
    get_data_about_app = kinesis_analytics_client.describe_application(
        ApplicationName=app_name, IncludeAdditionalDetails=True)['ApplicationDetail']
    conditional_token = get_data_about_app['ConditionalToken']
    get_vpc_data_about_app = get_data_about_app['ApplicationConfigurationDescription']
    get_vpc_data_about_app = get_vpc_data_about_app['VpcConfigurationDescriptions'][0]
    subnet_id = get_vpc_data_about_app['SubnetIds']
    vpc_configuration_id = get_vpc_data_about_app['VpcConfigurationId']
    update_status = kinesis_analytics_client.update_application(
        ApplicationName=app_name,
        ConditionalToken=conditional_token,
        ApplicationConfigurationUpdate={
            'VpcConfigurationUpdates': [
                {'VpcConfigurationId': vpc_configuration_id,
                    'SubnetIdUpdates': subnet_id,
                    'SecurityGroupIdUpdates': security_group_id}]})['ResponseMetadata']['HTTPStatusCode']
    return update_status


def get_kda_vpc_security_group(events, context, kinesis_analytics_client=None):
    """
    exctracts Kinesis Data Analytics application VPC security group
    """
    if not kinesis_analytics_client:
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        kinesis_analytics_client = boto3.client('kinesisanalyticsv2', config=config)
    app_name = events['ApplicationName']
    security_group_ids = kinesis_analytics_client.describe_application(
        ApplicationName=app_name, IncludeAdditionalDetails=True)['ApplicationDetail']
    security_group_ids = security_group_ids['ApplicationConfigurationDescription']
    security_group_ids = security_group_ids['VpcConfigurationDescriptions'][0]['SecurityGroupIds']
    return {"KinesisDataAnalyticsApplicationVPCSecurityGroupMappingOriginalValue": security_group_ids}


def confect_fake_vpc_security_group(events, context):
    """
    Confect fake VPC security group, to attach to Kinesis Data Analytics application
    on gameday test
    """
    required_params = [
        'ApplicationName',
        'ExecutionId',
        'Tag'
    ]
    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    kinesis_analytics_client = boto3.client('kinesisanalyticsv2', config=config)
    ec2_client = boto3.client('ec2', config=config)
    app_name = events['ApplicationName']
    get_data_about_app = kinesis_analytics_client.describe_application(
        ApplicationName=app_name, IncludeAdditionalDetails=True)['ApplicationDetail']
    get_vpc_data_about_app = get_data_about_app['ApplicationConfigurationDescription']
    get_vpc_data_about_app = get_vpc_data_about_app['VpcConfigurationDescriptions'][0]
    vpc_id = get_vpc_data_about_app['VpcId']
    group_id = ec2_client.create_security_group(
        Description=f'Empty SG for executionID {events["ExecutionId"]}',
        GroupName=f'EmptySG-{events["ExecutionId"]}',
        VpcId=vpc_id,
        TagSpecifications=[
            {
                'ResourceType': 'security-group',
                'Tags': [
                    {
                        'Key': 'Digito',
                        'Value': events['Tag']
                    },
                ]
            }
        ]
    )['GroupId']
    result = ec2_client.revoke_security_group_egress(
        GroupId=group_id,
        IpPermissions=[
            {
                "IpProtocol": "-1",
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0"
                    }
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "UserIdGroupPairs": []
            }
        ]
    )
    if not result['Return']:
        remove_fake_vpc_security_group({'EmptySecurityGroupId': group_id}, context)
        raise ClientError(
            error_response={
                "Error":
                {
                    "Code": "CouldNotRevoke",
                    "Message": f"Could not revoke egress from sg: {group_id}"
                }
            },
            operation_name='RevokeSecurityGroupEgress'
        )
    return {'KinesisDataAnalyticsApplicationVPCFakeSecurityGroupIdsList': [group_id]}


def remove_fake_vpc_security_group(events, context):
    """
    Remove fake VPC security group, former confected on a previous test step
    """
    required_params = [
        'EmptySecurityGroupId'
    ]
    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')
    time_to_wait = 1800
    ec2_client = boto3.client('ec2')
    if 'Timeout' in events:
        time_to_wait = events['Timeout']
    timeout_timestamp = time.time() + int(time_to_wait)
    while time.time() < timeout_timestamp:
        try:
            logger.info(f'Deleting empty security group: {events["EmptySecurityGroupId"]}')
            group_list = ec2_client.describe_security_groups(
                Filters=[
                    {
                        'Name': 'group-id',
                        'Values': [
                            events["EmptySecurityGroupId"][0],
                        ]
                    },
                ]
            )
            if not group_list['SecurityGroups']:
                break
            group_id = group_list['SecurityGroups'][0]['GroupId']
            logger.info(f'Deleting empty security group: {group_id}')
            response = ec2_client.delete_security_group(
                GroupId=group_id
            )
            if response['ResponseMetadata']['HTTPStatusCode'] < 400:
                break
        except ClientError as error:
            if error.response['Error']['Code'] == 'InvalidGroup.NotFound':
                logger.info(f"Empty security group doesn't exist: {events['EmptySecurityGroupId']}")
                break
            elif error.response['Error']['Code'] == 'DependencyViolation' \
                    or error.response['Error']['Code'] == 'RequestLimitExceeded':
                time.sleep(5)
                continue
            else:
                raise error
    if datetime.timestamp(datetime.now()) > timeout_timestamp:
        raise TimeoutError(f'Security group {events["EmptySecurityGroupId"]} couldn\'t '
                           f'be deleted in {time_to_wait} seconds')
