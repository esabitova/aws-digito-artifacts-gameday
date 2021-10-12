# coding=utf-8
"""SSM automation document to increase Lambda memory size"""
import logging

import pytest
from pytest_bdd import (
    scenario
)

from resource_manager.src.util import lambda_utils


@scenario('../features/change_memory_size.feature',
          'Execute Digito-ChangeLambdaMemorySizeSOP_2020-10-26 to change memory size of Lambda Function')
def test_change_memory_size(teardown_lambda_memory_size):
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@pytest.fixture(scope='function')
def teardown_lambda_memory_size(boto3_session, ssm_test_cache):
    yield
    if 'before' in ssm_test_cache and 'OldMemorySize' in ssm_test_cache['before'] \
            and 'LambdaARN' in ssm_test_cache['before']:
        memory_size_to_revert = ssm_test_cache['before']['OldMemorySize']
        lambda_arn = ssm_test_cache['before']['LambdaARN']
        logging.info(f'Reverting {lambda_arn} Lambda function memory size {memory_size_to_revert}')
        lambda_client = boto3_session.client('lambda')
        lambda_client.update_function_configuration(FunctionName=lambda_arn, MemorySize=int(memory_size_to_revert))

        lambda_utils.do_wait_for_memory_changed(lambda_arn, int(memory_size_to_revert), 100, boto3_session)
        logging.info(f'{lambda_arn} Lambda function memory size was reverted to {memory_size_to_revert}')
    else:
        logging.info('Skipping reverting of Lambda function memory size')
