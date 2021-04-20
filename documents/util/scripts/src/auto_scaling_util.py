
import json
import logging
from typing import List

import boto3


def _execute_boto3_auto_scaling(delegate):
    auto_scaling_client = boto3.client('application-autoscaling')
    description = delegate(auto_scaling_client)
    if not description['ResponseMetadata']['HTTPStatusCode'] == 200:
        logging.error(description)
        raise ValueError('Failed to execute request')
    return description


def _describe_scalable_targets(table_name: str):
    return _execute_boto3_auto_scaling(
        delegate=lambda x: x.describe_scalable_targets(ServiceNamespace='dynamodb',
                                                       ResourceIds=[f'table/{table_name}']))


def _register_scalable_target(table_name: str, dimension: str, min_cap: int, max_cap: int):
    return _execute_boto3_auto_scaling(
        delegate=lambda x: x.register_scalable_target(ServiceNamespace='dynamodb',
                                                      ScalableDimension=dimension,
                                                      MinCapacity=min_cap,
                                                      MaxCapacity=max_cap,
                                                      ResourceId=f'table/{table_name}'))


def get_scaling_targets(events: dict, context: dict) -> List:
    if 'TableName' not in events:
        raise KeyError('Requires TableName')

    table_name: str = events['TableName']
    table_result = _describe_scalable_targets(table_name=table_name)

    scaling_targets = [{"Dimension": x['ScalableDimension'], "Min":int(x["MinCapacity"]), "Max":int(x["MaxCapacity"])}
                       for x in table_result.get('ScalableTargets', [])]

    return {
        "ScalingTargets": json.dumps(scaling_targets)
    }


def register_scaling_targets(events: dict, context: dict) -> List:
    if 'TableName' not in events:
        raise KeyError('Requires TableName')
    if 'ScalingTargets' not in events:
        raise KeyError('Requires ScalingTargets')

    table_name: str = events['TableName']
    scaling_targets = json.loads(events['ScalingTargets'])
    for target in scaling_targets:
        _register_scalable_target(table_name=table_name,
                                  dimension=target['Dimension'],
                                  min_cap=target["Min"],
                                  max_cap=target["Max"])

    return get_scaling_targets(events=events,
                               context=context)
