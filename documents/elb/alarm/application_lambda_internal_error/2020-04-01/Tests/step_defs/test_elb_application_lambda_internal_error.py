# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_application_lambda_internal_error.feature',
          'Create elb:alarm:application_lambda_internal_error:2020-04-01 based on LambdaInternalError metric '
          'and test green state')
def test_elb_application_lambda_internal_error_alarm():
    pass
