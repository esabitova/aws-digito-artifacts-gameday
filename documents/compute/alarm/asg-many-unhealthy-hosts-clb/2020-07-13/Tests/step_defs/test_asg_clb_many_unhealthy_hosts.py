# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/asg_clb_many_unhealthy_hosts.feature',
          'Lease ASG from resource manager and test attach an alarm from Document')
def test_asg_clb_many_unhealthy_hosts_alarm():
    """Lease ASG from resource manager and test attach an alarm from Document"""
    pass
