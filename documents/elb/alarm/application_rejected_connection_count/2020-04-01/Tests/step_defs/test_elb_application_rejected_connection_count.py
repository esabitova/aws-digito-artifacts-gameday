# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_application_rejected_connection_count.feature',
          'Create elb:alarm:application_rejected_connection_count:2020-04-01 based on RejectedConnectionCount metric '
          'and test green state')
def test_elb_application_rejected_connection_count_green():
    pass
