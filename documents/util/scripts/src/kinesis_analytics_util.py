import boto3
import logging

from botocore.config import Config

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
                    'SecurityGroupIdUpdates': [security_group_id]}]})['ResponseMetadata']['HTTPStatusCode']
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
    security_group_id = security_group_ids['VpcConfigurationDescriptions'][0]['SecurityGroupIds'][0]
    return {"KinesisDataAnalyticsApplicationVPCSecurityGroupMappingOriginalValue": security_group_id}
