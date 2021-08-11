# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/synthetic_canary.feature',
          'Lease ASG from resource manager and test attach an alarm from Document')
def test_synthetic_canary_alarm():
    """Lease ASG from resource manager and test attach an alarm from Document"""
    pass
