# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_network_client_tls_negotiation_error_count.feature',
          'Create elb:alarm:network_client_tls_negotiation_error_count:2020-04-01 based on '
          'ClientTLSNegotiationErrorCount metric and check OK status')
def test_network_client_tls_negotiation_error_count_green_alarm():
    pass

# ALARM case:
# unfortunately we couldn't reproduce alarm in state ALARM case
# because for network load balancer datapoins were not been triggered
# in a stable way. We've used the same approach as for ApplicationLoadBalancer
# but no luck
