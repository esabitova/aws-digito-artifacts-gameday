# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/ebs_write_throughput.feature',
          'Lease EBS from resource manager and test attach an alarm from Document')
def test_ebs_write_throughput():
    """Lease EBS from resource manager and test attach an alarm from Document"""
    pass
