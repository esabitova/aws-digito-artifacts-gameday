# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_redis_engine_cpu_utilization_1vcpu.feature',
          'Create elasticache:alarm:health-redis_engine_cpu_utilization:2020-04-01 with 1 vCPU '
          'based on EngineCPUUtilization metric and check OK status')
def test_elasticache_redis_engine_cpu_utilization_1vcpu():
    pass


@scenario('../features/health_redis_engine_cpu_utilization_4vcpu.feature',
          'Create elasticache:alarm:health-redis_engine_cpu_utilization:2020-04-01 with 4 vCPU '
          'based on EngineCPUUtilization metric and check OK status')
def test_elasticache_redis_engine_cpu_utilization_4vcpu():
    pass
