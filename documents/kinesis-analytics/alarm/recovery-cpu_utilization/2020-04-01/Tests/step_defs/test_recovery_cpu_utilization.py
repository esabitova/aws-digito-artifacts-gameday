# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/recovery_cpu_utilization.feature',
          'Create kinesis:alarm:data_analytics_cpu_utilization:2020-04-01 based on '
          'cpuUtilization metric and check OK status')
def test_kin_an_flink_cpu_utilization():
    """
    Test Kinesis Data Analytics for Apache Flink Applications
    kinesis:alarm:data_analytics_cpu_utilization:2020-04-01
    """
    pass
