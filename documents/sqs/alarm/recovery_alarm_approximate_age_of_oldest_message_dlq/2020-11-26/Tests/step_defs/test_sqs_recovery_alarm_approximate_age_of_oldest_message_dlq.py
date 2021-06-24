# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/sqs_recovery_alarm_approximate_age_of_oldest_message_dlq.feature',
          'Check age of the oldest message in DLQ - green')
def test_alarm_green():
    pass


@scenario('../features/sqs_recovery_alarm_approximate_age_of_oldest_message_dlq.feature',
          'Check age of the oldest message in DLQ - red')
def test_alarm_red():
    pass
