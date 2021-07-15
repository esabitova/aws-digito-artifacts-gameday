# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/sqs_health_alarm_threshold_approximate_number_of_messages_not_visible_standard_queue.feature',
          'Check Alarm by Digito that checks that amount of inflight messages is not reaching the quota for '
          'Standard queue - green')
def test_sqs_health_alarm_threshold_approximate_number_of_messages_not_visible_standard_queue_alarm_green():
    pass


@scenario('../features/sqs_health_alarm_threshold_approximate_number_of_messages_not_visible_standard_queue.feature',
          'Check Alarm by Digito that checks that amount of inflight messages is not reaching the quota for '
          'Standard queue - red')
def test_sqs_health_alarm_threshold_approximate_number_of_messages_not_visible_standard_queue_alarm_red():
    pass
