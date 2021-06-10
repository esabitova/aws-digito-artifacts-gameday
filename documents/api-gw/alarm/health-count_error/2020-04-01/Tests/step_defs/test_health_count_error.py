# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_count_error.feature',
          'Test API Gateway api-gw:alarm:count-error:2020-04-01')
def test_apigw_count_errors():
    """Test API Gateway api-gw:alarm:count-error:2020-04-01"""
    pass
