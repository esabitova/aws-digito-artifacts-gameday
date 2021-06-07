import logging
import random
import string
import time
import datetime
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Any, Callable, List

from boto3 import Session
from botocore.exceptions import ClientError
from boto3.dynamodb.types import STRING, NUMBER, BINARY, Binary

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


def _delete_backup(boto3_session: Session, backup_arn: str):
    return _execute_boto3_dynamodb(boto3_session=boto3_session,
                                   delegate=lambda x: x.delete_backup(
                                       BackupArn=backup_arn
                                   ))


def _delete_backup_if_exist(boto3_session: Session, backup_arn: str):
    try:
        _delete_backup(boto3_session=boto3_session, backup_arn=backup_arn)
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'BackupNotFoundException':
            log.warning(f"Backup doesn't exist `{backup_arn}`")
            return False
        raise
    return True


def _describe_backup(boto3_session: Session, backup_arn: str):
    """
    Describes the given DynamoDB backup ARN
    :param boto3_session: The boto3 session
    :param backup_arn: The name of DynamoDB table backup
    """
    return _execute_boto3_dynamodb(boto3_session=boto3_session,
                                   delegate=lambda x: x.describe_backup(
                                       BackupArn=backup_arn
                                   ))


def _check_if_backup_exists(boto3_session: Session, backup_arn: str):
    """
    Describes the given DynamoDB backup ARN and returns True if it's not deleted
    :param boto3_session: The boto3 session
    :param backup_arn: The ARN of DynamoDB table backup
    """
    try:
        description = _describe_backup(boto3_session=boto3_session, backup_arn=backup_arn)
        backup_status = description.get('BackupDescription', {})\
            .get('BackupDetails', {})\
            .get('BackupStatus', '')
        log.info(f'Backup status is {backup_status}')
        if backup_status == 'DELETED' or backup_status == '':
            return False
        else:
            return True
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'BackupNotFoundException':
            log.warning(f"Backup doesn't exist `{backup_arn}`")
            return False
        raise


def _create_backup(boto3_session: Session, table_name: str, backup_name: str):
    """
    Create a backup of the given DynamoDB table
    :param boto3_session: The boto3 session
    :param table_name: The DynamoDB table
    :param backup_name: The name of DynamoDB table backup
    """
    return _execute_boto3_dynamodb(boto3_session=boto3_session,
                                   delegate=lambda x: x.create_backup(
                                       TableName=table_name,
                                       BackupName=backup_name
                                   ))


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


def wait_table_to_be_active(table_name: str,
                            wait_sec: int,
                            delay_sec: int,
                            boto3_session: Session) -> None:
    """
    Waits until the table became active
    :param table_name: The table name
    :param delay_sec: The delay in seconds between pulling atttempts of table status
    :param boto3_session: The boto3 session
    """

    start = time.time()
    elapsed = 0
    status = ''
    while elapsed < wait_sec:
        description = _describe_table(table_name=table_name, boto3_session=boto3_session)
        status = description['Table'].get('TableStatus', '')
        log.info(f'The current table status: {status}. Table:{table_name}')
        if status == 'ACTIVE':
            return

        end = time.time()
        elapsed = end - start
        time.sleep(delay_sec)

    raise TimeoutError(f'Timeout waiting for table `{table_name}` to be active. '
                       f'Elapsed:{elapsed};The latest State:{status}')


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


def delete_backup_and_wait(backup_arn: str,
                           wait_sec: int,
                           delay_sec: int,
                           boto3_session: Session):
    exists = _delete_backup_if_exist(boto3_session=boto3_session,
                                     backup_arn=backup_arn)
    log.info(f'Backup `{backup_arn}` exists: {exists}')
    if exists:
        start = time.time()
        elapsed = 0
        while elapsed < wait_sec:
            exists = _check_if_backup_exists(boto3_session=boto3_session, backup_arn=backup_arn)
            if not exists:
                log.info(f'The backup {backup_arn} has been deleted')
                return

            end = time.time()
            elapsed = end - start
            time.sleep(delay_sec)

        raise TimeoutError(f'Timeout of waiting the backup deleted. Backup arn: {backup_arn}')


def create_backup_and_wait_for_available(table_name: str,
                                         backup_name: str,
                                         wait_sec: int,
                                         delay_sec: int,
                                         boto3_session: Session):
    backup_description = _create_backup(boto3_session=boto3_session,
                                        backup_name=backup_name,
                                        table_name=table_name)

    start = time.time()
    elapsed = 0
    backup_arn = backup_description['BackupDetails']['BackupArn']
    while elapsed < wait_sec:
        description = _describe_backup(backup_arn=backup_arn,
                                       boto3_session=boto3_session)
        backup_status = description['BackupDescription']\
            .get('BackupDetails', {})\
            .get('BackupStatus', '')
        log.info(f'Backup status is {backup_status}. Table:{table_name}')
        if backup_status == 'AVAILABLE':
            return backup_arn

        end = time.time()
        elapsed = end - start
        time.sleep(delay_sec)

    raise TimeoutError(f'Timeout of waiting the backup deleted. Backup arn: {backup_arn}')


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
    _update_table(boto3_session=boto3_session,
                  table_name=table_name,
                  ReplicaUpdates=[
                      {'Delete': {'RegionName': region}} for region in global_table_regions])

    start = time.time()
    elapsed = 0
    replicas = []
    while elapsed < wait_sec:
        description = _describe_table(table_name=table_name, boto3_session=boto3_session)
        replicas = description['Table'].get('Replicas', [])
        all_deleted = replicas == []
        log.info(f'Replica deletion status `{table_name}`: {all_deleted}. Replicas:{replicas}')
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
        replicas = description['Table'].get('Replicas', [])
        log.info(f'Table `{table_name}` replicas:{replicas}')
        if replicas:
            latest_replica_statuses = [r['ReplicaStatus']
                                       for r in replicas
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
    """
    Returns the earliest restorable timestamp
    :param table_name: The table name
    :param boto3_session: The boto3 session
    """
    continuous_backups = _describe_continuous_backups(table_name=table_name, boto3_session=boto3_session)
    if 'ContinuousBackupsDescription' not in continuous_backups:
        raise ValueError(f'Continuous backups are not enabled for the table {table_name}')
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


def get_item_single(boto3_session, table_name: str, key: dict):
    """
    Single worker for get_item stress test
    :param boto3_session The boto3 session
    :param table_name The table name
    :param key The item key
    """
    dynamo_db_client = boto3_session.client('dynamodb')
    dynamo_db_client.get_item(TableName=table_name, Key=key, ConsistentRead=True)


def get_item_async_stress_test(boto3_session: Session, table_name: str, number: int, item: dict):
    """
    Stress test for dynamo db reading item that has a schema of { attribute: value }
    Use multiple threads to make lots of simultaneous read requests
    :param boto3_session The boto3 session
    :param table_name The table name
    :param number Number of times to read item
    :param item The item attribute
    """
    futures = []
    logging.info(f'Start DynamoDB read items stress test, read {str(number)} times')
    logging.info(f'{item}')
    with ThreadPoolExecutor() as executor:
        for i in range(number):
            futures.append(
                executor.submit(get_item_single, boto3_session, table_name, item)
            )
    logging.info('DynamoDB read items stress test done')


def _get_random_value(value_type: str, length: int = 5):
    """
    Generate random values for basic DynamoDB types
    :param value_type Type of the attribute
    :param length Length of the random item
    :return Random value
    """
    if value_type == STRING:
        return ''.join(random.choice(string.ascii_uppercase) for _ in range(length))
    if value_type == NUMBER:
        return random.randint(0, 10**length)
    if value_type == BINARY:
        return Binary(bytearray(random.getrandbits(8) for _ in range(length)))


def generate_random_item(boto3_session: Session, table_name: str):
    """
    Retrieve DynamoDB table schema, get primary key and return item with random values
    :param boto3_session The boto3 session
    :param table_name The table name
    :return Random item
    """
    table_description = _describe_table(table_name=table_name, boto3_session=boto3_session)['Table']
    attributes = table_description['AttributeDefinitions']
    keys = table_description['KeySchema']
    item = {}
    # Gather primary key attributes from schema
    primary_keys = [key['AttributeName'] for key in keys]
    # Generate minimal random item for schema
    for attribute in attributes:
        attribute_name = attribute['AttributeName']
        if attribute_name in primary_keys:
            attribute_type = attribute['AttributeType']
            random_value = _get_random_value(attribute_type)
            item[attribute_name] = {attribute_type: random_value}
    logging.info(f'{item}')
    return item
