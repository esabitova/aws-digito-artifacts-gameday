from typing import List

import boto3

lambda_client = boto3.client('lambda')

def get_function_configuration_property(lambda_arn: str, path: str):
    response = lambda_client.get_function_configuration(FunctionName=lambda_arn)
    return __get_property(response, path)

def __get_property(response: dict, path: str) -> str:
    properties: List = path.split('.')
    result = response
    for prop in properties:
        result = result[prop]
    return str(result)
