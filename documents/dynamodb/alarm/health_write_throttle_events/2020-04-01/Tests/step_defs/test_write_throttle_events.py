# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/write_throttle_events.feature',
          'Reports when write throttle events is greater than a threshold - red')
def test_write_throttle_events_alarm():
    """Reports when write throttle events is greater than a threshold - red"""
