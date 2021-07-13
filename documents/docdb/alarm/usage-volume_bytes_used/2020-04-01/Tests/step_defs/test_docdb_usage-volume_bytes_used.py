# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/docdb_usage-volume_bytes_used.feature',
          'To detect high values of VolumeBytesUsed - green')
def test_docdb_usage_volume_bytes_used_alarm_green():
    pass


@scenario('../features/docdb_usage-volume_bytes_used.feature',
          'To detect high values of VolumeBytesUsed - red')
def test_docdb_usage_volume_bytes_used_alarm_red():
    pass
