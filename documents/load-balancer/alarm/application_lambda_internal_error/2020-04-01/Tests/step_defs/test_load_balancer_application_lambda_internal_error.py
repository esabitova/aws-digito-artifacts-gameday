# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/load_balancer_application_lambda_internal_error.feature',
          'Create load-balancer:alarm:application_lambda_internal_error:2020-04-01 based on LambdaInternalError metric '
          'and check OK status')
def test_load_balancer_application_lambda_internal_error_alarm():
    pass
