# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_lambda_delivery_delivery_failed_records.feature',
          'Test kinesis:alarm:data_analytics_lambda_delivery_delivery_failed_records:2020-04-01 based on '
          'LambdaDelivery.DeliveryFailedRecords metric and check OK status')
def test_kin_an_lambda_delivery_delivery_failed_records():
    """
    Test Kinesis Data Analytics for SQL Applications
    kinesis:alarm:data_analytics_lambda_delivery_delivery_failed_records:2020-04-01
    """
    pass
