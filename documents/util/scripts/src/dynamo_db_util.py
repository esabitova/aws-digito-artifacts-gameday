import logging
import boto3
from datetime import datetime
from typing import Union


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _parse_recovery_date_time(restore_date_time_str: str, format: str) -> Union[datetime, None]:
    if restore_date_time_str.strip():
        try:
            return datetime.strptime(restore_date_time_str, format)
        except ValueError as ve:
            print(ve)
    return None


def _update_table(table_name: str, **kwargs):
    dynamo_db_client = boto3.client('dynamodb')
    description = dynamo_db_client.update_table(TableName=table_name, **kwargs)
    if not description['ResponseMetadata']['HTTPStatusCode'] == 200:
        logging.error(description)
        raise ValueError('Failed to update table')
    return description


def update_table_stream(events: dict, context: dict):
    if 'StreamEnabled' not in events:
        raise KeyError('Requires StreamEnabled')
    if 'TableName' not in events:
        raise KeyError('Requires TableName')
    if 'StreamViewType' not in events:
        raise KeyError('Requires StreamViewType')

    stream_enabled = events['StreamEnabled']
    table_name = events['TableName']
    if stream_enabled:
        stream_view_type = events['StreamViewType']
        settings = {
            "StreamSpecification": {
                "StreamEnabled": stream_enabled,
                "StreamViewType": stream_view_type
            }
        }
        result = _update_table(table_name=table_name, **settings)
        specification = result.get('StreamSpecification', {})
        return {
            'StreamEnabled': specification.get('StreamEnabled', False),
            'StreamViewType': specification.get('StreamViewType', '')
        }


def parse_recovery_date_time(events: dict, context: dict) -> dict:
    """
    Tries to parses the given `RecoveryPointDateTime` and returns it back if success
    :return: The dictionary that indicates if latest availabe recovery point should be used
    """
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

    if 'RecoveryPointDateTime' not in events:
        raise KeyError('Requires ExecutionId')

    restore_date_time_str = events['RecoveryPointDateTime']
    restore_date_time = _parse_recovery_date_time(restore_date_time_str=restore_date_time_str,
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
