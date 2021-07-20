# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_throttles.feature',
          'Test alarm lambda:alarm:health-throttles:2020-04-01')
def test_lambda_throttles():
    """Test alarm lambda:alarm:health-throttles:2020-04-01"""
    pass
