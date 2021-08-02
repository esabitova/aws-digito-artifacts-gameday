# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_network_unhealthy_host_count.feature',
          'Alarm is not triggered when count of elb unhealthy hosts less than a threshold - green')
def test_elb_network_unhealthy_host_count_green():
    pass


@scenario('../features/elb_network_unhealthy_host_count.feature',
          'Reports when count of network load balancer unhealthy hosts greater than or equal to a threshold')
def test_elb_network_unhealthy_host_count_exceeds_threshold():
    pass
