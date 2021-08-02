# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_application_lambda_user_error.feature',
          'Alarm is not triggered when count of lambda user errors from lambda targets is less than a threshold')
def test_elb_application_lambda_user_error_alarm():
    pass


@scenario('../features/elb_application_lambda_user_error.feature',
          'Report when count of lambda user errors from lambda targets is greater than or equal to a threshold - red')
def test_elb_application_lambda_user_error_trigger_alarm():
    pass
