# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/recovery_kpus.feature',
          'Create kinesis:alarm:data_analytics_kpus:2020-04-01 based on '
          'KPUs metric for SQL application and check OK status')
def test_kin_an_sql_kpus():
    """
    Test Kinesis Data Analytics for SQL Applications
    kinesis:alarm:data_analytics_kpus:2020-04-01
    """
    pass


@scenario('../features/recovery_kpus.feature',
          'Create kinesis:alarm:data_analytics_kpus:2020-04-01 based on '
          'KPUs metric for Apache Flink application and check OK status')
def test_kin_an_flink_kpus():
    """
    Test Kinesis Data Analytics for Apache Flink Applications
    kinesis:alarm:data_analytics_kpus:2020-04-01
    """
    pass
