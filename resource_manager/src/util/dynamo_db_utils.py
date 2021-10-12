import datetime
import logging
import random
import string
import time
from concurrent.futures.thread import ThreadPoolExecutor
from enum import Enum, unique
from typing import Any, Callable, List, Tuple

from boto3 import Session
from boto3.dynamodb.types import BINARY, NUMBER, STRING, Binary
from botocore.exceptions import ClientError
from resource_manager.src.util.common_test_utils import execute_function_with_gaussian_delay

log = logging.getLogger()


@unique
class DynamoDbIndexType(Enum):
    GlobalSecondaryIndexes = 1,
    LocalSecondaryIndexes = 2


def _execute_boto3_dynamodb(boto3_session: Session, delegate: Callable[[Any], dict]) -> dict:
    """
    Executes the given delegate against `dynamodb` client.
    Validate if the response is successful (return code 200)
    :param delegate: The lambda function
    :param boto3_session: The boto3 session
    """
    dynamo_db_client = boto3_session.client('dynamodb')
    description = delegate(dynamo_db_client)
    if not description['ResponseMetadata']['HTTPStatusCode'] == 200:
        raise ValueError(f'Failed to execute request. Response:{description}')
    return description


def get_secondary_indexes(boto3_session: Session,
                          table_name: str,
                          index_type: DynamoDbIndexType = DynamoDbIndexType.GlobalSecondaryIndexes) -> List[str]:
    """
    Returns the list of global indexes
    :param boto3_session: The boto3 session
    :param table_name: The table name
    :return: The list of global secondary index names
    """
    result = _describe_table(boto3_session=boto3_session, table_name=table_name)
    log.debug(result)

    return [gsi['IndexName'] for gsi in result['Table'].get(index_type.name, [])]


def _describe_contributor_insights(boto3_session: Session, table_name: str, index_name: str = None) -> dict:
    """
    Describes contributor insights for the given table or index
    :param boto3_session: The boto3 session
    :param table_name: The table name
    :param index_name: The index name
    """
    if index_name:
        return _execute_boto3_dynamodb(boto3_session=boto3_session,
                                       delegate=lambda x: x.describe_contributor_insights(TableName=table_name,
                                                                                          IndexName=index_name))

    return _execute_boto3_dynamodb(boto3_session=boto3_session,
                                   delegate=lambda x: x.describe_contributor_insights(TableName=table_name))


def get_stream_settings(boto3_session: Session, table_name: str) -> Tuple[bool, str]:
    description = _describe_table(boto3_session=boto3_session,
                                  table_name=table_name)['Table']
    stream_type = description\
        .get('StreamSpecification', {})\
        .get('StreamViewType', '')
    is_enabled = description\
        .get('StreamSpecification', {})\
        .get('StreamEnabled', False)
    return is_enabled, stream_type


def get_contributor_insights_status_for_table_and_indexes(boto3_session: Session,
                                                          table_name: str) -> Tuple[str, List[dict]]:
    """
    Returns contributors insights statuses for the given table and its global secondary indexes
    :param boto3_session: The boto3 session
    :param table_name: The table name
    :return: The list of global secondary index names
    """
    STATUS_TAG = 'ContributorInsightsStatus'
    table_status = _describe_contributor_insights(boto3_session=boto3_session,
                                                  table_name=table_name)[STATUS_TAG]
    table_indexes = get_secondary_indexes(boto3_session=boto3_session,
                                          table_name=table_name)
    indexes_contributor_insights = [
        {
            'IndexName': index_name,
            'Status': _describe_contributor_insights(boto3_session=boto3_session,
                                                     table_name=table_name,
                                                     index_name=index_name)[STATUS_TAG]
        }
        for index_name in table_indexes]
    return table_status, indexes_contributor_insights


def _delete_backup(boto3_session: Session, backup_arn: str):
    return _execute_boto3_dynamodb(boto3_session=boto3_session,
                                   delegate=lambda x: x.delete_backup(
                                       BackupArn=backup_arn
                                   ))


def get_time_to_live(boto3_session: Session, table_name: str) -> dict:
    """
    Describes TTL
    :param table_name: The table name
    :return: The dictionary of TTL description
    """
    return _execute_boto3_dynamodb(boto3_session=boto3_session,
                                   delegate=lambda x: x.describe_time_to_live(TableName=table_name))[
                                       'TimeToLiveDescription']


def get_kinesis_destinations(boto3_session: Session, table_name: str) -> List[dict]:
    """
    Returns the current kinesis destination of the given table
    :param boto3_session: The boto3 session
    :param table_name: The table name
    :return: The dictionary of kinesis destination settings
    """
    return _execute_boto3_dynamodb(boto3_session=boto3_session,
                                   delegate=lambda x:
                                   x.describe_kinesis_streaming_destination(TableName=table_name))[
                                       'KinesisDataStreamDestinations']


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
    Updates the given table with specified set of parameters (`kwargs`). Calls `update_table` of `dynamodb` client
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


def get_continuous_backups_status(boto3_session: Session, table_name: str) -> str:
    """
    Returns continuous backups status
    :param boto3_session: The boto3 session
    :param table_name: The table name
    """
    continuous_backups = _describe_continuous_backups(table_name=table_name, boto3_session=boto3_session)
    return continuous_backups\
        .get('ContinuousBackupsDescription', {})\
        .get('PointInTimeRecoveryDescription', {})\
        .get('PointInTimeRecoveryStatus', '')


def wait_table_to_be_active(table_name: str,
                            wait_sec: int,
                            delay_sec: int,
                            boto3_session: Session) -> None:
    """
    Waits until the table became active
    :param table_name: The table name
    :param delay_sec: The delay in seconds between pulling attempts of table status
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


def _get_global_table_all_regions(boto3_session: Session, table_name: str) -> List[dict]:
    """
    Returns all global table regions
    :param boto3_session: The boto3 session
    :param table_name: The table name
    :return : The list of replicas
    """
    description = _describe_table(boto3_session=boto3_session, table_name=table_name)
    replicas = description['Table'].get('Replicas', [])
    return replicas


def _check_if_replicas_exist(boto3_session: Session, table_name: str) -> Tuple[List[dict], bool]:
    """
    Checks if the tables has replicas
    :param table_name: The table name
    :param boto3_session: The boto3 session
    :return : Tuple of the list of replicas and indication if the list is empty
    """
    replicas = []
    try:
        replicas = _get_global_table_all_regions(table_name=table_name, boto3_session=boto3_session)
    except ClientError as error:
        if error.response['Error']['Code'] == 'ResourceNotFoundException':
            return [], False
    replicas_exist = replicas != []
    log.info(f'Replica status `{table_name}`: {replicas_exist}. Replicas:{replicas}')
    return replicas, replicas_exist


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
    :param delay_sec: The delay in seconds between pulling attempts of table status
    :param boto3_session: The boto3 session
    """
    replicas, replicas_exist = _check_if_replicas_exist(table_name=table_name,
                                                        boto3_session=boto3_session)
    if replicas_exist:
        start = time.time()
        elapsed = 0
        while elapsed < wait_sec:
            try:
                _update_table(boto3_session=boto3_session,
                              table_name=table_name,
                              ReplicaUpdates=[
                                  {'Delete': {'RegionName': region}} for region in global_table_regions])
                break
            except ClientError as ce:
                if ce.response['Error']['Code'] == 'ValidationException':
                    if ce.response['Error']['Message'] in "The resource which you are attempting to change is in use":
                        log.warning(f"Table `{table_name}` is busy")
                    elif "Update global table operation failed because one or more replicas were " \
                         "not part of the global table" in ce.response['Error']['Message']:
                        break
            end = time.time()
            elapsed = end - start
            time.sleep(delay_sec)
        start = time.time()
        elapsed = 0
        while elapsed < wait_sec:
            replicas, replicas_exist = _check_if_replicas_exist(table_name=table_name,
                                                                boto3_session=boto3_session)
            if not replicas_exist:
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
    :param delay_sec: The delay in seconds between pulling attempts of table status
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
    :param delay_sec: The delay in seconds between pulling attempts of table status
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


def put_item_single(boto3_session, table_name: str, item: dict):
    """
    Single worker for get_item stress test
    :param boto3_session The boto3 session
    :param table_name The table name
    :param item The item key
    """
    dynamo_db_client = boto3_session.client('dynamodb')
    dynamo_db_client.put_item(TableName=table_name, Item=item)


def update_item_single(boto3_session: Session, table_name: str, item: dict, attribute_updates: dict):
    """
    Function that updates item
    :param boto3_session The boto3 session
    :param table_name The table name
    :param item The item key
    :param attribute_updates expression which defines attributes to update and how to update
    :return None
    example:
    {
      "new_attribute_name": {
        "Action": "PUT",
        "Value": {"S": "test"}
      }
    }
    where:
    "new_attribute_name" - the attribute name
    "Acton" - A value that specifies how to perform the update. Can be PUT, DELETE or ADD
    "Value" - The new value, if applicable, for this attribute.
    For mor information see the documentation:
    https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/LegacyConditionalParameters.AttributeUpdates.html
    """
    dynamo_db_client = boto3_session.client('dynamodb')
    dynamo_db_client.update_item(TableName=table_name, Key=item, AttributeUpdates=attribute_updates)


def delete_item_single(boto3_session: Session, table_name: str, item: dict):
    """
    Function that updates item
    :param boto3_session The boto3 session
    :param table_name The table name
    :param item The item key
    :return None
    """
    dynamo_db_client = boto3_session.client('dynamodb')
    dynamo_db_client.delete_item(TableName=table_name, Key=item)


def batch_write_items_single(boto3_session: Session, table_name: str, items_for_batch: list):
    """
    This function writes items into DynamoDB table
    :param boto3_session The boto3 session
    :param table_name The table name
    :param items_for_batch The list of the items for batch operation
    :return none
    """
    batch = generate_batch_for_write_operation(table_name, items_for_batch)
    dynamo_db_client = boto3_session.client('dynamodb')
    dynamo_db_client.batch_write_item(RequestItems=batch)


def batch_get_items_single(boto3_session: Session, table_name: str, items_for_batch: list):
    """
    This function gets items from DynamoDB table
    :param boto3_session The boto3 session
    :param table_name The table name
    :param items_for_batch The list of the items for batch operation
    :return none
    """
    batch = generate_batch_for_get_operation(table_name, items_for_batch)
    dynamo_db_client = boto3_session.client('dynamodb')
    dynamo_db_client.batch_get_item(RequestItems=batch)


def transact_write_items_single(boto3_session: Session, table_name: str, items_for_transaction: list):
    """
    This function performs transact_write_item operation in DynamoDB table
    :param boto3_session The boto3 session
    :param table_name The table name
    :param items_for_transaction The list of the items for transaction operation
    :return none
    """
    transaction = generate_transaction_for_write_operation(table_name, items_for_transaction)
    dynamo_db_client = boto3_session.client('dynamodb')
    dynamo_db_client.transact_write_items(TransactItems=transaction)


def transact_get_items_single(boto3_session: Session, table_name: str, items_for_transaction: list):
    """
    This function performs transact_get_item operation in DynamoDB table
    :param boto3_session The boto3 session
    :param table_name The table name
    :param items_for_transaction The list of the items for transaction operation
    :return none
    """
    transaction = generate_transaction_for_get_operation(table_name, items_for_transaction)
    dynamo_db_client = boto3_session.client('dynamodb')
    dynamo_db_client.transact_get_items(TransactItems=transaction)


def generate_list_of_attribute_updates(number_of_items: int) -> list:
    """
    Creates list of attribute_updates dictionaries
    :pram number_of_items: The number of items
    :return list
    """
    def create_attribute_update(random_string: str) -> dict:
        attribute_update = {
            "test_attribute_name": {
                "Action": "PUT",
                "Value": {"S": random_string}
            }
        }
        return attribute_update
    values = [create_attribute_update(_get_random_value(value_type='S')) for i in range(number_of_items)]
    return values


def generate_transaction_for_write_operation(table, items):
    """
    Create transaction for write items operation
    :param table the name of the table
    :param items - list of items
    :return list
    """
    transaction = [
        {
            'Put':
                {
                    "Item": item,
                    "TableName": table
                }
        } for item in items
    ]
    return transaction


def generate_transaction_for_get_operation(table, items):
    """
    Create transaction for get items operation
    :param table the name of the table
    :param items - list of items
    :return list
    """
    transaction = [
        {
            'Get':
                {
                    "Key": item,
                    "TableName": table
                }
        } for item in items
    ]
    return transaction


def generate_batch_for_write_operation(table, items):
    """
    Creates batch of items from items
    :param table the name of the table
    :param items - list of items
    :return dict
    """
    batch = {
        table: [
            {
                'PutRequest': {
                    'Item': item
                }
            }
            for item in items
        ]
    }
    return batch


def generate_batch_for_get_operation(table, items):
    """
    Creates batch of items from items
    :param table the name of the table
    :param items - list of items
    :return dict
    """
    batch = {
        table: {
            'Keys': items
        }
    }
    return batch


def transact_write_item_async_stress_test_time_divided(boto3_session: Session, table_name: str,
                                                       items: list, mu: int, sigma: float):
    """
    Stress test for dynamodb TransactWriteItems operation that has a schema of { attribute: value }
    Use multiple threads to make lots of simultaneous TransactWriteItems requests
    :param boto3_session The boto3 session
    :param table_name The table name
    :param items List of list of items for transaction
    :param mu median time
    :param sigma standard deviation
    :return None
    """
    futures = []
    logging.info(f"Start DynamoDB transact write items stress test, write transaction {len(items)} times")
    with ThreadPoolExecutor(max_workers=len(items)) as executor:
        for items_for_transaction in items:
            futures.append(
                executor.submit(execute_function_with_gaussian_delay, transact_write_items_single,
                                mu, sigma, boto3_session, table_name, items_for_transaction)
            )
    logging.info(f'DynamoDB transact write items stress test done. Items were written: {items}')


def transact_get_item_async_stress_test_time_divided(boto3_session: Session, table_name: str,
                                                     items: list, mu: int, sigma: float):
    """
    Stress test for dynamodb TransactGetItems operation that has a schema of { attribute: value }
    Use multiple threads to make lots of simultaneous TransactGetItems requests
    :param boto3_session The boto3 session
    :param table_name The table name
    :param items List of list of items for transaction
    :param mu median time
    :param sigma standard deviation
    :return None
    """
    futures = []
    logging.info(f"Start DynamoDB transact get items stress test, get transaction {len(items)} times")
    with ThreadPoolExecutor(max_workers=len(items)) as executor:
        for items_for_transaction in items:
            futures.append(
                executor.submit(execute_function_with_gaussian_delay, transact_get_items_single,
                                mu, sigma, boto3_session, table_name, items_for_transaction)
            )
    logging.info(f'DynamoDB transact get items stress test done. Items were gotten: {items}')


def batch_write_item_async_stress_test_time_divided(boto3_session: Session, table_name: str,
                                                    items: list, mu: int, sigma: float):
    """
    Stress test for dynamodb BatchWriteItem operation that has a schema of { attribute: value }
    Use multiple threads to make lots of simultaneous BatchWriteItem requests
    :param boto3_session The boto3 session
    :param table_name The table name
    :param items List of list of items for batch
    :param mu median time
    :param sigma standard deviation
    :return None
    """
    futures = []
    logging.info(f"Start DynamoDB batch write items stress test, write batch {len(items)} times")
    with ThreadPoolExecutor(max_workers=len(items)) as executor:
        for items_for_batch in items:
            futures.append(
                executor.submit(execute_function_with_gaussian_delay, batch_write_items_single,
                                mu, sigma, boto3_session, table_name, items_for_batch)
            )
    logging.info(f'DynamoDB batch write items stress test done. Items were written: {items}')


def batch_get_item_async_stress_test_time_divided(boto3_session: Session, table_name: str,
                                                  items: list, mu: int, sigma: float):
    """
    Stress test for dynamodb BatchGetItem operation that has a schema of { attribute: value }
    Use multiple threads to make lots of simultaneous BatchGetItem requests
    :param boto3_session The boto3 session
    :param table_name The table name
    :param items List of list of items for batch
    :param mu median time
    :param sigma standard deviation
    :return None
    """
    futures = []
    logging.info(f"Start DynamoDB batch get items stress test, get batch {len(items)} times")
    with ThreadPoolExecutor(max_workers=len(items)) as executor:
        for items_for_batch in items:
            futures.append(
                executor.submit(execute_function_with_gaussian_delay, batch_get_items_single,
                                mu, sigma, boto3_session, table_name, items_for_batch)
            )
    logging.info(f'DynamoDB batch get items stress test done. Items were gotten: {items}')


def update_item_async_stress_test_time_divided(boto3_session: Session, table_name: str, item: dict,
                                               updates: list, mu: int, sigma: float):
    """
    Stress test for dynamodb updating item that has a schema of { attribute: value }
    Use multiple threads to make lots of simultaneous update requests
    :param boto3_session The boto3 session
    :param table_name The table name
    :param updates List of update_items dictionary
    :param item The item attribute
    :param mu median time
    :param sigma standard deviation
    :return None
    """
    futures = []
    logging.info(f"Start DynamoDB update items stress test, update {len(updates)} times")
    with ThreadPoolExecutor(max_workers=len(updates)) as executor:
        for update in updates:
            futures.append(
                executor.submit(execute_function_with_gaussian_delay, update_item_single,
                                mu, sigma, boto3_session, table_name, item, update)
            )
    logging.info(f'DynamoDB update items stress test done. Updates were applied: {updates}')


def delete_item_async_stress_test_time_divided(boto3_session: Session, table_name: str,
                                               items: list, mu: int, sigma: float):
    """
    Stress test for dynamodb deleting item that has a schema of { attribute: value }
    Use multiple threads to make lots of simultaneous delete requests
    :param boto3_session The boto3 session
    :param table_name The table name
    :param items The list of the items to delete
    :param mu median time
    :param sigma standard deviation
    :return None
    """
    futures = []
    logging.info(f"Start DynamoDB delete items stress test, items to delete: {str(items)}")
    with ThreadPoolExecutor(max_workers=len(items)) as executor:
        for item in items:
            futures.append(
                executor.submit(execute_function_with_gaussian_delay, delete_item_single,
                                mu, sigma, boto3_session, table_name, item)
            )
    logging.info(f'DynamoDB delete items stress test done. Items: {items}')


def get_item_async_stress_test_time_divided(boto3_session: Session, table_name: str,
                                            number: int, item: dict, mu: int, sigma: float):
    """
    Stress test for dynamo db reading item that has a schema of { attribute: value }
    Use multiple threads to make lots of simultaneous read requests
    :param boto3_session The boto3 session
    :param table_name The table name
    :param number Number of times to read item
    :param item The item attribute
    :param mu median time
    :param sigma standard deviation
    :return None
    """
    futures = []
    logging.info(f'Start DynamoDB read items stress test, read {str(number)} times')
    with ThreadPoolExecutor(max_workers=number) as executor:
        for i in range(number):
            futures.append(
                executor.submit(execute_function_with_gaussian_delay, get_item_single,
                                mu, sigma, boto3_session, table_name, item)
            )
    logging.info(f'DynamoDB read items stress test done. Item {item} were written {str(number)} times.')


def put_item_async_stress_test_time_divided(boto3_session: Session, table_name: str,
                                            items: list, mu: int, sigma: float):
    """
    Stress test for dynamo db reading item that has a schema of { attribute: value }
    Use multiple threads to make lots of simultaneous read requests
    :param items List of items to put into table
    :param boto3_session The boto3 session
    :param table_name The table name
    :param items The items
    :param mu median time
    :param sigma standard deviation
    :return None
    """
    futures = []
    items_size = len(items)
    logging.info(f'Start DynamoDB put items stress test, write {items_size} times')
    with ThreadPoolExecutor(max_workers=items_size) as executor:
        for item in items:
            futures.append(
                executor.submit(execute_function_with_gaussian_delay, put_item_single,
                                mu, sigma, boto3_session, table_name, item)
            )
    logging.info(f'DynamoDB put items stress test done. Items: {items}')


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
    with ThreadPoolExecutor() as executor:
        for i in range(number):
            futures.append(
                executor.submit(get_item_single, boto3_session, table_name, item)
            )
    logging.info('DynamoDB read items stress test done')


def put_item_async_stress_test(boto3_session: Session, table_name: str, items: list):
    """
    Stress test for dynamo db reading item that has a schema of { attribute: value }
    Use multiple threads to make lots of simultaneous read requests
    :param items List of items to put into table
    :param boto3_session The boto3 session
    :param table_name The table name
    :param items The items
    """
    futures = []
    items_size = len(items)
    logging.info(f'Start DynamoDB put items stress test, write {items_size} times')
    with ThreadPoolExecutor() as executor:
        for item in items:
            futures.append(
                executor.submit(put_item_single, boto3_session, table_name, item)
            )
    logging.info('DynamoDB put items stress test done')


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


def generate_random_item(boto3_session: Session, table_name: str, total_number: int = 1):
    """
    Retrieve DynamoDB table schema, get primary key and return item with random values
    :param total_number items to generate
    :param boto3_session The boto3 session
    :param table_name The table name
    :return Random item
    """
    table_description = _describe_table(table_name=table_name, boto3_session=boto3_session)['Table']
    attributes = table_description['AttributeDefinitions']
    keys = table_description['KeySchema']
    items = []
    # Gather primary key attributes from schema
    primary_keys = [key['AttributeName'] for key in keys]
    # Generate minimal random item for schema
    for i in range(total_number):
        item = {}
        for attribute in attributes:
            attribute_name = attribute['AttributeName']
            if attribute_name in primary_keys:
                attribute_type = attribute['AttributeType']
                random_value = _get_random_value(attribute_type)
                item[attribute_name] = {attribute_type: random_value}
        items.append(item)

    logging.info(f'generated {len(items)} items: {items}')
    if len(items) == 1:
        return items[0]
    return items
