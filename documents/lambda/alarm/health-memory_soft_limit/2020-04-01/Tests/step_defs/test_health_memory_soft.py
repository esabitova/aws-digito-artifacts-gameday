# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_memory_soft.feature',
          'Test alarm lambda:alarm:health-memory_soft_limit:2020-04-01')
def test_lambda_health_memory_soft():
    """Test alarm lambda:alarm:health-memory_soft_limit:2020-04-01"""
    pass
