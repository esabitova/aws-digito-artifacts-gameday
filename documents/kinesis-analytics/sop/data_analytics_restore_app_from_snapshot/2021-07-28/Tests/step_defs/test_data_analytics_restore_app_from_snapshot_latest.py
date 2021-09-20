
from pytest_bdd import scenario


@scenario('../features/data_analytics_restore_app_from_snapshot_latest.feature',
          'Execute Digito-RestoreKinesisDataAnalyticsApplicationFromSnapshotSOP_2021-07-28 '
          'to restore kinesis data analytics flink application from latest snapshot')
def test_data_analytics_restore_app_from_snapshot_latest():
    """
    Execute Digito-RestoreKinesisDataAnalyticsApplicationFromSnapshotSOP_2021-07-28.
    Use latest snapshot or fail, if latest snapshot does not exist
    """
