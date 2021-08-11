# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_application_client_tls_negotiation_error_count.feature',
          'Create elb:alarm:application_client_tls_negotiation_error_count:2020-04-01 based on '
          'ClientTLSNegotiationErrorCount metric normal case')
def test_application_elb_client_tls_negotiation_error_count_alarm():
    pass


@scenario('../features/elb_application_client_tls_negotiation_error_count.feature',
          'Create elb:alarm:application_client_tls_negotiation_error_count:2020-04-01 based on '
          'ClientTLSNegotiationErrorCount metric state.ALARM case')
def test_application_elb_client_tls_negotiation_error_count_red_alarm():
    pass
