# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/natgw_idle_timeout_count.feature',
          'Check alarm for number of connections that transitioned from the active state to the idle state')
def test_alarm_green():
    pass
