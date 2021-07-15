# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_memory_deviation.feature',
          'Test alarm lambda:alarm:health-memory_deviation:2020-04-01')
def test_lambda_health_memory_deviation():
    """Test alarm lambda:alarm:health-memory_deviation:2020-04-01"""
    pass
