# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_application_lambda_user_error.feature',
          'Create elb:alarm:application_lambda_user_error:2020-04-01 based on LambdaUserError metric '
          'and check OK status')
def test_elb_application_lambda_user_error_alarm():
    pass


@scenario('../features/elb_application_lambda_user_error.feature',
          'Create elb:alarm:application_lambda_user_error:2020-04-01 based on LambdaUserError metric '
          'and check ALARM status')
def test_elb_application_lambda_user_error_trigger_alarm():
    pass
