# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_millisbehindlatest_flink.feature',
          'Create kinesis:alarm:data_millis_behind_latest_records:2020-04-01 based on '
          'millisBehindLatest metric and check OK status')
def test_kin_an_flink_millisbehindlatest():
    """
    Test Kinesis Data Analytics for Apache Flink Applications
    kinesis:alarm:data_millis_behind_latest_records:2020-04-01
    """
    pass
