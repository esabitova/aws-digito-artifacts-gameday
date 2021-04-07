import logging
from datetime import datetime
from botocore.exceptions import ClientError

from pytest_bdd import (
    given,
    parsers, when, then
)

from resource_manager.src.util import sqs_utils as sqs_utils
from resource_manager.src.util.common_test_utils import extract_param_value
from resource_manager.src.util.common_test_utils import put_to_ssm_test_cache


@given(parsers.parse('purge the queue\n{input_parameters}'))
@when(parsers.parse('purge the queue\n{input_parameters}'))
def purge_the_queue(boto3_session, resource_manager, ssm_test_cache, input_parameters):
    sqs_client = boto3_session.client('sqs')
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_manager, ssm_test_cache)
    logging.info(f'Purging the queue with url = {queue_url}')
    sqs_client.purge_queue(QueueUrl=queue_url)
    logging.info(f'The queue was purged with url = {queue_url}')


@given(parsers.parse('send "{number_of_messages}" messages to queue\n{input_parameters}'))
@when(parsers.parse('send "{number_of_messages}" messages to queue\n{input_parameters}'))
def send_messages(resource_manager, ssm_test_cache, boto3_session, number_of_messages, input_parameters):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_manager, ssm_test_cache)
    for i in range(int(number_of_messages)):
        sqs_utils.send_message_to_standard_queue(
            boto3_session, queue_url, f'This is message {i}',
            {'test_attribute_name_1': {'StringValue': 'test_attribute_value_1', 'DataType': 'String'}}
        )


@given(parsers.parse('send "{number_of_messages}" messages to FIFO queue\n{input_parameters}'))
@when(parsers.parse('send "{number_of_messages}" messages to FIFO queue\n{input_parameters}'))
def send_messages_to_fifo(resource_manager, ssm_test_cache, boto3_session, number_of_messages, input_parameters):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_manager, ssm_test_cache)
    for i in range(int(number_of_messages)):
        sqs_utils.send_message_to_fifo_queue(
            boto3_session, queue_url, f'This is message {i}', 'digito-test-group', datetime.now().isoformat(),
            {'test_attribute_name_1': {'StringValue': 'test_attribute_value_1', 'DataType': 'String'}}
        )


@given(parsers.parse('send "{number_of_messages}" messages to queue with error\n{input_parameters}'))
@when(parsers.parse('send "{number_of_messages}" messages to queue with error\n{input_parameters}'))
def send_messages_with_error(resource_manager, ssm_test_cache, boto3_session, number_of_messages,
                             input_parameters):
    """
    This method expects that message should fail due to AccessDenied
    Any other error should be raised and message should not be sent
    """
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_manager, ssm_test_cache)
    for i in range(int(number_of_messages)):
        try:
            sqs_utils.send_message_to_standard_queue(
                boto3_session, queue_url, f'This is message {i}',
                {'test_attribute_name_1': {'StringValue': 'test_attribute_value_1', 'DataType': 'String'}}
            )
            raise Exception('Message was sent successfully but error was expected')
        except ClientError as error:
            if error.response['Error']['Code'] == 'AccessDenied':
                logging.info('Message sending failed due to access denied')
            else:
                raise error


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
        resource_manager, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_manager, ssm_test_cache)
    number_of_messages: int = sqs_utils.get_number_of_messages(boto3_session, queue_url)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, number_of_messages)


@given(parsers.parse('cache policy as "{cache_property}" "{step_key}" SSM automation execution\n{input_parameters}'))
@when(parsers.parse('cache policy as "{cache_property}" "{step_key}" SSM automation execution\n{input_parameters}'))
def cache_policy(resource_manager, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_manager, ssm_test_cache)
    policy = sqs_utils.get_policy(boto3_session, queue_url)
    logging.debug(f'Queue policy is {policy}')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, policy)


@given(parsers.parse('cache visibility timeout as "{cache_property}" "{step_key}" SSM automation execution'
                     '\n{input_parameters}'))
@when(parsers.parse('cache visibility timeout as "{cache_property}" "{step_key}" SSM automation execution'
                    '\n{input_parameters}'))
def cache_visibility_timeout(
        resource_manager, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_manager, ssm_test_cache)
    visibility_timeout = sqs_utils.get_queue_attribute(boto3_session, queue_url, 'VisibilityTimeout')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, visibility_timeout)


@given(parsers.parse('cache redrive policy as "{cache_property}" "{step_key}" SSM automation execution'
                     '\n{input_parameters}'))
@when(parsers.parse('cache redrive policy as "{cache_property}" "{step_key}" SSM automation execution'
                    '\n{input_parameters}'))
def cache_redrive_policy(resource_manager, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_manager, ssm_test_cache)
    redrive_policy = sqs_utils.get_queue_attribute(boto3_session, queue_url, 'RedrivePolicy')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, redrive_policy)
