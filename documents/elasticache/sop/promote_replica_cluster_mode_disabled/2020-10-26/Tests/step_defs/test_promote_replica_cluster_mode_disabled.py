# coding=utf-8

from pytest_bdd import scenario


@scenario('../features/promote_replica_cluster_mode_disabled_usual_case.feature',
          'Execute SSM automation document Digito-PromoteReplicaClusterModeDisabled_2020-10-26')
def test_promote_replica_cluster_mode_disabled_usual_case():
    """Execute SSM automation document Digito-PromoteReplicaClusterModeDisabled_2020-10-26"""
