# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_freeable_memory.feature',
          'Test DocDb freeable memory:alarm:health-freeable_memory:2020-04-01')
def test_docdb_freeable_memory():
    """Test DocDb freeable memory:alarm:health-freeable_memory:2020-04-01"""
    pass
