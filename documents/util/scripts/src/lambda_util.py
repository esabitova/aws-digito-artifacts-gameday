import time
from datetime import datetime

import boto3
import logging

from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CONCURRENT_EXECUTION_QUOTA_CODE = 'L-B99A9384'
MINIMUM_UNRESERVED_CONCURRENCY = 100


def check_required_params(required_params, events):
    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')


def get_concurrent_execution_quota(events, context):
    try:
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        quotas_client = boto3.client('service-quotas', config=config)
        paginator = quotas_client.get_paginator('list_service_quotas')
        pages = paginator.paginate(ServiceCode='lambda')
        concurrent_execution_quota = None
        for page in pages:
            quotas = page.get('Quotas')
            for quota in quotas:
                quota_code = quota.get('QuotaCode')
                if quota_code == CONCURRENT_EXECUTION_QUOTA_CODE:
                    concurrent_execution_quota = quota.get('Value')
                    break
        if not concurrent_execution_quota:
            default_quota_info = quotas_client.get_aws_default_service_quota(
                ServiceCode='lambda',
                QuotaCode=CONCURRENT_EXECUTION_QUOTA_CODE
            )
            concurrent_execution_quota = default_quota_info.get('Quota').get('Value')
        return {'ConcurrentExecutionsQuota': int(concurrent_execution_quota)}
    except Exception as e:
        logger.error(f'Loading ConcurrentExecutionsQuota for Lambda failed with error: {e}')
        raise


def calculate_total_reserved_concurrency(events, context):
    try:
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        lambda_client = boto3.client('lambda', config=config)
        lambda_arn = events.get('LambdaARN')
        paginator = lambda_client.get_paginator('list_functions')
        pages = paginator.paginate()
        total_reserved_concurrency = 0
        for page in pages:
            functions = page.get('Functions')
            for lambda_function in functions:
                function_name: str = lambda_function.get('FunctionName')
                function_arn: str = lambda_function.get('FunctionArn')
                if lambda_arn != function_arn:
                    function_concurrency_info = lambda_client.get_function_concurrency(
                        FunctionName=function_name
                    )
                    function_concurrency = function_concurrency_info.get('ReservedConcurrentExecutions', 0)
                    total_reserved_concurrency += function_concurrency
        return {'TotalReservedConcurrency': total_reserved_concurrency}
    except Exception as e:
        logger.error(f'Calculating total reserved concurrency for all Lambda functions failed with error: {e}')
        raise


def check_feasibility(events: dict, context):
    try:
        concurrent_executions_quota = events.get('ConcurrentExecutionsQuota')
        total_reserved_concurrency = events.get('TotalReservedConcurrency')
        new_reserved_concurrent_executions = events.get('NewReservedConcurrentExecutions')
        maximum_possible_reserved_concurrency = (concurrent_executions_quota
                                                 - total_reserved_concurrency
                                                 - new_reserved_concurrent_executions
                                                 - MINIMUM_UNRESERVED_CONCURRENCY)
        can_set_reserved_concurrency = maximum_possible_reserved_concurrency > 0
        if not can_set_reserved_concurrency:
            raise Exception(
                f'You can reserve up to the Unreserved account concurrency value that is shown, minus 100 for functions'
                f' that don\'t have reserved concurrency. There is only {maximum_possible_reserved_concurrency}'
                f'concurrent executions left')
        return {
            'CanSetReservedConcurrency': can_set_reserved_concurrency,
            'MaximumPossibleReservedConcurrency': maximum_possible_reserved_concurrency
        }
    except Exception as e:
        logger.error(f'Checking feasibility failed with error: {e}')
        raise


def set_reserved_concurrent_executions(events: dict, context):
    try:
        lambda_arn = events.get('LambdaARN')
        new_reserved_concurrent_executions = events.get('NewReservedConcurrentExecutions')
        maximum_possible_reserved_concurrency = events.get('MaximumPossibleReservedConcurrency')
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        lambda_client = boto3.client('lambda', config=config)
        lambda_client.put_function_concurrency(
            FunctionName=lambda_arn,
            ReservedConcurrentExecutions=new_reserved_concurrent_executions
        )
        reserved_concurrency_left = maximum_possible_reserved_concurrency - new_reserved_concurrent_executions
        return {
            'ReservedConcurrencyLeft': reserved_concurrency_left,
            'NewReservedConcurrencyValue': new_reserved_concurrent_executions
        }
    except Exception as e:
        logger.error(f'Setting new value for reserved concurrent executions failed with error: {e}')
        raise


def backup_reserved_concurrent_executions(events: dict, context):
    lambda_arn = events.get('LambdaARN')
    if not lambda_arn:
        raise KeyError('Requires LambdaARN in events')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    lambda_client = boto3.client('lambda', config=config)
    response = lambda_client.get_function_concurrency(
        FunctionName=lambda_arn
    )
    reserved_concurrent_executions_configured = False
    concurrent_executions_value = 0
    if response:
        reserved_concurrent_executions_configured = True
        concurrent_executions_value = response.get('ReservedConcurrentExecutions')
    return {
        'ReservedConcurrentExecutionsConfigured': reserved_concurrent_executions_configured,
        'BackupReservedConcurrentExecutionsValue': concurrent_executions_value
    }


def remove_sg_assignment(events: dict, context):
    required_params = [
        'LambdaARN',
        'EmptySecurityGroupId',
        'SecurityGroupId',
        'ExecutionId'
    ]
    check_required_params(required_params, events)
    lambda_client = boto3.client('lambda')
    lambda_description = lambda_client.get_function(
        FunctionName=events['LambdaARN']
    )
    security_group_list = lambda_description['Configuration']['VpcConfig']['SecurityGroupIds']
    subnet_ids = lambda_description['Configuration']['VpcConfig']['SubnetIds']

    logger.info(f'Emptying Security groups for lambda:{events["LambdaARN"]}')

    if events['SecurityGroupId']:
        if events['SecurityGroupId'] not in security_group_list:
            raise KeyError(f"Security group {events['SecurityGroupId']} is not in security group list of Lambda: "
                           f"{security_group_list}")
        security_group_list.remove(events['SecurityGroupId'])
    else:
        security_group_list = []
    security_group_list.append(events['EmptySecurityGroupId'])

    lambda_client.update_function_configuration(
        FunctionName=events['LambdaARN'],
        VpcConfig={
            'SecurityGroupIds': security_group_list,
            'SubnetIds': subnet_ids
        }
    )
    return {'SecurityGroupListUpdatedValue': security_group_list}


def rollback_security_groups(events: dict, context):
    required_params = [
        'LambdaARN',
        'SecurityGroupList',
        'ExecutionId'
    ]
    check_required_params(required_params, events)
    lambda_client = boto3.client('lambda')
    lambda_description = lambda_client.get_function(
        FunctionName=events['LambdaARN']
    )

    subnet_ids = lambda_description['Configuration']['VpcConfig']['SubnetIds']

    time_to_wait = 900
    if 'Timeout' in events:
        time_to_wait = events['Timeout']
    timeout_timestamp = datetime.timestamp(datetime.now()) + int(time_to_wait)
    while datetime.timestamp(datetime.now()) < timeout_timestamp:
        try:
            response = lambda_client.update_function_configuration(
                FunctionName=events['LambdaARN'],
                VpcConfig={
                    'SecurityGroupIds': events['SecurityGroupList'],
                    'SubnetIds': subnet_ids
                }
            )
            if response['ResponseMetadata']['HTTPStatusCode'] < 400:
                break
        except ClientError as error:
            if error.response['Error']['Code'] == 'ResourceConflictException':
                logger.info(f'Function {events["LambdaARN"]} is still updating, waiting...')
            time.sleep(5)
    return {'SecurityGroupListRestoredValue': events['SecurityGroupList']}


def assert_lambda_in_vpc_and_backup_sg(events: dict, context):
    required_params = [
        'LambdaARN'
    ]
    check_required_params(required_params, events)

    lambda_client = boto3.client('lambda')
    lambda_description = lambda_client.get_function(
        FunctionName=events['LambdaARN']
    )
    result = {}
    if 'VpcId' in lambda_description['Configuration']['VpcConfig']:
        result['VpcId'] = lambda_description['Configuration']['VpcConfig']['VpcId']
        result['SecurityGroupIds'] = lambda_description['Configuration']['VpcConfig']['SecurityGroupIds']
    else:
        raise AssertionError(f'Lambda function:{events["LambdaARN"]} is not a member of any VPC')

    return result
