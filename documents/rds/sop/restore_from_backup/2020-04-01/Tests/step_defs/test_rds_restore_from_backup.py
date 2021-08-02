# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/restore_from_backup.feature', 'Create AWS resources using CloudFormation template '
          'and execute SSM automation document to restore from backup')
def test_restore_from_backup():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
