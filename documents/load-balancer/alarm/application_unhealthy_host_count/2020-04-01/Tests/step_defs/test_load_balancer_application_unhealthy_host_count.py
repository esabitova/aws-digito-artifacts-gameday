# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/load_balancer_application_unhealthy_host_count.feature',
          'Create load-balancer:alarm:application_unhealthy_host_count:2020-04-01 based on UnHealthyHostCount metric '
          'and check OK status')
def test_elb_application_unhealthy_host_count_alarm_green():
    pass


@scenario('../features/load_balancer_application_unhealthy_host_count.feature',
          'Create load-balancer:alarm:application_unhealthy_host_count:2020-04-01 based on UnHealthyHostCount metric '
          'and check ALARM status')
def test_elb_application_unhealthy_host_count_exceeded_threshold_alarm():
    pass
