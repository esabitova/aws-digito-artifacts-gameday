# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_concurrent_executions.feature',
          'Test alarm lambda:alarm:health-concurrent_executions:2020-04-01')
def test_lambda_health_concurrency_executions():
    """Test alarm lambda:alarm:health-concurrent_executions:2020-04-01"""
    pass
