import logging
from datetime import datetime
import time
from typing import Any, Callable, List, Union

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ENABLED_INSIGHTS_STATUSES = ['ENABLING', 'ENABLED']
GLOBAL_TABLE_ACTIVE_STATUSES = ['ACTIVE']


def _parse_date_time(date_time_str: str, format: str) -> Union[datetime, None]:
    if date_time_str.strip():
        try:
            return datetime.strptime(date_time_str, format)
        except ValueError as ve:
            logger.error(ve)
    return None


def _execute_boto3_dynamodb(delegate: Callable[[Any], dict]) -> dict:
    dynamo_db_client = boto3.client('dynamodb')
    description = delegate(dynamo_db_client)
    if not description['ResponseMetadata']['HTTPStatusCode'] == 200:
        logging.error(description)
        raise ValueError('Failed to execute request')
    return description


def _describe_kinesis_destinations(table_name: str) -> dict:
    return _execute_boto3_dynamodb(
        delegate=lambda x: x.describe_kinesis_streaming_destination(TableName=table_name))


def _list_tags(resource_arn: str) -> dict:
    return _execute_boto3_dynamodb(
        delegate=lambda x: x.list_tags_of_resource(ResourceArn=resource_arn))


def _update_tags(resource_arn: str, tags: List[dict]) -> dict:
    return _execute_boto3_dynamodb(
        delegate=lambda x: x.tag_resource(ResourceArn=resource_arn, Tags=tags))


def _enable_kinesis_destinations(table_name: str, kds_arn: str) -> dict:
    return _execute_boto3_dynamodb(
        delegate=lambda x: x.enable_kinesis_streaming_destination(TableName=table_name,
                                                                  StreamArn=kds_arn))


def _describe_time_to_live(table_name: str) -> dict:
    return _execute_boto3_dynamodb(
        delegate=lambda x: x.describe_time_to_live(TableName=table_name))


def _update_time_to_live(table_name: str, is_enabled: bool, attribute_name: str) -> dict:
    return _execute_boto3_dynamodb(
        delegate=lambda x: x.update_time_to_live(TableName=table_name,
                                                 TimeToLiveSpecification={
                                                     "Enabled": is_enabled,
                                                     "AttributeName": attribute_name
                                                 }))


def _update_table(table_name: str, **kwargs) -> dict:
    return _execute_boto3_dynamodb(
        delegate=lambda x: x.update_table(TableName=table_name, **kwargs))


def _describe_table(table_name: str) -> dict:
    return _execute_boto3_dynamodb(
        delegate=lambda x: x.describe_table(TableName=table_name))


def _describe_contributor_insights(table_name: str, index_name: str = None) -> dict:
    if index_name:
        return _execute_boto3_dynamodb(
            delegate=lambda x: x.describe_contributor_insights(TableName=table_name, IndexName=index_name))

    return _execute_boto3_dynamodb(
        delegate=lambda x: x.describe_contributor_insights(TableName=table_name))


def _update_contributor_insights(table_name: str, status: str, index_name: str = None) -> dict:
    if index_name:
        return _execute_boto3_dynamodb(
            delegate=lambda x: x.update_contributor_insights(TableName=table_name,
                                                             IndexName=index_name,
                                                             ContributorInsightsAction=status))

    return _execute_boto3_dynamodb(
        delegate=lambda x: x.update_contributor_insights(TableName=table_name,
                                                         ContributorInsightsAction=status))


def _get_global_table_all_regions(table_name: str) -> List[dict]:
    description = _describe_table(table_name=table_name)
    replicas = description['Table'].get('Replicas', [])
    return replicas


def get_global_table_active_regions(events: dict, context: dict) -> dict:
    """
    Returns list of replicas of the given table
    :param events: The dictionary that supposed to have the following keys:
    * `TableName` - The table name
    * `GlobalTableRegions` - The list of regions where replicas should be established
    :return: The dictionary that contains list of regions where replicas set up where status is Active
    """
    if 'TableName' not in events:
        raise KeyError('Requires TableName')

    table_name: str = events['TableName']
    replicas = _get_global_table_all_regions(table_name=table_name)

    return{
        'GlobalTableRegions': [r['RegionName']
                               for r in replicas
                               if r['ReplicaStatus'] in GLOBAL_TABLE_ACTIVE_STATUSES]
    }


def set_up_replication(events: dict, context: dict) -> dict:
    """
    Sets up replicas in the given regions
    :param events: The dictionary that supposed to have the following keys:
    * `TableName` - The table name
    * `GlobalTableRegions` - The list of regions where replicas should be established
    :return: The dictionary that contains list of regions where replicas set up
    """
    if 'TableName' not in events:
        raise KeyError('Requires TableName')
    if 'GlobalTableRegions' not in events:
        raise KeyError('Requires GlobalTableRegions')

    table_name: str = events['TableName']
    global_table_regions: str = events.get('GlobalTableRegions', [])
    if global_table_regions:
        _update_table(table_name=table_name, ReplicaUpdates=[
            {'Create': {'RegionName': region}} for region in global_table_regions])

    return{
        'GlobalTableRegionsAdded': global_table_regions
    }


def wait_replication_status_in_all_regions(events: dict, context: dict) -> dict:
    """
    Updates contributor insights settings for the given table and the list of indexes
    :param events: The dictionary that supposed to have the following keys:
    * `TableName` - The table name
    * `ReplicasRegionsToWait` - The list of regions where replicas should be active
    * `WaitTimeoutSeconds` - The number of seconds to wait Active status
    :return: The dictionary that contains list of regions where status is Active
    """
    if 'TableName' not in events:
        raise KeyError('Requires TableName')
    if 'ReplicasRegionsToWait' not in events:
        raise KeyError('Requires ReplicasRegionsToWait')
    if 'WaitTimeoutSeconds' not in events:
        raise KeyError('Requires WaitTimeoutSeconds')

    table_name: str = events['TableName']
    wait_timeout_seconds: int = int(events['WaitTimeoutSeconds'])
    replicas_regions_to_wait: str = events['ReplicasRegionsToWait']
    if not replicas_regions_to_wait:
        return{
            "GlobalTableRegionsActive": []
        }

    start = time.time()
    elapsed = 0
    while elapsed < wait_timeout_seconds:
        replicas = _get_global_table_all_regions(table_name=table_name)
        all_active = all([r['ReplicaStatus'] in GLOBAL_TABLE_ACTIVE_STATUSES
                          for r in replicas
                          if r['RegionName'] in replicas_regions_to_wait])
        if all_active:
            return{
                'GlobalTableRegionsActive': replicas_regions_to_wait
            }

        end = time.time()
        logging.debug(f'time elapsed {elapsed} seconds. The last result:{replicas}')
        time.sleep(20)
        elapsed = end - start

    raise TimeoutError(f'After {elapsed} not all replicas are Active. '
                       'Regions to waits: {GLOBAL_TABLE_ACTIVE_STATUSES}')


def copy_contributor_insights_settings(events: dict, context: dict) -> dict:
    """
    Returns contributor insights settings for the given table and the list of indexes
    :param events: The dictionary that supposed to have the following keys:
    * `SourceTableName` - The source table name
    * `TargetTableName` - The target table name
    :return: The dictionary that contains copied contributor insights statuses for the table and also
    a list of `IndexName`-`Status` map
    """
    if 'SourceTableName' not in events:
        raise KeyError('Requires SourceTableName')
    if 'TargetTableName' not in events:
        raise KeyError('Requires TargetTableName')

    source_table_name: str = events['SourceTableName']
    target_table_name: str = events['TargetTableName']

    # coping settings for table
    table_result = _describe_contributor_insights(table_name=source_table_name)
    table_status = table_result['ContributorInsightsStatus']
    if table_status in ENABLED_INSIGHTS_STATUSES:
        _update_contributor_insights(table_name=target_table_name,
                                     status='ENABLE')
    # coping settings for indexes
    indexes = _get_global_secondary_indexes(table_name=source_table_name)
    indexes_results = [_describe_contributor_insights(
        table_name=source_table_name, index_name=index_name) for index_name in indexes]

    index_statuses = [{
        'IndexName': r['IndexName'],
        'ContributorInsightsStatus': r['ContributorInsightsStatus']
    } for r in indexes_results]
    for index_status in index_statuses:
        if index_status['ContributorInsightsStatus'] in ENABLED_INSIGHTS_STATUSES:
            _update_contributor_insights(table_name=target_table_name,
                                         status='ENABLE',
                                         index_name=index_status['IndexName'])

    return {
        "CopiedTableContributorInsightsStatus": table_result['ContributorInsightsStatus'],
        "CopiedIndexesContributorInsightsStatus": index_statuses
    }


def _get_global_secondary_indexes(table_name: str) -> List[str]:
    """
    Returns the list of global indexes
    :param table_name: The table name
    :return: The list of global secondary index names
    """
    result = _describe_table(table_name=table_name)
    logger.debug(result)

    return [gsi['IndexName'] for gsi in result['Table'].get('GlobalSecondaryIndexes', [])]


def copy_resource_tags(events: dict, context: dict) -> dict:
    """
    Copied tags of a Dynamo DB table to a target one
    :param events: The dictionary that supposed to have the following keys:
    * `SourceTableName` - The source table name
    * `TargetTableName` - The target table name
    * `Region` - The region to concatenate ARN
    * `Account` - The account to concatenate ARN
    :return: The MapList of copied resource Tags
    """
    if 'SourceTableName' not in events:
        raise KeyError('Requires SourceTableName')
    if 'TargetTableName' not in events:
        raise KeyError('Requires TargetTableName')
    if 'Region' not in events:
        raise KeyError('Requires Region')
    if 'Account' not in events:
        raise KeyError('Requires Account')

    source_table_name = events['SourceTableName']
    region = events['Region']
    account = events['Account']
    resource_arn = f'arn:aws:dynamodb:{region}:{account}:table/{source_table_name}'
    tags = _list_tags(resource_arn=resource_arn)['Tags']
    if tags:
        target_table_name = events['TargetTableName']
        resource_arn = f'arn:aws:dynamodb:{region}:{account}:table/{target_table_name}'
        _update_tags(resource_arn=resource_arn, tags=tags)

    return {
        "Tags": tags
    }


def copy_time_to_live(events: dict, context: dict) -> dict:
    """
    Updates TTL for the given table. Enables TTL is the provided `Status` equals to `ENABLED`
    :param events: The dictionary that supposed to have the following keys:
    * `SourceTableName` - The source table name
    * `TargetTableName` - The targe table name
    :return: The dictionary that contains repose of TTL update AWS API
    """
    if 'SourceTableName' not in events:
        raise KeyError('Requires SourceTableName')
    if 'TargetTableName' not in events:
        raise KeyError('Requires TargetTableName')

    source_table_name = events['SourceTableName']
    target_table_name = events['TargetTableName']
    ttl_description = _describe_time_to_live(table_name=source_table_name)
    is_enabled = ttl_description\
        .get('TimeToLiveDescription', {})\
        .get('TimeToLiveStatus', '') == 'ENABLED'
    attribute_name = ttl_description\
        .get('TimeToLiveDescription', {})\
        .get('AttributeName', '')

    logging.debug(f'table:{target_table_name};TTL is enabled: {is_enabled};')
    if is_enabled:
        _update_time_to_live(table_name=target_table_name,
                             is_enabled=is_enabled,
                             attribute_name=attribute_name)

    return {
        'TTLCopied': is_enabled,
        'TTLAttribute': attribute_name
    }


def copy_active_kinesis_destinations(events: dict, context: dict) -> dict:
    """
    Returns information about Kinesis Data Stream destinations of the given Dynamo DB table
    :param events: The dictionary that supposed to have the following keys:
    * `SourceTableName` - The source table name
    * `TargetTableName` - The target table name
    :return: The list of Kinesis Data Stream ARNs
    """
    if 'SourceTableName' not in events:
        raise KeyError('Requires SourceTableName')
    if 'TargetTableName' not in events:
        raise KeyError('Requires TargetTableName')

    ACTIVE_STATUSES = ['ACTIVE', 'ENABLING']
    source_table_name = events['SourceTableName']
    target_table_name = events['TargetTableName']
    kinesis_destinations = _describe_kinesis_destinations(table_name=source_table_name)
    destinations = [d['StreamArn'] for d in kinesis_destinations['KinesisDataStreamDestinations']
                    if d['DestinationStatus'] in ACTIVE_STATUSES]

    for d in destinations:
        _enable_kinesis_destinations(table_name=target_table_name, kds_arn=d)

    return destinations


def copy_table_stream_settings(events: dict, context: dict):
    """
    if `StreamEnabled` is True, enabled streaming for the given table according to the given `StreamViewType`
    :param events: The dictionary that supposed to have the following keys:
    * `SourceTableName` - The source table name
    * `TargetTableName` - The target table name
    :return: The dictionary that contains 'StreamViewType' and `StreamEnabled` values of the target table
    """
    if 'SourceTableName' not in events:
        raise KeyError('Requires SourceTableName')
    if 'TargetTableName' not in events:
        raise KeyError('Requires TargetTableName')

    source_table_name = events['SourceTableName']
    description = _describe_table(table_name=source_table_name)['Table']
    stream_enabled = description\
        .get('StreamSpecification', {})\
        .get('StreamEnabled', False)
    if stream_enabled:
        target_table_name = events['TargetTableName']
        stream_view_type = description['StreamSpecification']['StreamViewType']
        settings = {
            "StreamSpecification": {
                "StreamEnabled": stream_enabled,
                "StreamViewType": stream_view_type
            }
        }
        result = _update_table(table_name=target_table_name, **settings)
        specification = result.get('StreamSpecification', {})
        return specification


def parse_recovery_date_time(events: dict, context: dict) -> dict:
    """
    Tries to parse the given `RecoveryPointDateTime` and returns it back if success
    :return: The dictionary that indicates if latest availabe recovery point should be used
    """
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

    if 'RecoveryPointDateTime' not in events:
        raise KeyError('Requires RecoveryPointDateTime')

    restore_date_time_str = events['RecoveryPointDateTime']
    restore_date_time = _parse_date_time(date_time_str=restore_date_time_str,
                                         format=DATETIME_FORMAT)
    if restore_date_time:
        return {
            'RecoveryPointDateTime': datetime.strftime(restore_date_time, DATETIME_FORMAT),
            'UseLatestRecoveryPoint': False
        }
    else:
        return {
            'RecoveryPointDateTime': 'None',
            'UseLatestRecoveryPoint': True
        }
