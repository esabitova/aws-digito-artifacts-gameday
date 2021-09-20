# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_redis_evictions.feature',
          'Create elasticache:alarm:health-redis_evictions:2020-04-01 '
          'for Redis based on Evictions metric and check OK status')
def test_elasticache_redis_evictions():
    pass
