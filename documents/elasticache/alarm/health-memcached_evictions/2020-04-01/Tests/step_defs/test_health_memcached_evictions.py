# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_memcached_evictions.feature',
          'Create elasticache:alarm:health-memcached_evictions:2020-04-01 '
          'for Memcached based on Evictions metric and check OK status')
def test_elasticache_memcached_evictions():
    pass
