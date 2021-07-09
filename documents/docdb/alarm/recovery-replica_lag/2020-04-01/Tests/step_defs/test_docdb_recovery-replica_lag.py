# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/docdb_recovery-replica_lag.feature',
          'To detect high values of DBInstanceReplicaLag - green')
def test_alarm_green():
    pass


@scenario('../features/docdb_recovery-replica_lag.feature',
          'To detect high values of DBInstanceReplicaLag - red')
def test_alarm_red():
    pass
