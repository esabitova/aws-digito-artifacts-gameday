# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/write_throttle_events.feature',
          'Reports when write throttle events is less than a threshold')
def test_ebs_burst_balance_alarm():
    """Reports when write throttle events is less than a threshold"""
    pass
