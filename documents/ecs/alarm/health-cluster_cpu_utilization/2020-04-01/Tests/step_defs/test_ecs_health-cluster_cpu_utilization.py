# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/ecs_health-cluster_cpu_utilization.feature',
          'HighCPUClusterUtilization - green')
def test_alarm_green():
    pass


@scenario('../features/ecs_health-cluster_cpu_utilization.feature',
          'HighCPUClusterUtilization - red')
def test_alarm_red():
    pass
