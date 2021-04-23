
import logging
from typing import Any, Callable

import boto3


def _execute_boto3_auto_scaling(delegate: Callable[[Any], dict]) -> dict:
    """
    Executes the given delegate against `application-autoscaling` client.
    Validates is the response is successfull (return code `200`)
    :param delegate: The lambda function
    :return: The response of AWS API
    """
    auto_scaling_client = boto3.client('application-autoscaling')
    description = delegate(auto_scaling_client)
    if not description['ResponseMetadata']['HTTPStatusCode'] == 200:
        logging.error(description)
        raise ValueError('Failed to execute request')
    return description


def _describe_scalable_targets(table_name: str) -> dict:
    """
    Describes scalable targets
    :param table_name: The table name
    :return: The response of AWS API
    """
    return _execute_boto3_auto_scaling(
        delegate=lambda x: x.describe_scalable_targets(ServiceNamespace='dynamodb',
                                                       ResourceIds=[f'table/{table_name}']))


def _register_scalable_target(table_name: str, dimension: str, min_cap: int, max_cap: int) -> dict:
    """
    Describes scalable targets
    :param table_name: The table name
    :param dimension: The dimension
    :param min_cap: The minimum of scaling target
    :param max_cap: The maximum of scaling target
    :return: The response of AWS API
    """
    return _execute_boto3_auto_scaling(
        delegate=lambda x: x.register_scalable_target(ServiceNamespace='dynamodb',
                                                      ScalableDimension=dimension,
                                                      MinCapacity=min_cap,
                                                      MaxCapacity=max_cap,
                                                      ResourceId=f'table/{table_name}'))


def register_scaling_targets(events: dict, context: dict) -> dict:
    """
    Returns scalable targets
    :param events: The dictionary that supposed to have the following keys:
    * `TableName` - The table name
    * `ScalingTargets` - The array of object that contains attributes of scaling targets, namely
    `ScalableDimension`, `Min` and `Max`
    :return: The dictionary that contains a JSON dump of an array of objects
    that contains attributes of scaling targets, namely
    `ScalableDimension`, `Min` and `Max`
    """
    if 'TableName' not in events:
        raise KeyError('Requires TableName')
    if 'ScalingTargets' not in events:
        raise KeyError('Requires ScalingTargets')

    table_name: str = events['TableName']
    scaling_targets = events['ScalingTargets']
    for target in scaling_targets:
        _register_scalable_target(table_name=table_name,
                                  dimension=target['ScalableDimension'],
                                  min_cap=target["MinCapacity"],
                                  max_cap=target["MaxCapacity"])

    return _describe_scalable_targets(table_name=table_name)['ScalableTargets']
