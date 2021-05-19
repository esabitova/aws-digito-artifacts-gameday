import logging
from typing import Any, Callable, List

from boto3.session import Session


def _execute_boto3_cloudwatch(boto3_session: Session, delegate: Callable[[Any], dict]) -> dict:
    """
    Executes the given delegate against `cloudwatch` client.
    Validates is the response is successfull (return code `200`)
    :param delegate: The lambda function
    """
    cloudwatch_client = boto3_session.client('cloudwatch')
    response = delegate(cloudwatch_client)
    if not response['ResponseMetadata']['HTTPStatusCode'] == 200:
        logging.error(response)
        raise ValueError('Failed to execute request')
    return response


def _describe_metric_alarms(boto3_session: Session):
    """
    Returns all alarms setup in the current region
    :param boto3_session: The boto3 session
    """
    return _execute_boto3_cloudwatch(boto3_session=boto3_session,
                                     delegate=lambda x:
                                     x.describe_alarms(AlarmTypes=['MetricAlarm']))


def _delete_alarms(boto3_session: Session, alarms_to_delete: List[str]):
    """
    Deletes the given alarms
    :param alarms_to_delete: The list of alarms to delete
    :param boto3_session: The boto3 session
    """
    return _execute_boto3_cloudwatch(boto3_session=boto3_session,
                                     delegate=lambda x:
                                     x.delete_alarms(AlarmNames=alarms_to_delete))


def delete_alarms_for_dynamo_db_table(boto3_session: Session, table_name: str):
    """
    Gets all the alarms in the region and selects metrics alarms that has the given
    dynamodb table in their dimensions. Deletes selected alarms
    :param alarms_to_delete: The list of alarms to delete
    :param boto3_session: The boto3 session
    """
    source_alarms = _describe_metric_alarms(boto3_session=boto3_session)

    alarms_to_delete = []
    for alarm in filter(lambda x: x['Namespace'] == 'AWS/DynamoDB', source_alarms.get('MetricAlarms', [])):
        for dimension in alarm['Dimensions']:
            if dimension['Name'] == 'TableName' and \
                    dimension['Value'] == table_name:
                alarms_to_delete.append(alarm['AlarmName'])
                break
    _delete_alarms(boto3_session=boto3_session, alarms_to_delete=alarms_to_delete)
