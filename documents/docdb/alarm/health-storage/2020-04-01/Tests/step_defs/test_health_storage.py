# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_storage.feature',
          'Test DocDb FreeLocalStorage memory:alarm:health-storage:2020-04-01')
def test_health_storage():
    """Test DocDb FreeLocalStorage memory:alarm:health-storage:2020-04-01"""
    pass
