# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/asg_cpu_util.feature',
          'Lease ASG from resource manager and test attach an alarm from Document')
def test_asg_cpu_util_alarm():
    """Lease ASG from resource manager and test attach an alarm from Document"""
    pass
