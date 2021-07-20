# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_latency.feature',
          'Test API Gateway api-gw:alarm:health-latency:2020-04-01')
def test_apigw_latency():
    """Test API Gateway api-gw:alarm:health-latency:2020-04-01"""
    pass
