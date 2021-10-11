# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/dynamodb_health-successful_request_latency_transact_write_items.feature',
          'Create dynamodb:alarm:health-successful_request_latency_transact_write_items:2020-04-01 '
          'based on SuccessfulRequestLatency and check OK status')
def test_alarm_green():
    pass


@scenario('../features/dynamodb_health-successful_request_latency_transact_write_items.feature',
          'Create dynamodb:alarm:health-successful_request_latency_transact_write_items:2020-04-01 '
          'based on SuccessfulRequestLatency and check ALARM status')
def test_alarm_red():
    pass
