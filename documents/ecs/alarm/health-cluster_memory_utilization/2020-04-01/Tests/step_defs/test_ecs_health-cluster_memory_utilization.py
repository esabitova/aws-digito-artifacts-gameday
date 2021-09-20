# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/ecs_health-cluster_memory_utilization.feature',
          'HighMemoryUtilization - green')
def test_alarm_green():
    pass


@scenario('../features/ecs_health-cluster_memory_utilization.feature',
          'HighMemoryUtilization - red')
def test_alarm_red():
    pass
