# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/load_balancer_network_client_tls_negotiation_error_count.feature',
          'Create load-balancer:alarm:network_client_tls_negotiation_error_count:2020-04-01 based on '
          'ClientTLSNegotiationErrorCount metric and check OK status')
def test_network_client_tls_negotiation_error_count_green_alarm():
    pass


@scenario('../features/load_balancer_network_client_tls_negotiation_error_count.feature',
          'Create load-balancer:alarm:network_client_tls_negotiation_error_count:2020-04-01 based on '
          'ClientTLSNegotiationErrorCount metric and check ALARM status')
def test_network_client_tls_negotiation_error_count_red_alarm():
    pass
