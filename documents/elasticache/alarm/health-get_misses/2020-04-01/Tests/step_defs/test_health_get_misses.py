# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_get_misses.feature',
          'Create elasticache:alarm:health-get_misses:2020-04-01 based on GetMisses metric and check OK status')
def test_elasticache_memcached_get_misses():
    pass
