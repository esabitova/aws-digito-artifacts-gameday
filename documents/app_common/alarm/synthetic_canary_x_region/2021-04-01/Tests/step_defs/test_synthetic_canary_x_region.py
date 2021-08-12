# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/synthetic_canary_x_region.feature',
          'Lease ASG from resource manager and test attach an alarm from Document')
def test_synthetic_canary_alarm_cross_region():
    """Lease ASG from resource manager and test attach an alarm from Document"""
    pass
