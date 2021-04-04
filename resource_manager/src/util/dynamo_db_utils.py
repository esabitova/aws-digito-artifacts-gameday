import logging
import time

from boto3 import Session
from botocore.exceptions import ClientError

log = logging.getLogger()


def _check_if_table_deleted(table_name: str, boto3_session: Session):
    dynamo_db_client = boto3_session.client('dynamodb')
    try:
        description = dynamo_db_client.describe_table(TableName=table_name)
        if not description['ResponseMetadata']['HTTPStatusCode'] == 200:
            log.error(description)
            raise ValueError('Failed to delete table')
        status = description['Table']['TableStatus']
        log.info(f'The current status of the table `{table_name}` is {status}')
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'ResourceNotFoundException':
            log.warning(f"The table `{table_name}` doesn't exist, happy path")
            return True
    return False


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
                log.warn(f"The table {table_name} doesn't exist, happy path")
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
