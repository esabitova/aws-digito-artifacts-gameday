import logging
import time
from botocore.exceptions import ClientError

from datetime import datetime, timedelta
from boto3 import Session
from concurrent.futures.thread import ThreadPoolExecutor

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


def get_alias_version(lambda_arn: str, alias_name: str, session: Session):
    """
    Calls AWS API to get function version in alias info for Lambda with given name

    :param lambda_arn: The ARN of Lambda Function
    :param alias_name: Alias name
    :param session The boto3 session
    :return: Function version in alias
    """
    lambda_client = client('lambda', session)
    response = lambda_client.get_alias(
        FunctionName=lambda_arn,
        Name=alias_name,
    )
    return response.get('FunctionVersion')


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
                   invocation_type: LambdaInvocationType, session: Session, log_type: str = 'None') -> dict:
    """
    Calls AWS API to get the value of memory size parameter of given Lambda

    :param lambda_arn: The ARN of Lambda Function
    :param session The boto3 session
    :return: The metadata of response
    """
    lambda_client = client('lambda', session)
    invoke_result = lambda_client.invoke(FunctionName=lambda_arn,
                                         InvocationType=invocation_type.name,
                                         LogType=log_type,
                                         Payload=bytes(payload, 'utf-8'))
    status_code = int(invoke_result['ResponseMetadata']['HTTPStatusCode'])
    if not (200 <= status_code <= 300):
        log.error(invoke_result)
        raise ValueError('Failed to invoke lambda')

    invoke_result['Payload'] = invoke_result['Payload'].read()
    return invoke_result


def trigger_throttled_lambda(lambda_arn: str, session: Session):
    lambda_client = client('lambda', session)
    try:
        lambda_client.invoke(
            FunctionName=lambda_arn
        )
    except Exception as e:
        if e.response['ResponseMetadata']['HTTPStatusCode'] != 429:
            raise Exception('Wrong StatusCode in response for throttled function invocation')
    return True


def trigger_ordinary_lambda(lambda_arn: str, session: Session, invocation_time='RequestResponse'):
    """
    invokes lambda for alarm fata population
    """
    lambda_client = client('lambda', session)
    try:
        lambda_client.invoke(
            FunctionName=lambda_arn,
            InvocationType=invocation_time
        )
    except ClientError as ee:
        raise ee(f"Lambda Function not invoked, StatusCode: {ee.response['ResponseMetadata']['HTTPStatusCode']}")
    return True


def trigger_ordinary_lambda_several_times(lambda_arn: str, session: Session, trigger_attempts: int):
    """
    invokes lambda for alarm fata population several times:
    param:trigger_attempts - attempts to trigger lambda, default = 3
    """
    lambda_client = client('lambda', session)
    i = 0
    while i < trigger_attempts:
        try:
            lambda_client.invoke(
                FunctionName=lambda_arn
            )
            i += 1
        except ClientError as ee:
            raise ee(f"Lambda Function not invoked, StatusCode:\
                            {ee.response['ResponseMetadata']['HTTPStatusCode']}")
    return True


def trigger_lambda_under_stress(lambda_arn: str, boto3_session: Session, overall_stress_time: int,
                                number_in_each_chunk: int, delay_among_chunks: int):
    """
    stress lambda - invokes lambda many times, chunk by chunk, waits among chunks
    and invokes again, till stress time pass:
    param:overall_stress_time - overall time (seconds) from stress initiate still completion
    param:number_in_each_chunk - number of lambda invokes in each stress chunk
    param:delay_among_chunks - delay seconds among chunks
    """
    futures = []
    logging.info(f'Start Lambda stress invokes, stress time {str(overall_stress_time)} seconds')
    start_stress = datetime.utcnow()
    end_stress = start_stress + timedelta(seconds=overall_stress_time)
    overall_exec = 0
    with ThreadPoolExecutor() as executor:
        while datetime.utcnow() < end_stress:
            for i in range(number_in_each_chunk):
                futures.append(
                    executor.submit(trigger_ordinary_lambda, lambda_arn, boto3_session,
                                    invocation_time='Event')
                )
                overall_exec += 1
            time.sleep(delay_among_chunks)
    logging.info('Lambda invoke stress test done')
    return overall_exec


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


def publish_version(lambda_arn: str, session: Session):
    """
    Calls AWS API to create a version from the current code and configuration of a function
    :param lambda_arn: The ARN of Lambda Function
    :param session The boto3 session
    :return: The metadata of response
    """
    lambda_client = client('lambda', session)
    response = lambda_client.publish_version(
        FunctionName=lambda_arn,
    )
    return response


def delete_function_version(lambda_arn: str, version: str, session: Session):
    """
    Calls AWS API to delete function version
    :param lambda_arn: The ARN of Lambda Function
    :param version: The function version
    :param session The boto3 session
    :return: None
    """
    lambda_client = client('lambda', session)
    lambda_client.delete_function(
        FunctionName=lambda_arn,
        Qualifier=version
    )


def get_function_execution_time_limit(lambda_arn: str, session: Session):
    """
    Calls AWS API to get function execution time limit
    :param lambda_arn: The ARN of Lambda Function
    :param session The boto3 session
    :return: None
    """
    lambda_client = client('lambda', session)
    function_configuration = lambda_client.get_function_configuration(FunctionName=lambda_arn)
    return function_configuration.get('Timeout')
