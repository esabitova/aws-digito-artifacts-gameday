# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_invocations.feature',
          'Test alarm lambda:alarm:health-invocations:2020-04-01')
def test_lambda_invocations():
    """Test alarm lambda:alarm:health-invocations:2020-04-01"""
    pass
