# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/docdb_usage-high_volume_write_iops.feature',
          'To detect anomalies of high values of VolumeWriteIOPs')
def test_alarm():
    pass
