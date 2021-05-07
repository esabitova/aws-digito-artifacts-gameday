import logging
from boto3 import Session
from resource_manager.src.util.enums.lambda_invocation_type import LambdaInvocationType
from .boto3_client_factory import client

log = logging.getLogger()


def get_lambda_state(lambda_arn, session):
    """
    Calls AWS API to obtain Lambda state

    :param lambda_arn: The ARN of Lambda Function
    :param session The boto3 session
    :return: None
    """
    lambda_client = client('lambda', session)
    function = lambda_client.get_function(FunctionName=lambda_arn)
    return function['Configuration']['State']


def create_alias(lambda_arn: str, alias_name: str, lambda_version: str, session: Session):
    """
    Calls AWS API to create a new alias for Lambda with given name

    :param lambda_arn: The ARN of Lambda Function
    :param alias_name: Alias name
    :param lambda_version: Lambda function version
    :param session The boto3 session
    :return: None
    """
    lambda_client = client('lambda', session)
    lambda_client.create_alias(
        FunctionName=lambda_arn,
        Name=alias_name,
        FunctionVersion=lambda_version
    )


def delete_alias(lambda_arn: str, alias_name: str, session: Session):
    """
    Calls AWS API to delete an alias of given Lambda by name

    :param lambda_arn: The ARN of Lambda Function
    :param alias_name: Alias name
    :param session The boto3 session
    :return: None
    """
    lambda_client = client('lambda', session)
    lambda_client.delete_alias(
        FunctionName=lambda_arn,
        Name=alias_name,
    )


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


def get_function_provisioned_concurrency(lambda_arn: str, qualifier: str, session: Session):
    """
    Calls AWS API to get the value of provisioned concurrency parameter of given Lambda
    :param lambda_arn: The ARN of Lambda Function
    :param qualifier: version number or alias name
    :param session The boto3 session
    :return: The metadata of response
    """
    lambda_client = client('lambda', session)
    response = lambda_client.get_provisioned_concurrency_config(
        FunctionName=lambda_arn,
        Qualifier=qualifier
    )
    return response.get('AllocatedProvisionedConcurrentExecutions')


def delete_function_provisioned_concurrency_config(lambda_arn: str, qualifier: str, session: Session):
    """
    Calls AWS API to delete provisioned concurrency parameter of given Lambda
    :param lambda_arn: The ARN of Lambda Function
    :param qualifier: version number or alias name
    :param session The boto3 session
    :return: The metadata of response
    """
    lambda_client = client('lambda', session)
    lambda_client.delete_provisioned_concurrency_config(
        FunctionName=lambda_arn,
        Qualifier=qualifier
    )
