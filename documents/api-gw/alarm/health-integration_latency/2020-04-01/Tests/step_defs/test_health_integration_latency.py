# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_integration_latency.feature',
          'Test API Gateway api-gw:alarm:integration-latency:2020-04-01')
def test_apigw_integration_latency():
    """Test API Gateway api-gw:alarm:integration-latency:2020-04-01"""
    pass
