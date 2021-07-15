# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/sqs_health_alarm_approximate_age_of_oldest_message_maximum.feature',
          'Check age of the oldest message - green')
def test_sqs_health_alarm_approximate_age_of_oldest_message_maximum_alarm_green():
    pass


@scenario('../features/sqs_health_alarm_approximate_age_of_oldest_message_maximum.feature',
          'Check age of the oldest message - red')
def test_sqs_health_alarm_approximate_age_of_oldest_message_maximum_alarm_red():
    pass
