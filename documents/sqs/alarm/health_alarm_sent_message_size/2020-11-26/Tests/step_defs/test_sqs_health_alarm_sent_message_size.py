# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/sqs_health_alarm_sent_message_size.feature',
          'Check how SentMessageSize became close to allowed Threshold')
def test_alarm_red():
    pass


@scenario('../features/sqs_health_alarm_sent_message_size.feature',
          'Check how SentMessageSize not became close to allowed Threshold')
def test_alarm_green():
    pass
