import logging
from datetime import datetime

from pytest_bdd import (
    parsers, when, given
)

from resource_manager.src.util.common_test_utils import extract_param_value


@when(parsers.parse('send messages to the SQS queue "{times}" times'
                    '\n{input_parameters}'))
def send_messages_to_sqs_standard_queue(boto3_session, resource_manager, ssm_test_cache, times, input_parameters):
    sqs_client = boto3_session.client('sqs')
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_manager, ssm_test_cache)
    logging.info(f'Sending {times} times...')
    for i in range(int(times)):
        response: dict = sqs_client.send_message(QueueUrl=queue_url,
                                                 MessageBody=f'The message sent at {datetime.utcnow()}')
        message_id = response.get('MessageId')
        logging.info(f'Sent {i + 1} message with id = {message_id}')


@given(parsers.parse('purge the queue\n{input_parameters}'))
@when(parsers.parse('purge the queue\n{input_parameters}'))
def receive_messages_from_sqs(boto3_session, resource_manager, ssm_test_cache, input_parameters):
    sqs_client = boto3_session.client('sqs')
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_manager, ssm_test_cache)
    logging.info(f'Purging the queue with url = {queue_url}')
    sqs_client.purge_queue(QueueUrl=queue_url)
    logging.info(f'The queue was purged with url = {queue_url}')
