import logging
import time
import datetime

from boto3 import Session
from botocore.exceptions import ClientError

log = logging.getLogger()


def _describe_table(table_name: str, boto3_session: Session):
    dynamo_db_client = boto3_session.client('dynamodb')
    description = dynamo_db_client.describe_table(TableName=table_name)
    if not description['ResponseMetadata']['HTTPStatusCode'] == 200:
        log.error(description)
        raise ValueError('Failed to describe table')
    return description


def _describe_continuous_backups(table_name: str, boto3_session: Session):
    dynamo_db_client = boto3_session.client('dynamodb')
    continuous_backups = dynamo_db_client.describe_continuous_backups(TableName=table_name)
    if not continuous_backups['ResponseMetadata']['HTTPStatusCode'] == 200:
        log.error(continuous_backups)
        raise ValueError('Failed to get continuous backups info')
    return continuous_backups


def _check_if_table_deleted(table_name: str, boto3_session: Session):
    try:
        description = _describe_table(table_name=table_name,
                                      boto3_session=boto3_session)
        status = description['Table']['TableStatus']
        log.info(f'The current status of the table `{table_name}` is {status}')
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'ResourceNotFoundException':
            log.warning(f"The table `{table_name}` doesn't exist, happy path")
            return True
    return False


def get_earliest_recovery_point_in_time(table_name: str, boto3_session: Session) \
        -> datetime.datetime:
    continuous_backups = _describe_continuous_backups(table_name=table_name, boto3_session=boto3_session)
    backups_description = continuous_backups['ContinuousBackupsDescription']
    return backups_description['PointInTimeRecoveryDescription']['EarliestRestorableDateTime']


def drop_and_wait_dynamo_db_table_if_exists(table_name: str,
                                            boto3_session: Session,
                                            wait_sec: int = 300,
                                            delay_sec=20) -> None:
    """
    TBD
    :param lambda_arn: The ARN of Lambda Function
    :return: The memory size in megabytes
    """
    dynamo_db_client = boto3_session.client('dynamodb')
    start = time.time()
    elapsed = 0
    while elapsed < wait_sec:
        try:
            deletion_result = dynamo_db_client.delete_table(TableName=table_name)
            log.info(deletion_result)
            if not deletion_result['ResponseMetadata']['HTTPStatusCode'] == 200:
                log.error(deletion_result)
                raise ValueError('Failed to delete table')
        except ClientError as ce:
            code = ce.response['Error']['Code']
            log.error(f"error when deleting table {table_name}:{code}")
            if code == 'ResourceNotFoundException':
                log.warning(f"The table {table_name} doesn't exist, happy path")
                return
        finally:
            end = time.time()
            elapsed = end - start
            time.sleep(delay_sec)

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
