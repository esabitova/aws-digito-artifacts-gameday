# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_downtime.feature',
          'Create kinesis:alarm:data_analytics_downtime:2020-04-01 based on downtime metric and check OK status')
def test_kin_an_flink_downtime():
    """
    Test Kinesis Data Analytics for Apache Flink Applications
    kinesis:alarm:data_analytics_downtime:2020-04-01
    """
    pass
