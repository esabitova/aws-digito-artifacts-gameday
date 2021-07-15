# coding=utf-8
from pytest_bdd import (
    scenario,
    parsers,
    when
)

from datetime import datetime

from resource_manager.src.util.common_test_utils import extract_param_value
from resource_manager.src.util import sqs_utils as sqs_utils


@scenario('../features/sqs_health_alarm_threshold_approximate_number_of_messages_not_visible_fifo.feature',
          'Check Alarm by Digito that checks that amount of inflight messages is not reaching the quota for '
          'Fifo queue - green')
def test_sqs_health_alarm_threshold_approximate_number_of_messages_not_visible_fifo_alarm_green():
    pass


@scenario('../features/sqs_health_alarm_threshold_approximate_number_of_messages_not_visible_fifo.feature',
          'Check Alarm by Digito that checks that amount of inflight messages is not reaching the quota for '
          'Fifo queue - red')
def test_sqs_health_alarm_threshold_approximate_number_of_messages_not_visible_fifo_alarm_red():
    pass


@when(parsers.parse('send "{number_of_messages}" messages with different groups to FIFO queue'
                    '\n{input_parameters}'))
def send_messages_different_groups(resource_pool, ssm_test_cache, boto3_session, number_of_messages, input_parameters):
    queue_url: str = extract_param_value(input_parameters, "QueueUrl", resource_pool, ssm_test_cache)
    for i in range(int(number_of_messages)):
        sqs_utils.send_message_to_fifo_queue(
            boto3_session, queue_url, f'This is message {i}', f'digito-test-group-{i}', datetime.now().isoformat(),
            {'test_attribute_name_1': {'StringValue': 'test_attribute_value_1', 'DataType': 'String'}}
        )
