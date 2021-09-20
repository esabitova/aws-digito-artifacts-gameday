# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_memcached_host_level_cpu_utilization.feature',
          'Create elasticache:alarm:memcached_host_level_cpu_utilization:2020-04-01 '
          'based on CPUUtilization metric and check OK status')
def test_elasticache_memcached_cpu_utilization():
    pass
