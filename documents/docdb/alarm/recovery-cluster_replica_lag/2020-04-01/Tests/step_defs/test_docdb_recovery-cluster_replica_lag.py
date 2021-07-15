# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/docdb_recovery-cluster_replica_lag.feature',
          'To detect high values of DBClusterReplicaLagMaximum - green')
def test_docdb_recovery_cluster_replica_lag_alarm_green():
    pass


@scenario('../features/docdb_recovery-cluster_replica_lag.feature',
          'To detect high values of DBClusterReplicaLagMaximum - red')
def test_docdb_recovery_cluster_replica_lag_alarm_red():
    pass
