# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/asg_req_count.feature',
          'Lease ASG from resource manager and test attach an alarm from Document')
def test_asg_req_count():
    """Lease ASG from resource manager and test attach an alarm from Document"""
    pass
