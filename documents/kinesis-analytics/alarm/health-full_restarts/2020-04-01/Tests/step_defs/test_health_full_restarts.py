# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_full_restarts.feature',
          'Create kinesis:alarm:data_analytics_full_restarts:2020-04-01 '
          'based on fullRestarts metric and check OK status')
def test_kin_an_flink_full_restarts():
    """
    Test Kinesis Data Analytics for Apache Flink Applications
    kinesis:alarm:data_analytics_full_restarts:2020-04-01
    """
    pass
