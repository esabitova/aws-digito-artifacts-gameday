# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/load_balancer_network_unhealthy_host_count.feature',
          'Create load-balancer:alarm:network_unhealthy_host_count:2020-04-01 based on UnHealthyHostCount metric '
          'and check OK status')
def test_load_balancer_network_unhealthy_host_count_green():
    pass


@scenario('../features/load_balancer_network_unhealthy_host_count.feature',
          'Create load-balancer:alarm:network_unhealthy_host_count:2020-04-01 based on UnHealthyHostCount metric '
          'and check ALARM status')
def test_load_balancer_network_unhealthy_host_count_exceeds_threshold():
    pass
