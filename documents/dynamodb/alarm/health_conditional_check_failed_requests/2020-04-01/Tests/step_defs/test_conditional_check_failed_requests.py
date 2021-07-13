# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/conditional_check_failed_requests.feature',
          'Alarm is not triggered when amount of conditional check failed requests is less than threshold - green')
def test_condition_check_failed_requests_alarm_green():
    """Alarm is not triggered when amount of conditional check failed requests is less than threshold - green"""


@scenario('../features/conditional_check_failed_requests.feature',
          'Reports when amount of conditional check failed requests is greater than or equal to threshold - red')
def test_condition_check_failed_requests_alarm_red():
    """Reports when amount of conditional check failed requests is greater than or equal to threshold - red"""
