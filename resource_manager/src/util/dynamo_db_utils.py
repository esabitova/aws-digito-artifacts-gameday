import logging
import time
import datetime
from typing import Any, Callable, List

from boto3 import Session
from botocore.exceptions import ClientError

log = logging.getLogger()


def _execute_boto3_dynamodb(boto3_session: Session, delegate: Callable[[Any], dict]) -> dict:
    """
    Executes the given delegate against `dynamodb` client.
    Validates is the response is successfull (return code `200`)
    :param delegate: The lambda function
    :param boto3_session: The boto3 session
    """
    dynamo_db_client = boto3_session.client('dynamodb')
    description = delegate(dynamo_db_client)
    if not description['ResponseMetadata']['HTTPStatusCode'] == 200:
        raise ValueError(f'Failed to execute request. Response:{description}')
    return description


def _update_table(boto3_session: Session, table_name: str, **kwargs) -> dict:
    """
    Updates the given table with specified set of parametes (`kwargs`). Calls `update_table` of `dynamodb` client
    :param table_name: The table name
    :param kwargs: The parameters of update_table
    :param boto3_session: The boto3 session
    """
    return _execute_boto3_dynamodb(boto3_session=boto3_session,
                                   delegate=lambda x: x.update_table(TableName=table_name, **kwargs))


def _describe_table(table_name: str, boto3_session: Session) -> dict:
    """
    Returns a response of `describe_table` method of `dynamodb` client
    :param table_name: The table name
    :param boto3_session: The boto3 session
    """
    return _execute_boto3_dynamodb(boto3_session=boto3_session,
                                   delegate=lambda x: x.describe_table(TableName=table_name))


def _describe_continuous_backups(table_name: str, boto3_session: Session) -> dict:
    """
    Returns a response of `describe_continuous_backups` method of `dynamodb` client
    :param table_name: The table name
    :param boto3_session: The boto3 session
    """
    return _execute_boto3_dynamodb(boto3_session=boto3_session,
                                   delegate=lambda x: x.describe_continuous_backups(TableName=table_name))


def _check_if_table_deleted(table_name: str, boto3_session: Session) -> bool:
    """
    Checks if the table is deleted
    :param table_name: The table name
    :param boto3_session: The boto3 session
    :return : `True` if the table doesn't exist, `False` otherwise
    """
    try:
        description = _describe_table(table_name=table_name,
                                      boto3_session=boto3_session)
        status = description['Table']['TableStatus']
        log.info(f'The current status of the table `{table_name}` is {status}')
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'ResourceNotFoundException':
            log.warning(f"Table `{table_name}` has been deleted")
            return True
    return False


def update_time_to_live(table_name: str, is_enabled: bool, attribute_name: str, boto3_session: Session) -> dict:
    """
    Updates TLL setting for the given table
    :param table_name: The table name
    :param is_enabled: The flag that says if TTL needs to be enabled
    :param attribute_name: The name of the attribute that will be used to decided on TTL
    :param boto3_session: The boto3 session
    """
    return _execute_boto3_dynamodb(boto3_session=boto3_session,
                                   delegate=lambda x: x.update_time_to_live(TableName=table_name,
                                                                            TimeToLiveSpecification={
                                                                                "Enabled": is_enabled,
                                                                                "AttributeName": attribute_name
                                                                            }))


def add_kinesis_destinations(table_name: str, kds_arn: str, boto3_session: Session) -> dict:
    """
    Adds a new kinesis destination
    :param table_name: The table name
    :param kds_arn: The ARN of Kinesis Data Stream
    :param boto3_session: The boto3 session
    """
    return \
        _execute_boto3_dynamodb(boto3_session=boto3_session,
                                delegate=lambda x:
                                x.enable_kinesis_streaming_destination(TableName=table_name,
                                                                       StreamArn=kds_arn))


def try_remove_replica(table_name: str,
                       global_table_regions: List[str],
                       boto3_session: Session,
                       retry_count: int = 5,
                       delay_sec: int = 20) -> None:
    """
    Gives a try to remove replica. Sometimes the table is in use and the request fails.
    This function makes several retries and the given delay
    :param table_name: The table name
    :param global_table_regions: The list of regions where replica should be removed from
    :param delay_sec: The delay in seconds between request attempts
    :param retry_count: The number of retries
    :param boto3_session: The boto3 session
    """
    i: int = 0
    while i < retry_count:
        try:
            _update_table(boto3_session=boto3_session,
                          table_name=table_name,
                          ReplicaUpdates=[
                              {'Delete': {'RegionName': region}} for region in global_table_regions])
            return
        except ClientError as ce:
            if ce.response['Error']['Code'] == 'ResourceInUseException':
                log.warning(f"The table `{table_name}` current in use (something in progress) '\
                'skipping this error while remove replica. '\
                    f'The next try later in {delay_sec} seconds")

        time.sleep(delay_sec)
        i += 1


def remove_global_table_and_wait_for_active(table_name: str,
                                            global_table_regions: List[str],
                                            wait_sec: int,
                                            delay_sec: int,
                                            boto3_session: Session) -> None:
    """
    Removes replicas in the given regions and waits them to be removed
    :param table_name: The table name
    :param global_table_regions: The list of regions where replica should be removed from
    :param delay_sec: The delay in seconds between pulling atttempts of table status
    :param boto3_session: The boto3 session
    """
    try_remove_replica(boto3_session=boto3_session,
                       global_table_regions=global_table_regions,
                       table_name=table_name)

    start = time.time()
    elapsed = 0
    replicas = []
    while elapsed < wait_sec:
        description = _describe_table(table_name=table_name, boto3_session=boto3_session)
        replicas = description['Table'].get('Replicas', [])
        all_deleted = replicas == []
        log.info(f'Replica deletion status: {all_deleted}. Replicas:{replicas}')
        if all_deleted:
            return

        end = time.time()
        elapsed = end - start
        time.sleep(delay_sec)

    raise TimeoutError('Timeout waiting for global table being deleted. '
                       f'Elapsed:{elapsed};The latest State:{replicas}')


def add_global_table_and_wait_for_active(table_name: str,
                                         global_table_regions: List[str],
                                         wait_sec: int,
                                         delay_sec: int,
                                         boto3_session: Session) -> None:
    """
    Adds global table in the given regions and waits when replicas and the table it self became ACTIVE
    :param table_name: The table name
    :param global_table_regions: The list of regions
    :param delay_sec: The delay in seconds between pulling atttempts of table status
    :param boto3_session: The boto3 session
    """
    _update_table(boto3_session=boto3_session,
                  table_name=table_name,
                  ReplicaUpdates=[
                      {'Create': {'RegionName': region}} for region in global_table_regions])

    start = time.time()
    elapsed = 0
    latest_replica_statuses = []
    latest_table_status = []
    while elapsed < wait_sec:
        description = _describe_table(table_name=table_name, boto3_session=boto3_session)
        log.info(description)

        latest_replica_statuses = [r['ReplicaStatus']
                                   for r in description['Table'].get('Replicas', [])
                                   if r['RegionName'] in global_table_regions]
        all_active = all([s == 'ACTIVE'
                          for s in latest_replica_statuses])

        latest_table_status = description['Table']['TableStatus']
        table_active = latest_table_status == 'ACTIVE'
        log.info(f'Current status of table and replica. Replicas is active={all_active}; '
                 f'Table is active={table_active}')
        if all_active and table_active:
            return

        end = time.time()
        elapsed = end - start
        time.sleep(delay_sec)

    raise TimeoutError('Timeout waiting for global table to be Active. '
                       f'Elapsed:{elapsed};'
                       f'The latest table status:{latest_table_status};'
                       f'The latest replicas statuses:{latest_replica_statuses};')


def get_earliest_recovery_point_in_time(table_name: str, boto3_session: Session) -> datetime.datetime:
    continuous_backups = _describe_continuous_backups(table_name=table_name, boto3_session=boto3_session)
    backups_description = continuous_backups['ContinuousBackupsDescription']
    return backups_description['PointInTimeRecoveryDescription']['EarliestRestorableDateTime']


def drop_and_wait_dynamo_db_table_if_exists(table_name: str,
                                            boto3_session: Session,
                                            wait_sec: int = 300,
                                            delay_sec=20) -> None:
    """
    Requests table deletion and waits until the given table is gone
    :param table_name: The table name
    :param wait_sec: The number of seconds to wait table deletion
    :param delay_sec: The delay in seconds between pulling atttempts of table status
    :param boto3_session: The boto3 session
    """
    start = time.time()
    elapsed = 0
    try:
        _execute_boto3_dynamodb(boto3_session=boto3_session,
                                delegate=lambda x: x.delete_table(TableName=table_name))
    except ClientError as ce:
        code = ce.response['Error']['Code']
        log.error(f"error when deleting table {table_name}:{code}")
        if code == 'ResourceNotFoundException':
            log.warning(f"The table {table_name} doesn't exist, happy path")
            return

    while elapsed < wait_sec:
        log.info(f"Waiting {table_name} to be deleted. Elapsed {elapsed} seconds")
        table_deleted = _check_if_table_deleted(table_name=table_name,
                                                boto3_session=boto3_session)
        if table_deleted:
            return

        end = time.time()
        elapsed = end - start
        time.sleep(delay_sec)

    raise TimeoutError(f'Timeout of waiting `{table_name}` deletion')
