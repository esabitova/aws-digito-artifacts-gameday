# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/load_balancer_gateway_unhealthy_host_count.feature',
          'Alarm is not triggered when count of load-balancer unhealthy hosts less than a threshold - green')
def test_elb_gateway_unhealthy_host_count_green():
    pass
