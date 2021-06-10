# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_5xx_error.feature',
          'Test API Gateway api-gw:alarm:5xx-error:2020-04-01')
def test_apigw_5xx_errors():
    """Test API Gateway api-gw:alarm:5xx-error:2020-04-01"""
    pass
