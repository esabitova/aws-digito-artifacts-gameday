# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/write_throttle_events_green.feature',
          'Alarm is not triggered when write throttle events is less than a threshold - green')
def test_write_throttle_events_alarm_green():
    """Alarm is not triggered when write throttle events is less than a threshold - green"""
