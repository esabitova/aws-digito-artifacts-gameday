# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/efs_percent_io_limit.feature',
          'Lease EFS from resource manager and test attach an alarm from Document')
def test_efs_percent_io_limit_alarm():
    """Lease EFS from resource manager and test attach an alarm from Document"""
    pass
