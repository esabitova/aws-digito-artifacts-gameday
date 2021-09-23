# coding=utf-8
import pytest
from pytest_bdd import (
    scenario
)


@pytest.mark.skip(reason="Broken test: https://issues.amazon.com/issues/Digito-3222")
@scenario('../features/asg_many_unhealthy_hosts.feature',
          'Lease ASG from resource manager and test attach an alarm from Document')
def test_asg_cpu_util_alarm():
    """Lease ASG from resource manager and test attach an alarm from Document"""
    pass
