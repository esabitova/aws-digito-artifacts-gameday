# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_read_latency.feature',
          'Test DocDb  time taken per disk I/O operation:alarm:health-read_latency:2020-04-01')
def test_health_read_latency():
    """Test DocDb  time taken per disk I/O operation:alarm:health-read_latency:2020-04-01"""
    pass
