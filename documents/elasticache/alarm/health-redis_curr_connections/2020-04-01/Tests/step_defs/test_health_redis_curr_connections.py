# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_redis_curr_connections.feature',
          'Create elasticache:alarm:health-redis_curr_connections:2020-04-01 '
          'for Redis based on CurrConnections metric and check OK status')
def test_elasticache_redis_curr_connections():
    pass
