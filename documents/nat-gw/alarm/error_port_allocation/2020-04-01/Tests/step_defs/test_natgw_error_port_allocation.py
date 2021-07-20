# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/natgw_error_port_allocation.feature',
          'Check alarm for number of times the NAT gateway could not allocate a source port')
def test_natgw_error_port_allocation_alarm_green():
    pass
