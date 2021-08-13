# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_application_httpcode_elb_5xx_count.feature',
          'Create elb:alarm:application_httpcode_elb_5xx_count:2020-04-01 based on HTTPCode_ELB_5XX_Count '
          'metric and check OK status')
def test_elb_application_httpcode_elb_5xx_count_alarm():
    pass


@scenario('../features/elb_application_httpcode_elb_5xx_count.feature',
          'Create elb:alarm:application_httpcode_elb_5xx_count:2020-04-01 based on HTTPCode_ELB_5XX_Count '
          'metric and check ALARM status')
def test_elb_application_httpcode_elb_5xx_count_threshold_exceeded_alarm():
    pass
