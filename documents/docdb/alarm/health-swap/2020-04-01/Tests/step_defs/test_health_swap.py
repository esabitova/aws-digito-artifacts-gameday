# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_swap.feature',
          'Test DocDb swap space:alarm:health-swap:2020-04-01')
def test_health_cpu():
    """Test DocDb swap space:alarm:health-swap:2020-04-01"""
    pass
