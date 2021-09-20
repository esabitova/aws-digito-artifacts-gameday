# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_processing_dropped_records.feature',
          'Create kinesis:alarm:data_analytics_inputprocessing_droppedrecords:2020-04-01 based on '
          'InputProcessing.DroppedRecords metric and check OK status')
def test_kin_an_processing_dropped_records():
    """
    Test Kinesis Data Analytics for SQL Applications
    kinesis:alarm:data_analytics_inputprocessing_droppedrecords:2020-04-01
    """
    pass
