# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/read_throttle_events.feature',
          'Reports when read throttle events is greater than a threshold - red')
def test_read_throttle_events_alarm():
    """Reports when read throttle events is greater than a threshold - red"""
