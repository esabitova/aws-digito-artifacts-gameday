# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/replication_lag.feature',
          'Test Elasticache Redis ReplicationLag Alarm elasticache:alarm:replication_lag:2020-04-01')
def test_replication_lag():
    pass
