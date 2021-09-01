# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_memcached_swap_usage.feature',
          'Create elasticache:alarm:health-swap_usage:2020-04-01 '
          'for Memcached based on SwapUsage metric and check OK status')
def test_elasticache_memcached_swap_usage():
    pass


@scenario('../features/health_redis_swap_usage.feature',
          'Create elasticache:alarm:health-swap_usage:2020-04-01 '
          'for Redis based on SwapUsage metric and check OK status')
def test_elasticache_redis_swap_usage():
    pass
