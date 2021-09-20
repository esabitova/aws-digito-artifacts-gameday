# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/total_execution_time.feature',
          'Create athena:alarm:total_execution_time:2020-04-01 based on TotalExecutionTime metric and check OK status')
def test_total_execution_time():
    """
    Test Athena alarm based on TotalExecutionTime metric with OK status:
    athena:alarm:total_execution_time:2020-04-01
    """
    pass
