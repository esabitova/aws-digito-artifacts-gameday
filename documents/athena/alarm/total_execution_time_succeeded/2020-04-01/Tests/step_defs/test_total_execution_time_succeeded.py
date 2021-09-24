# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/total_execution_time_succeeded.feature',
          'Create athena:alarm:total_execution_time_succeeded:2020-04-01 based on TotalExecutionTime metric and check '
          'OK status')
def test_total_execution_time_succeeded_alarm_green():
    """
    Test Athena alarm based on TotalExecutionTime metric with OK status:
    athena:alarm:total_execution_time_succeeded:2020-04-01
    """
    pass


@scenario('../features/total_execution_time_succeeded.feature',
          'Create athena:alarm:total_execution_time_succeeded:2020-04-01 based on TotalExecutionTime metric and '
          'check ALARM status')
def test_total_execution_time_succeeded_alarm_red():
    """
    Test Athena alarm based on TotalExecutionTime metric with ALARM status:
    athena:alarm:total_execution_time_succeeded:2020-04-01
    """
    pass
