# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/ec2_cloudwatch_mem_util.feature',
          'Lease EC2 from resource manager and test attach an alarm from Document')
def test_asg_mem_util_alarm():
    """Lease ASG from resource manager and test attach an alarm from Document"""
    pass
