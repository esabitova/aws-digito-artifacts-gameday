# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/write_provisioned_throughput_exceeded.feature',
          'Create kinesis-data-streams:alarm:write_provisioned_throughput_exceeded:2020-04-01 '
          'based on WriteProvisionedThroughputExceeded '
          'metric and check OK status')
def test_write_provisioned_throughput_exceeded_ok_status():
    pass


@scenario('../features/write_provisioned_throughput_exceeded.feature',
          'Create kinesis-data-streams:alarm:write_provisioned_throughput_exceeded:2020-04-01 '
          'based on WriteProvisionedThroughputExceeded '
          'metric and check ALARM status')
def test_write_provisioned_throughput_exceeded_alarm_status():
    pass
