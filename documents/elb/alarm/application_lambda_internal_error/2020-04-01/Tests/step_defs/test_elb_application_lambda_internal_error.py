# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_application_lambda_internal_error.feature',
          'Alarm is not triggered when count of lambda internal errors from lambda targets is less than a threshold')
def test_elb_application_lambda_internal_error_alarm():
    pass
