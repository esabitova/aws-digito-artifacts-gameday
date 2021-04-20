import logging
from boto3 import Session
from resource_manager.src.util.enums.lambda_invocation_type import LambdaInvocationType
from .boto3_client_factory import client
log = logging.getLogger()


def get_memory_size(lambda_arn: str, session: Session) -> int:
    """
    Calls AWS API to get the value of memory size parameter of given Lambda

    :param lambda_arn: The ARN of Lambda Function
    :param session The boto3 session
    :return: The memory size in megabytes
    """
    lambda_client = client('lambda', session)
    lambda_definition = lambda_client.get_function(FunctionName=lambda_arn)
    if not lambda_definition['ResponseMetadata']['HTTPStatusCode'] == 200:
        log.error(lambda_definition)
        raise ValueError('Failed to get memory size')

    return lambda_definition['Configuration']['MemorySize']


def trigger_lambda(lambda_arn: str, payload: dict,
                   invocation_type: LambdaInvocationType, session: Session) -> dict:
    """
    Calls AWS API to get the value of memory size parameter of given Lambda

    :param lambda_arn: The ARN of Lambda Function
    :param session The boto3 session
    :return: The metadata of response
    """
    lambda_client = client('lambda', session)
    invoke_result = lambda_client.invoke(FunctionName=lambda_arn,
                                         InvocationType=invocation_type.name,
                                         Payload=bytes(payload, 'utf-8'))
    status_code = int(invoke_result['ResponseMetadata']['HTTPStatusCode'])
    if not (200 <= status_code <= 300):
        log.error(invoke_result)
        raise ValueError('Failed to invoke lambda')

    payload = invoke_result['Payload'].read()
    return payload


def get_function_concurrency(lambda_arn: str, session: Session):
    """
    Calls AWS API to get the value of concurrent executions parameter of given Lambda

    :param lambda_arn: The ARN of Lambda Function
    :param session The boto3 session
    :return: The metadata of response
    """
    lambda_client = client('lambda', session)
    response = lambda_client.get_function_concurrency(
        FunctionName=lambda_arn
    )
    return response['ReservedConcurrentExecutions']


def delete_function_concurrency(lambda_arn: str, session: Session):
    """
    Calls AWS API to delete concurrency of given Lambda

    :param lambda_arn: The ARN of Lambda Function
    :param session The boto3 session
    :return: None
    """
    lambda_client = client('lambda', session)
    lambda_client.delete_function_concurrency(
        FunctionName=lambda_arn
    )
