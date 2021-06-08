
import logging
from typing import Any, Callable, Iterator

from boto3.session import Session


def _execute_boto3_auto_scaling(boto3_session: Session, delegate: Callable[[Any], dict]) -> dict:
    """
    Executes the given delegate against `application-autoscaling` client.
    Validates is the response is successfull (return code `200`)
    :param delegate: The lambda function
    :return: The response of AWS API
    """
    auto_scaling_client = boto3_session.client('application-autoscaling')
    description = delegate(auto_scaling_client)
    if not description['ResponseMetadata']['HTTPStatusCode'] == 200:
        logging.error(description)
        raise ValueError('Failed to execute request')
    return description


def _execute_boto3_auto_scaling_paginator(boto3_session: Session, func_name: str,
                                          search_exp: str = None, **kwargs) -> Iterator[Any]:
    """
    Executes the given function with pagination
    :param func_name: The function name of auto_scaling client
    :param search_exp: The search expression to return elements
    :param kwargs: The arguments of `func_name`
    :return: The iterator over elements on pages
    """
    autoscaling_db_client = boto3_session.client('application-autoscaling')
    paginator = autoscaling_db_client.get_paginator(func_name)
    page_iterator = paginator.paginate(**kwargs)
    if search_exp:
        return page_iterator.search(search_exp)
    else:
        return page_iterator


def _describe_scalable_targets_for_dynamodb_table(boto3_session: Session, table_name: str) -> Iterator[dict]:
    """
    Describes scalable targets
    :param table_name: The table name
    :return: The response of AWS API
    """
    return [{'ScalableDimension': x['ScalableDimension'],
             'MinCapacity':int(x["MinCapacity"]),
             'MaxCapacity':int(x["MaxCapacity"]),
             'RoleARN':x['RoleARN']}
            for x in _execute_boto3_auto_scaling_paginator(boto3_session=boto3_session,
                                                           func_name='describe_scalable_targets',
                                                           search_exp='ScalableTargets[]',
                                                           ServiceNamespace='dynamodb',
                                                           ResourceIds=[f'table/{table_name}'])]


def _deregister_scalable_target_for_dynamodb_table(boto3_session: Session, table_name: str, dimension: str) -> dict:
    """
    Deregisters scaling target for the given dynamodb table
    :param table_name: The table name
    :param dimension: The dimension
    :return: The response of AWS API
    """
    return _execute_boto3_auto_scaling(boto3_session=boto3_session,
                                       delegate=lambda x:
                                       x.deregister_scalable_target(ServiceNamespace='dynamodb',
                                                                    ScalableDimension=dimension,
                                                                    ResourceId=f'table/{table_name}'))


def deregister_all_scaling_target_all_dynamodb_table(boto3_session: Session, table_name: str) -> dict:
    """
    Describes scaling target for the given table and deregisters all of them
    :param boto3_session: The boto3 session
    :param boto3_session: The boto3 session
    :param boto3_session: The boto3 session
    """
    table_result = _describe_scalable_targets_for_dynamodb_table(boto3_session=boto3_session, table_name=table_name)

    scaling_targets = [{'ScalableDimension': x['ScalableDimension'],
                        'MinCapacity':int(x["MinCapacity"]),
                        'MaxCapacity':int(x["MaxCapacity"]),
                        'RoleARN':x['RoleARN']} for x in table_result]
    for x in scaling_targets:
        _deregister_scalable_target_for_dynamodb_table(boto3_session=boto3_session,
                                                       table_name=table_name,
                                                       dimension=x['ScalableDimension'])
