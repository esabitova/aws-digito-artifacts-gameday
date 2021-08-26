
from pytest_bdd import scenario


@scenario('../features/data_analytics_restore_app_from_snapshot_existent.feature',
          'Execute Digito-RestoreKinesisDataAnalyticsApplicationFromSnapshotSOP_2021-07-28 '
          'to restore kinesis data analytics flink application from existent snapshot')
def test_data_analytics_restore_app_from_snapshot_existent():
    """
    Execute Digito-RestoreKinesisDataAnalyticsApplicationFromSnapshotSOP_2021-07-28
    Use existent snapshot
    """
