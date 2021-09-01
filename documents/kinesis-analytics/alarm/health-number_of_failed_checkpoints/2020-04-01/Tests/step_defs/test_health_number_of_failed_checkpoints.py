# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_number_of_failed_checkpoints.feature',
          'Create kinesis:alarm:data_analytics_number_of_failed_checkpoints:2020-04-01 based on '
          'numberOfFailedCheckpoints metric and check OK status')
def test_kin_an_flink_failed_checkpoints():
    """
    Test Kinesis Data Analytics for Apache Flink Applications
    kinesis:alarm:data_analytics_number_of_failed_checkpoints:2020-04-01
    """
    pass
