# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/ec2_used_disk.feature',
          'Lease EC2 from resource manager and test attach an alarm from Document')
def test_ec2_used_disk_alarm():
    """Lease EC2 from resource manager and test attach an alarm from Document"""
    pass
