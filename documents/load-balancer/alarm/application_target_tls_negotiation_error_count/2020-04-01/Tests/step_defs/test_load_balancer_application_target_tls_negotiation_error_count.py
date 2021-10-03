# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/load_balancer_application_target_tls_negotiation_error_count.feature',
          'Create load-balancer:alarm:application_target_tls_negotiation_error_count:2020-04-01 based on'
          ' TargetTLSNegotiationErrorCount metric and check OK status')
def test_load_balancer_application_target_tls_negotiation_error_count_green():
    pass


@scenario('../features/load_balancer_application_target_tls_negotiation_error_count.feature',
          'Create load-balancer:alarm:application_target_tls_negotiation_error_count:2020-04-01 based on '
          'TargetTLSNegotiationErrorCount metric and check ALARM status')
def test_load_balancer_application_target_tls_negotiation_error_count_red():
    pass
