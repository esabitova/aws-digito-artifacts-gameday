# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_total_request_latency.feature',
          'Create the alarm based on the TotalRequestLatency metric')
def test_health_total_request_latency():
    pass
