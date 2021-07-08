# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_cpu.feature',
          'Test DocDb CPU utilization:alarm:health-cpu:2020-04-01')
def test_health_cpu():
    """Test DocDb CPU utilization:alarm:health-cpu:2020-04-01"""
    pass
