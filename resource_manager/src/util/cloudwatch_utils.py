import logging
from typing import Any, Callable, Iterator, List

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


def _execute_boto3_cloudwatch_paginator(boto3_session: Session,
                                        func_name: str,
                                        search_exp: str = None,
                                        **kwargs) -> Iterator[Any]:
    """
    Executes the given function with pagination
    :param func_name: The function name of cloudwatch client
    :param search_exp: The search expression to return elements
    :param kwargs: The arguments of `func_name`
    :return: The iterator over elements on pages
    """
    dynamo_db_client = boto3_session.client('cloudwatch')
    paginator = dynamo_db_client.get_paginator(func_name)
    page_iterator = paginator.paginate(**kwargs)
    if search_exp:
        return page_iterator.search(search_exp)
    else:
        return page_iterator


def _describe_metric_alarms(boto3_session: Session,
                            alarm_names: List[str] = None) -> Iterator[dict]:
    """
    Returns all alarms setup in the current region
    """
    if alarm_names:
        return _execute_boto3_cloudwatch_paginator(boto3_session=boto3_session,
                                                   func_name='describe_alarms',
                                                   search_exp='MetricAlarms[]',
                                                   AlarmTypes=['MetricAlarm'],
                                                   AlarmNames=alarm_names)
    else:
        return _execute_boto3_cloudwatch_paginator(boto3_session=boto3_session,
                                                   func_name='describe_alarms',
                                                   search_exp='MetricAlarms[]',
                                                   AlarmTypes=['MetricAlarm'])


def _delete_alarms(boto3_session: Session, alarms_to_delete: List[str]):
    """
    Deletes the given alarms
    :param alarms_to_delete: The list of alarms to delete
    :param boto3_session: The boto3 session
    """
    return _execute_boto3_cloudwatch(boto3_session=boto3_session,
                                     delegate=lambda x:
                                     x.delete_alarms(AlarmNames=alarms_to_delete))


def get_metric_alarms_for_table(boto3_session: Session,
                                table_name: str,
                                alarms_names: List[str] = None) -> Iterator[dict]:
    alarms = _describe_metric_alarms(boto3_session=boto3_session, alarm_names=alarms_names)
    for alarm in filter(lambda x: x.get('Namespace', '') == 'AWS/DynamoDB', alarms):
        for dimension in alarm['Dimensions']:
            if dimension['Name'] == 'TableName' and \
                    dimension['Value'] == table_name:
                yield alarm


def delete_alarms_for_dynamo_db_table(boto3_session: Session, table_name: str):
    """
    Gets all the alarms in the region and selects metrics alarms that has the given
    dynamodb table in their dimensions. Deletes selected alarms
    :param alarms_to_delete: The list of alarms to delete
    :param boto3_session: The boto3 session
    """
    alarms = get_metric_alarms_for_table(boto3_session=boto3_session, table_name=table_name)
    alarms_to_delete = [alarm['AlarmName'] for alarm in alarms]
    if alarms_to_delete:
        _delete_alarms(boto3_session=boto3_session, alarms_to_delete=alarms_to_delete)
