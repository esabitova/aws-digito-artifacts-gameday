# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_errors.feature',
          'Test alarm lambda:alarm:health-errors:2020-04-01')
def test_lambda_errors():
    """Test alarm lambda:alarm:health-errors:2020-04-01"""
    pass
