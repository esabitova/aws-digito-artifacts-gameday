# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/ec2_procstate.feature',
          'Lease EC2 from resource manager and test attach an alarm from Document')
def test_ec2_procstate():
    """Lease EC2 from resource manager and test attach an alarm from Document"""
    pass
