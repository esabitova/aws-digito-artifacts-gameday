# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/sqs_health_alarm_number_of_messages_sent_band.feature',
          'To detect anomalies of high and low values of NumberOfMessagesSent')
def test_alarm():
    pass
