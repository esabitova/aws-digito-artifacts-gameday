# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_key_authorization_failures.feature',
          'Create elasticache:alarm:key_authorization_failures:2020-04-01 based on '
          'KeyAuthorizationFailures metric and check OK status')
def test_health_key_authorization_failures():
    pass
