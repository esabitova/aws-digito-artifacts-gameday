# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/create_backup.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to '
          'create backup of EFS')
def test_restore_backup():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
