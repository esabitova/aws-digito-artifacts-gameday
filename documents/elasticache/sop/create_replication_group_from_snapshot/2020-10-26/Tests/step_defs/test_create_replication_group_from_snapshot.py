from pytest_bdd import scenario


@scenario('../features/create_replication_group_from_snapshot_usual_case.feature',
          'Execute SSM automation document Digito-CreateElasticacheReplicationGroupFromSnapshotSOP_2020-10-26 '
          'when source cluster available and cluster mode disabled')
def test_case_when_source_cluster_available_and_cluster_mode_disabled():
    """Execute SSM automation document Digito-CreateElasticacheReplicationGroupFromSnapshotSOP_2020-10-26"""


@scenario('../features/create_replication_group_from_snapshot_usual_case.feature',
          'Execute SSM automation document Digito-CreateElasticacheReplicationGroupFromSnapshotSOP_2020-10-26 '
          'when source cluster available and cluster mode enabled')
def test_case_when_source_cluster_available_and_cluster_mode_enabled():
    """Execute SSM automation document Digito-CreateElasticacheReplicationGroupFromSnapshotSOP_2020-10-26"""
