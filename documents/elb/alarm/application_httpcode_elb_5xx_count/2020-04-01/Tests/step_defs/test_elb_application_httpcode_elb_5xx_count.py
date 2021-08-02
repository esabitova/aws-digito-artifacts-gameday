# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_application_httpcode_elb_5xx_count.feature',
          'Alarm is not triggered when count of http 5xx responses received by load balancer is less '
          'than a threshold - green')
def test_elb_application_httpcode_elb_5xx_count_alarm():
    pass


# @scenario('../features/elb_application_httpcode_elb_5xx_count.feature',
#           'Reports when count of http 5xx responses received by load balancer is greater than or equal to'
#           ' a threshold - red')
# def test_elb_application_httpcode_elb_5xx_count_threshold_exceeded_alarm():
#     pass
