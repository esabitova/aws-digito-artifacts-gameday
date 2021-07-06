# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/natgw_connection_attempt_count.feature',
          'Check alarm for number of connection attempts for which there was no response')
def test_alarm_green():
    pass
