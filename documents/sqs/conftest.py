import logging
import time
from datetime import datetime

import pytest
from pytest_bdd import (
    given,
    parsers, when, then
)

from resource_manager.src.util import sqs_utils as sqs_utils
from resource_manager.src.util.common_test_utils import extract_param_value
from resource_manager.src.util.common_test_utils import put_to_ssm_test_cache


@given(parsers.parse('purge the queue\n{input_parameters}'))
@when(parsers.parse('purge the queue\n{input_parameters}'))
def purge_the_queue(boto3_session, resource_pool, ssm_test_cache, input_parameters):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_pool, ssm_test_cache)
    sqs_utils.purge_queue(boto3_session, queue_url)


@given(parsers.parse('send "{number_of_messages}" messages to queue\n{input_parameters}'))
@when(parsers.parse('send "{number_of_messages}" messages to queue\n{input_parameters}'))
def send_messages(resource_pool, ssm_test_cache, boto3_session, number_of_messages, input_parameters):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_pool, ssm_test_cache)
    for i in range(int(number_of_messages)):
        sqs_utils.send_message_to_standard_queue(
            boto3_session, queue_url, f'This is message {i}',
            {'test_attribute_name_1': {'StringValue': 'test_attribute_value_1', 'DataType': 'String'}}
        )


@given(parsers.parse('receive "{number_of_messages}" messages from queue\n{input_parameters}'))
@when(parsers.parse('receive "{number_of_messages}" messages from queue\n{input_parameters}'))
def receive_messages(resource_pool, ssm_test_cache, boto3_session, number_of_messages, input_parameters):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_pool, ssm_test_cache)
    try:
        visibility_timeout = int(
            extract_param_value(input_parameters, "VisibilityTimeout", resource_pool, ssm_test_cache)
        )
    except KeyError:
        visibility_timeout = None
    except ValueError:
        raise ValueError(f'parameter "VisibilityTimeout" must be an integer, got '
                         f'{extract_param_value(input_parameters, "VisibilityTimeout", resource_pool, ssm_test_cache)}')
    sqs_client = boto3_session.client('sqs')
    for i in range(int(number_of_messages)):
        if visibility_timeout:
            msg = sqs_client.receive_message(
                QueueUrl=queue_url,
                VisibilityTimeout=visibility_timeout,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=3,
                MessageAttributeNames=['All'],
                AttributeNames=['All']
            )
        else:
            msg = sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=3,
                MessageAttributeNames=['All'],
                AttributeNames=['All']
            )
        logging.info(f"Got message: {msg['Messages'][0]['Body']}")


@given(parsers.parse('send "{number_of_messages}" messages to FIFO queue\n{input_parameters}'))
@when(parsers.parse('send "{number_of_messages}" messages to FIFO queue\n{input_parameters}'))
def send_messages_to_fifo(resource_pool, ssm_test_cache, boto3_session, number_of_messages, input_parameters):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_pool, ssm_test_cache)
    for i in range(int(number_of_messages)):
        sqs_utils.send_message_to_fifo_queue(
            boto3_session, queue_url, f'This is message {i}', 'digito-test-group', datetime.now().isoformat(),
            {'test_attribute_name_1': {'StringValue': 'test_attribute_value_1', 'DataType': 'String'}}
        )


@given(parsers.parse('send messages for "{time_to_wait}" seconds until access denied\n{input_parameters}'))
def send_messages_until_access_denied(resource_pool, ssm_test_cache, boto3_session, time_to_wait, input_parameters):
    """
    Keep sending messages to queue and expect to get access denied error before timeout
    """
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_pool, ssm_test_cache)
    sqs_utils.send_messages_until_access_denied(boto3_session, queue_url, time_to_wait)


@when(parsers.parse('send messages for "{time_to_wait}" seconds ignoring access denied until "{number_of_messages}" '
                    'sent successfully\n{input_parameters}'))
def send_messages_until_success_ignore_access_denied(
        resource_pool, ssm_test_cache, boto3_session, time_to_wait, number_of_messages, input_parameters
):
    """
    Keep sending messages to queue and ignore access denied error until min number is sent
    """
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_pool, ssm_test_cache)
    sqs_utils.send_messages_until_success(boto3_session, queue_url, time_to_wait, number_of_messages)


@given(parsers.parse('cache number of messages in queue as "{cache_property}" "{step_key}" SSM '
                     'automation execution'
                     '\n{input_parameters}'))
@when(parsers.parse('cache number of messages in queue as "{cache_property}" "{step_key}" SSM '
                    'automation execution'
                    '\n{input_parameters}'))
@then(parsers.parse('cache number of messages in queue as "{cache_property}" "{step_key}" SSM '
                    'automation execution'
                    '\n{input_parameters}'))
def cache_number_of_messages(
        resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_pool, ssm_test_cache)
    number_of_messages: int = sqs_utils.get_number_of_messages(boto3_session, queue_url)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, number_of_messages)


@given(parsers.parse('cache policy as "{cache_property}" "{step_key}" SSM automation execution\n{input_parameters}'))
@when(parsers.parse('cache policy as "{cache_property}" "{step_key}" SSM automation execution\n{input_parameters}'))
@then(parsers.parse('cache policy as "{cache_property}" "{step_key}" SSM automation execution\n{input_parameters}'))
def cache_policy(resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_pool, ssm_test_cache)
    policy = sqs_utils.get_policy(boto3_session, queue_url)
    logging.debug(f'Queue policy is {policy}')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, policy)


@given(parsers.parse('cache visibility timeout as "{cache_property}" "{step_key}" SSM automation execution'
                     '\n{input_parameters}'))
@when(parsers.parse('cache visibility timeout as "{cache_property}" "{step_key}" SSM automation execution'
                    '\n{input_parameters}'))
def cache_visibility_timeout(
        resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_pool, ssm_test_cache)
    visibility_timeout = sqs_utils.get_queue_attribute(boto3_session, queue_url, 'VisibilityTimeout')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, visibility_timeout)


@given(parsers.parse('cache redrive policy as "{cache_property}" "{step_key}" SSM automation execution'
                     '\n{input_parameters}'))
@when(parsers.parse('cache redrive policy as "{cache_property}" "{step_key}" SSM automation execution'
                    '\n{input_parameters}'))
def cache_redrive_policy(resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_pool, ssm_test_cache)
    redrive_policy = sqs_utils.get_queue_attribute(boto3_session, queue_url, 'RedrivePolicy')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, redrive_policy)


@pytest.fixture(scope='function')
def queue_for_teardown(boto3_session, ssm_test_cache):
    yield
    queue_url = ssm_test_cache['before']['QueueUrl']
    sqs_client = boto3_session.client('sqs')
    logging.info('Purging the queue for teardown')
    sqs_client.purge_queue(QueueUrl=queue_url)
    logging.info('Sleeping for 60 secs after queue purge for teardown')
    time.sleep(60)


@given(parsers.parse('cache queue url as "{cache_property}" "{step_key}" SSM automation execution for teardown'
                     '\n{input_parameters}'))
def cache_queue_url(
    resource_pool, ssm_test_cache, queue_for_teardown, cache_property, step_key, input_parameters
):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_pool, ssm_test_cache)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, queue_url)
