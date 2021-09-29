# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_authentication_failures.feature',
          'Create elasticache:alarm:health-authentication_failures:2020-04-01 '
          'based on AuthenticationFailures metric and check OK status')
def test_elasticache_redis_authentication_failures():
    pass
