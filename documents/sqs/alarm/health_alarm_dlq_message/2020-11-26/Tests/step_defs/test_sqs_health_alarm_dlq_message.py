# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/sqs_health_alarm_dlq_message.feature',
          'Is there any message in DLQ - green')
def test_alarm_green():
    pass


@scenario('../features/sqs_health_alarm_dlq_message.feature',
          'Is there any message in DLQ - red')
def test_alarm_red():
    pass
