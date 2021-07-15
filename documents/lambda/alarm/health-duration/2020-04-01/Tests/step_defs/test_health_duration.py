# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_duration.feature',
          'Test alarm lambda:alarm:health-duration:2020-04-01')
def test_lambda_health_duration():
    """Test alarm lambda:alarm:health-duration:2020-04-01"""
    pass
