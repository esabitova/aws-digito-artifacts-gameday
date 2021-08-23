# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/ecs_health-service_cpu_utilization.feature',
          'HighCPUServiceUtilization - green')
def test_alarm_green():
    pass


@scenario('../features/ecs_health-service_cpu_utilization.feature',
          'HighCPUServiceUtilization - red')
def test_alarm_red():
    pass
