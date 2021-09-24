# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/failed_queries.feature',
          'Create athena:alarm:failed_queries:2020-04-01 based on TotalExecutionTime metric '
          'and check OK status')
def test_failed_queries_alarm_green():
    """
    Test Athena QueryState alarm based on TotalExecutionTime metric with OK status:
    athena:alarm:failed_queries:2020-04-01
    """
    pass


@scenario('../features/failed_queries.feature',
          'Create athena:alarm:failed_queries:2020-04-01 based on TotalExecutionTime metric and '
          'check ALARM status')
def test_failed_queries_alarm_red():
    """
    Test Athena QueryState alarm based on TotalExecutionTime metric with ALARM status:
    athena:alarm:failed_queries:2020-04-01
    """
    pass
