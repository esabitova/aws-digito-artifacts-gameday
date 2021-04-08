import logging
import boto3
import json
from datetime import datetime
from typing import List, Union


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _parse_recovery_date_time(restore_date_time_str: str, format: str) -> Union[datetime, None]:
    if restore_date_time_str.strip():
        try:
            return datetime.strptime(restore_date_time_str, format)
        except ValueError as ve:
            print(ve)
    return None


def _execute_boto3_dynamodb(delegate):
    dynamo_db_client = boto3.client('dynamodb')
    description = delegate(dynamo_db_client)
    if not description['ResponseMetadata']['HTTPStatusCode'] == 200:
        logging.error(description)
        raise ValueError('Failed to execute request')
    return description


def _describe_kinesis_destinations(table_name: str):
    return _execute_boto3_dynamodb(
        delegate=lambda x: x.describe_kinesis_streaming_destination(TableName=table_name))


def _enable_kinesis_destinations(table_name: str, kds_arn: str):
    return _execute_boto3_dynamodb(
        delegate=lambda x: x.enable_kinesis_streaming_destination(TableName=table_name,
                                                                  StreamArn=kds_arn))


def _update_time_to_live(table_name: str, is_enabled: bool, attribute_name: str):
    return _execute_boto3_dynamodb(
        delegate=lambda x: x.update_time_to_live(TableName=table_name,
                                                 TimeToLiveSpecification={
                                                     "Enabled": is_enabled,
                                                     "AttributeName": attribute_name
                                                 }))


def _update_table(table_name: str, **kwargs):
    return _execute_boto3_dynamodb(
        delegate=lambda x: x.update_table(TableName=table_name, **kwargs))


def update_time_to_live(events: dict, context: dict) -> List:
    if 'TableName' not in events:
        raise KeyError('Requires TableName')
    if 'Status' not in events:
        raise KeyError('Requires Status')
    is_enabled = events['AttributeName'] == 'ENABLED'
    if not is_enabled:
        return{
            "Enabled": False,
        }

    if is_enabled and 'AttributeName' not in events:
        raise KeyError('Requires AttributeName when status is ENABLED')

    table_name = events['TableName']
    attribute_name = events.get('AttributeName', '')
    logging.info(f'table:{table_name};kinesis is_enabled: {is_enabled};')
    result = _update_time_to_live(table_name=table_name, is_enabled=is_enabled, attribute_name=attribute_name)

    return {**result}


def add_kinesis_destinations(events: dict, context: dict) -> List:
    if 'TableName' not in events:
        raise KeyError('Requires TableName')
    if 'Destinations' not in events:
        raise KeyError('Requires Destinations')
    table_name = events['TableName']
    destinations = json.loads(events['Destinations'])
    logging.info(f'table:{table_name};kinesis destinations: {destinations}')
    for d in destinations:
        _enable_kinesis_destinations(table_name=table_name, kds_arn=d['StreamArn'])

    return get_active_kinesis_destinations(events=events,
                                           context=context)


def get_active_kinesis_destinations(events: dict, context: dict) -> List:
    if 'TableName' not in events:
        raise KeyError('Requires TableName')
    ACTIVE_STATUSES = ['ACTIVE', 'ENABLING']
    table_name = events['TableName']
    kinesis_destinations = _describe_kinesis_destinations(table_name=table_name)

    return {
        "KinesisDestinations":
        json.dumps([d for d in kinesis_destinations['KinesisDataStreamDestinations']
                   if d['DestinationStatus'] in ACTIVE_STATUSES])
    }


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
