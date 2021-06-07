# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/ebs_burst_balance.feature',
          'Lease EBS from resource manager and test attach an alarm from Document')
def test_ebs_burst_balance_alarm():
    """Lease EBS from resource manager and test attach an alarm from Document"""
    pass
