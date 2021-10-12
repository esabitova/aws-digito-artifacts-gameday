# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/load_balancer_application_rejected_connection_count.feature',
          'Create load-balancer:alarm:application_rejected_connection_count:2020-04-01 based on '
          'RejectedConnectionCount metric and check OK status')
def test_load_balancer_application_rejected_connection_count_green():
    pass
