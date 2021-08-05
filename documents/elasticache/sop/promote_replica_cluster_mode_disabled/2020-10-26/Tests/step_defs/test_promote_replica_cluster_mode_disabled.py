# coding=utf-8

from pytest_bdd import scenario


@scenario('../features/promote_replica_cluster_mode_disabled_usual_case.feature',
          'Execute SSM automation document Digito-PromoteReplicaClusterModeDisabled_2020-10-26 '
          'with AutomaticFailover and MultiAZ enabled in a multi AZ deployment')
def test_promote_replica_cluster_mode_disabled_usual_case_with_automatic_failover_enabled_multi_az():
    """Execute SSM automation document Digito-PromoteReplicaClusterModeDisabled_2020-10-26"""


@scenario('../features/promote_replica_cluster_mode_disabled_usual_case.feature',
          'Execute SSM automation document Digito-PromoteReplicaClusterModeDisabled_2020-10-26 '
          'with AutomaticFailover enabled in a single AZ deployment')
def test_promote_replica_cluster_mode_disabled_usual_case_with_automatic_failover_enabled_single_az():
    """Execute SSM automation document Digito-PromoteReplicaClusterModeDisabled_2020-10-26"""


@scenario('../features/promote_replica_cluster_mode_disabled_usual_case.feature',
          'Execute SSM automation document Digito-PromoteReplicaClusterModeDisabled_2020-10-26 '
          'with AutomaticFailover disabled in a single AZ deployment')
def test_promote_replica_cluster_mode_disabled_usual_case_with_automatic_failover_disabled():
    """Execute SSM automation document Digito-PromoteReplicaClusterModeDisabled_2020-10-26"""
