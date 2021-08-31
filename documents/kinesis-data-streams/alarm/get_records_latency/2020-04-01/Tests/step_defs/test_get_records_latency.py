# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/get_records_latency.feature',
          'Create kinesis-data-streams:alarm:get_records_latency:2020-04-01 based on GetRecords.Latency '
          'metric and check OK status')
def test_get_records_latency_ok_status():
    pass


@scenario('../features/get_records_latency.feature',
          'Create kinesis-data-streams:alarm:get_records_latency:2020-04-01 based on GetRecords.Latency '
          'metric and check ALARM status')
def test_get_records_latency_alarm_status():
    pass
