import logging
from datetime import datetime
from pytest_bdd import (
    given,
    parsers, when
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
        sqs_utils.send_message_to_standard_queue(boto3_session, queue_url, f'This is message {i}',
                                                 {'test_attribute_name_1': {'StringValue': 'test_attribute_value_1',
                                                                            'DataType': 'String'}
                                                  })


@given(parsers.parse('send "{number_of_messages}" messages to FIFO queue\n{input_parameters}'))
def send_messages_to_fifo(resource_manager, ssm_test_cache, boto3_session, number_of_messages, input_parameters):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_manager, ssm_test_cache)
    for i in range(int(number_of_messages)):
        sqs_utils.send_message_to_fifo_queue(
            boto3_session, queue_url, f'This is message {i}', 'digito-test-group', datetime.now().isoformat()
        )


cache_number_of_messages_expression = 'cache number of messages in queue as "{cache_property}" "{step_key}" SSM ' \
                                      'automation execution' \
                                      '\n{input_parameters}'


@given(parsers.parse(cache_number_of_messages_expression))
@when(parsers.parse(cache_number_of_messages_expression))
def cache_number_of_messages(
        resource_manager, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_manager, ssm_test_cache)
    number_of_messages: int = sqs_utils.get_number_of_messages(boto3_session, queue_url)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, number_of_messages)
