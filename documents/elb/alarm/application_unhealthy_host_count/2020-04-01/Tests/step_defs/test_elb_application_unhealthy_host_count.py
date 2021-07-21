# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_application_unhealthy_host_count.feature',
          'Alarm is not triggered when count of application load balancer unhealthy hosts '
          'less than a threshold - green')
def test_elb_application_unhealthy_host_count_alarm_green():
    pass


@scenario('../features/elb_application_unhealthy_host_count.feature',
          'Report when count of application load balancer unhealthy hosts greater than or equal to a threshold - red')
def test_elb_application_unhealthy_host_count_exceeded_threshold_alarm():
    pass
