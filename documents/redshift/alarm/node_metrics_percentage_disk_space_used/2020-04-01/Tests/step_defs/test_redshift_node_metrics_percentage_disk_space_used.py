# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/redshift_node_metrics_percentage_disk_space_used.feature',
          'Create redshift:alarm:node_metrics_percentage_disk_space_used:2020-04-01 '
          'based on PercentageDiskSpaceUsed metric and check OK status.')
def test_node_metrics_percentage_disk_space_used():
    pass
