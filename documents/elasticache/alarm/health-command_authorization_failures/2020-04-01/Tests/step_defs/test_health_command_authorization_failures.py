# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_command_authorization_failures.feature',
          'Create elasticache:alarm:health-command_authorization_failures:2020-04-01 '
          'based on CommandAuthorizationFailures metric and check OK status')
def test_elasticache_redis_command_authorization_failures():
    pass
