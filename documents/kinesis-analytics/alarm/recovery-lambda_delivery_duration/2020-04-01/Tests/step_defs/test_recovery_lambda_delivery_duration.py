# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/recovery_lambda_delivery_duration.feature',
          'Create kinesis:alarm:data_analytics_lambda_delivery_duration:2020-04-01 based on '
          'LambdaDelivery.DeliveryFailedRecords metric and check OK status')
def test_kin_an_sql_lambda_delivery_duration():
    """
    Test Kinesis Data Analytics for SQL Applications
    kinesis:alarm:data_analytics_lambda_delivery_duration:2020-04-01
    """
    pass
