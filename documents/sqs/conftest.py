from datetime import datetime

from pytest_bdd import (
    parsers, when
)

from resource_manager.src.util.common_test_utils import extract_param_value


@when(parsers.parse('send messages to the SQS queue "{times}" times\n{input_parameters}'))
def send_messages_to_sqs_standard_queue(boto3_session, resource_manager, ssm_test_cache, times, input_parameters):
    sqs_client = boto3_session.client('sqs')
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_manager, ssm_test_cache)
    sqs_client.send_message(QueueUrl=queue_url, MessageBody=f'The message sent at {datetime.utcnow()}')


@when(parsers.parse('receive "{messages_number}" messages from the SQS queue\n{input_parameters}'))
def receive_messages_from_sqs(boto3_session, resource_manager, ssm_test_cache, messages_number, input_parameters):
    sqs_client = boto3_session.client('sqs')
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_manager, ssm_test_cache)
    sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=int(messages_number))
