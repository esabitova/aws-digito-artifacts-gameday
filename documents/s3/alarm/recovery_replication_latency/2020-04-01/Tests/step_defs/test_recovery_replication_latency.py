# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/recovery_replication_latency.feature',
          'Create the alarm based on the RecoveryReplicationLatency metric')
def test_recovery_replication_latency():
    pass
