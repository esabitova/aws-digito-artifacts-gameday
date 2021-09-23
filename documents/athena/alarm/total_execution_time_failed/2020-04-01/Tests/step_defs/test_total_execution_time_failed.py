# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/total_execution_time_failed.feature',
          'Create athena:alarm:total_execution_time_failed:2020-04-01 based on TotalExecutionTime metric '
          'and check OK status')
def test_total_execution_time_failed_alarm_green():
    """
    Test Athena QueryState alarm based on TotalExecutionTime metric with OK status:
    athena:alarm:total_execution_time_failed:2020-04-01
    """
    pass


@scenario('../features/total_execution_time_failed.feature',
          'Create athena:alarm:total_execution_time_failed:2020-04-01 based on TotalExecutionTime metric and '
          'check ALARM status')
def test_total_execution_time_failed_alarm_red():
    """
    Test Athena QueryState alarm based on TotalExecutionTime metric with ALARM status:
    athena:alarm:total_execution_time_failed:2020-04-01
    """
    pass
