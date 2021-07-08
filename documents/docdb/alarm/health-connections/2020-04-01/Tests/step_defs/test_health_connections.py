# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_connections.feature',
          'Test DocDb open connections:alarm:health-connections:2020-04-01')
def test_health_connections():
    """Test DocDb open connections:alarm:health-connections:2020-04-01"""
    pass
