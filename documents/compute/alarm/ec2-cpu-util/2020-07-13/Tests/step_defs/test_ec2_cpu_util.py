# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/ec2_cpu_util.feature',
          'Lease EC2 from resource manager and test attach an alarm from Document')
def test_ec2_cpu_util():
    """Lease EC2 from resource manager and test attach an alarm from Document"""
    pass
