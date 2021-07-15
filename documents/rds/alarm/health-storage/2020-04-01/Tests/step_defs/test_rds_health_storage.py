# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/rds_health_storage.feature',
          'Lease RDS from resource manager and test attach an alarm from Document')
def test_rds_health_storage():
    """Lease RDS from resource manager and test attach an alarm from Document"""
    pass
