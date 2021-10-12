# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/load_balancer_application_lambda_user_error.feature',
          'Create load-balancer:alarm:application_lambda_user_error:2020-04-01 based on LambdaUserError metric '
          'and check OK status')
def test_load_balancer_application_lambda_user_error_alarm():
    pass


@scenario('../features/load_balancer_application_lambda_user_error.feature',
          'Create load-balancer:alarm:application_lambda_user_error:2020-04-01 based on LambdaUserError metric '
          'and check ALARM status')
def test_load_balancer_application_lambda_user_error_trigger_alarm():
    pass
