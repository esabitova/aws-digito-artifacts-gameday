# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/docdb_health-disk_queue_depth.feature',
          'To detect high values of DiskQueueDepth - green')
def test_docdb_health_disk_queue_depth_alarm_green():
    pass


@scenario('../features/docdb_health-disk_queue_depth.feature',
          'To detect high values of DiskQueueDepth - red')
def test_docdb_health_disk_queue_depth_alarm_red():
    pass
