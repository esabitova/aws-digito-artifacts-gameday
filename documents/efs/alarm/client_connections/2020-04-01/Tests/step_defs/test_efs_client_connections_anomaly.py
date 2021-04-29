# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/efs_client_connections_anomaly.feature',
          'Lease EFS from resource manager and test attach an alarm from Document')
def test_asg_mem_util_alarm():
    """Lease EFS from resource manager and test attach an alarm from Document"""
    pass
