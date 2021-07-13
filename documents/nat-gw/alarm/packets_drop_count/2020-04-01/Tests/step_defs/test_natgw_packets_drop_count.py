# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/natgw_packets_drop_count.feature',
          'Check alarm for number of packets dropped by the NAT gateway')
def test_natgw_packets_drop_count_alarm_green():
    pass
