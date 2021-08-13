# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_application_target_tls_negotiation_error_count.feature',
          'Create elb:alarm:application_target_tls_negotiation_error_count:2020-04-01 based on'
          ' TargetTLSNegotiationErrorCount metric and check OK status')
def test_elb_application_target_tls_negotiation_error_count_green():
    pass


# @scenario('../features/elb_application_target_tls_negotiation_error_count.feature',
#           'Create elb:alarm:application_target_tls_negotiation_error_count:2020-04-01 based on '
#           'TargetTLSNegotiationErrorCount metric and check ALARM status')
# def test_elb_application_target_tls_negotiation_error_count_red():
#     pass
