# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_4xx_error.feature',
          'Test API Gateway api-gw:alarm:4xx-error:2020-04-01')
def test_apigw_4xx_errors():
    """Test API Gateway api-gw:alarm:4xx-error:2020-04-01"""
    pass
