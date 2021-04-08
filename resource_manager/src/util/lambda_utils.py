import logging
from boto3 import Session
from .boto3_client_factory import client
log = logging.getLogger()


def get_memory_size(lambda_arn: str, session: Session) -> int:
    """
    Calls AWS API to get the value of memory size parameter of given Lambda

    :param lambda_arn: The ARN of Lambda Function
    :param session: The boto3 session
    :return: The memory size in megabytes
    """
    lambda_client = client('lambda', session)
    lambda_definition = lambda_client.get_function(FunctionName=lambda_arn)
    if not lambda_definition['ResponseMetadata']['HTTPStatusCode'] == 200:
        log.error(lambda_definition)
        raise ValueError('Failed to get memory size')

    return lambda_definition['Configuration']['MemorySize']
