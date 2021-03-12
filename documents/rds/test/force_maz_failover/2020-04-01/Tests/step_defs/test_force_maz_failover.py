# coding=utf-8
"""SSM automation document for RDS instance failover."""
from pytest_bdd import (
    scenario
)

@scenario('../../Tests/features/force_maz_failover.feature', 'Create AWS resources using CloudFormation template '
                                                                  'and execute SSM automation document to failover '
                                                                  'RDS instance')
def test_force_maz_failover():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""