# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_network_client_tls_negotiation_error_count.feature',
          'Create elb:alarm:network_client_tls_negotiation_error_count:2020-04-01 based on '
          'ClientTLSNegotiationErrorCount metric normal case')
def test_network_client_tls_negotiation_error_count_green_alarm():
    pass
