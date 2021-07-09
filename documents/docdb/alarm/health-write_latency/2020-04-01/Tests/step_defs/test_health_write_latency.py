# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_write_latency.feature',
          'Test DocDb  time taken per disk I/O operation:alarm:health-write_latency:2020-04-01')
def test_health_write_latency():
    """Test DocDb  time taken per disk I/O operation:alarm:health-write_latency:2020-04-01"""
    pass
