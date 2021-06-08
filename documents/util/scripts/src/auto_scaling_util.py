
import logging
from typing import Any, Callable, Iterator

import boto3
from botocore.config import Config

boto3_config = Config(retries={'max_attempts': 20, 'mode': 'standard'})


def _execute_boto3_auto_scaling(delegate: Callable[[Any], dict]) -> dict:
    """
    Executes the given delegate against `application-autoscaling` client.
    Validates is the response is successfull (return code `200`)
    :param delegate: The lambda function
    :return: The response of AWS API
    """
    auto_scaling_client = boto3.client('application-autoscaling', config=boto3_config)
    description = delegate(auto_scaling_client)
    if not description['ResponseMetadata']['HTTPStatusCode'] == 200:
        logging.error(description)
        raise ValueError('Failed to execute request')
    return description


def _execute_boto3_auto_scaling_paginator(func_name: str, search_exp: str = None, **kwargs) -> Iterator[Any]:
    """
    Executes the given function with pagination
    :param func_name: The function name of auto_scaling client
    :param search_exp: The search expression to return elements
    :param kwargs: The arguments of `func_name`
    :return: The iterator over elements on pages
    """
    autoscaling_db_client = boto3.client('application-autoscaling', config=boto3_config)
    paginator = autoscaling_db_client.get_paginator(func_name)
    page_iterator = paginator.paginate(**kwargs)
    if search_exp:
        return page_iterator.search(search_exp)
    else:
        return page_iterator


def _describe_scalable_targets(table_name: str) -> Iterator[dict]:
    """
    Describes scalable targets
    :param table_name: The table name
    :return: The response of AWS API
    """
    return _execute_boto3_auto_scaling_paginator(func_name='describe_scalable_targets',
                                                 search_exp='ScalableTargets[]',
                                                 ServiceNamespace='dynamodb',
                                                 ResourceIds=[f'table/{table_name}'])


def _register_scalable_target(table_name: str, dimension: str,
                              min_cap: int, max_cap: int, role_arn: str) -> dict:
    """
    Describes scalable targets
    :param table_name: The table name
    :param dimension: The dimension
    :param min_cap: The minimum of scaling target
    :param max_cap: The maximum of scaling target
    :param role_arn: The autoscaling role ARN
    :return: The response of AWS API
    """
    return _execute_boto3_auto_scaling(
        delegate=lambda x: x.register_scalable_target(ServiceNamespace='dynamodb',
                                                      ScalableDimension=dimension,
                                                      MinCapacity=min_cap,
                                                      MaxCapacity=max_cap,
                                                      RoleARN=role_arn,
                                                      ResourceId=f'table/{table_name}'))


def copy_scaling_targets(events: dict, context: dict) -> dict:
    """
    Copy scaling targets settings from source table and applies to the target one
    :param events: The dictionary that supposed to have the following keys:
    * `SourceTableName` - The source table name
    * `TargetTableName` - The target table name
    :return: MapList of copied scalable targets
    """
    if 'SourceTableName' not in events:
        raise KeyError('Requires SourceTableName')
    if 'TargetTableName' not in events:
        raise KeyError('Requires SourceTableName')

    source_table_name: str = events['SourceTableName']
    target_table_name: str = events['TargetTableName']
    scaling_targets = _describe_scalable_targets(table_name=source_table_name)

    scaling_targets = \
        [{'ScalableDimension': x['ScalableDimension'],
          'MinCapacity':int(x["MinCapacity"]),
          'MaxCapacity':int(x["MaxCapacity"]),
          'RoleARN':x['RoleARN']} for x in scaling_targets]
    for x in scaling_targets:
        _register_scalable_target(table_name=target_table_name,
                                  dimension=x['ScalableDimension'],
                                  min_cap=int(x["MinCapacity"]),
                                  max_cap=int(x["MaxCapacity"]),
                                  role_arn=x['RoleARN'])

    return scaling_targets
