# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_application_rejected_connection_count.feature',
          'Alarm is not triggered when application load balancer rejected connections count is less than a threshold')
def test_elb_application_rejected_connection_count_green():
    pass
