# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/load-balancer_network_client_tls_negotiation_error_count.feature',
          'Alarm is not triggered when network client tls negotiation error count is less than a threshold')
def test_network_client_tls_negotiation_error_count_green_alarm():
    pass
