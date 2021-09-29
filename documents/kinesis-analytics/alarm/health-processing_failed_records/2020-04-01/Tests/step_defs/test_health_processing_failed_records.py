# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_processing_failed_records.feature',
          'Create kinesis:alarm:data_analytics_inputprocessing_processingfailedrecords:2020-04-01 based on '
          'InputProcessing.ProcessingFailedRecords metric and check OK status')
def test_kin_an_processing_failed_records():
    """
    Test Kinesis Data Analytics for SQL Applications
    kinesis:alarm:data_analytics_inputprocessing_processingfailedrecords:2020-04-01
    """
    pass
