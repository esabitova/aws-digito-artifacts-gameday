# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_memcached_curr_connections.feature',
          'Create elasticache:alarm:health-memcached_curr_connections:2020-04-01 '
          'for Memcached based on CurrConnections metric and check OK status')
def test_elasticache_memcached_curr_connections():
    pass
