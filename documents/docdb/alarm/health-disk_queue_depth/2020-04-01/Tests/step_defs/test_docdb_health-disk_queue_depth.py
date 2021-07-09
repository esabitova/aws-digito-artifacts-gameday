# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/docdb_health-disk_queue_depth.feature',
          'To detect high values of DiskQueueDepth - green')
def test_alarm_green():
    pass


@scenario('../features/docdb_health-disk_queue_depth.feature',
          'To detect high values of DiskQueueDepth - red')
def test_alarm_red():
    pass
