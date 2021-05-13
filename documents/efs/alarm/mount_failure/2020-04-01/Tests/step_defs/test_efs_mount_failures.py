# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/efs_mount_failures.feature',
          'Lease EFS from resource manager and test attach an alarm from Document')
def test_efs_mount_failures_alarm():
    """Lease EFS from resource manager and test attach an alarm from Document"""
    pass
